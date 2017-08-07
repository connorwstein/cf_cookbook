"""Backend for cashflowcookbook.ca
"""
import time
import os
import re
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from O365.inbox import Inbox
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from sqlalchemy import create_engine
from flask_bootstrap import Bootstrap
from flask_basicauth import BasicAuth
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from bs4 import BeautifulSoup

from keys import user, pwd, db_location, log_location, app, email_user, email_pass
from send_email import send_mail


app = Flask(__name__)
Bootstrap(app)
BasicAuth(app)

app.config['SECRET_KEY'] = app
app.config['SQLALCHEMY_DATABASE_URI'] = db_location
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['BASIC_AUTH_USERNAME'] = user
app.config['BASIC_AUTH_PASSWORD'] = pwd
app.config['BASIC_AUTH_FORCE'] = True
app.config['UPLOAD_FOLDER'] = '/home/ubuntu/cf_cookbook/static'

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

basic_auth = BasicAuth(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
from models import Recipe, Subscriber, Comment

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_new_recipe(title, text, path):
    date = time.strftime("%d/%m/%Y %H:%M:%S")
    new_recipe = Recipe(title, text, date, path)
    app.logger.info("New article upload %s", new_recipe)
    db.session.add(new_recipe)
    db.session.commit()

def delete_recipe(title):
    to_delete = Recipe.query.filter_by(title=title).first()
    if to_delete:
        # Also clean up the image, guaranteed to be unique
        subprocess.call("rm -f {}".format(to_delete.img_path), shell=True)
        db.session.delete(to_delete)
        db.session.commit()

def delete_comment(comment_text):
    to_delete = Comment.query.filter_by(body=comment_text).first()
    if to_delete:
        db.session.delete(to_delete)
        db.session.commit()

def basic_valid_email_check(email):
    return re.match(r'[^@]+@[^@]+\.[^@]+', email)

@app.route('/update_comments')
def update_comments():
    """Use a cronjob to periodically curl this URL"""
    i = Inbox((email_user, email_pass), getNow=True)
    try:
        i.getMessages()
    except KeyError: 
        app.logger.info("No new comments")
    else:
        for message in i.messages:
            # Inbox filter doesn't seem to be working, filter manually
            if message.getSubject() == 'Re: New comment from reader!':
                app.logger.info("Found an approved comment")
                soup = BeautifulSoup(message.getBody(), 'html.parser')
                # Extract the message from the email body
                # Example: <div class="PlainText">Reader Connor would like to comment the 
                # following on recipe Cross Border Couch Potato: test</div>
                message = soup.findAll("div", { "class" : "PlainText" })[0].contents[0]
                app.logger.info("Message {}".format(message))
                reader = re.search(r'Reader (.*) would', message).groups()[0]
                comment = re.search(r': (.*)$', message).groups()[0]
                recipe = re.search(r'recipe (.*):', message).groups()[0]
                app.logger.info("Reader {}, Comment {}, Recipe {}".format(reader, comment, recipe))
                recipe_id = Recipe.query.filter_by(title=recipe).first().id
                check_comment_already_added  = Comment.query.filter_by(user=reader, body=comment, recipe_id=recipe_id).first()
                if not check_comment_already_added:
                    new_comment = Comment(reader, comment, datetime.now(), recipe_id)
                    db.session.add(new_comment)
                    db.session.commit()
                
    return ('', 204)

@app.route('/')
def home():
    app.logger.info("Home page requested")
    recipes_sorted = sorted([(r, os.path.basename(r.img_path), i) for i, r in enumerate(Recipe.query.all())], key=lambda r: r[0].date)
    num_recent = 3 
    app.logger.info("{}".format(recipes_sorted))
    return render_template('index.html', new_recipes=recipes_sorted[:num_recent+1])

@app.route('/recipes')
def recipes():
    app.logger.info("Recipes requested")
    all_recipes_and_imgs = [(r, os.path.basename(r.img_path)) for r in Recipe.query.all()]
    app.logger.info("%s", str(all_recipes_and_imgs))
    return render_template('recipes.html', recipes=all_recipes_and_imgs)

@app.route('/utensils')
def utensils():
    app.logger.info("Utensils requested")
    all_utensils = {'Debt': {'xlsx': 'CFCB_debt_sheet.xlsx', 'img': 'CFCB_debt_sheet_img.png',
                             'text': 'Having debts lurking about in credit cards, student loans, mortgages, car loans and various other things is no fun. They slurp away at your bank account like a colony of vampire bats leaving you dry 3 days before each pay check. Before we whack them with a rolling pin, we need to get them all up where we can see them. Download the handy Cashflow Cookbook Debt Sheet, enter in your debts (yes all of them) and start to grind them down one a time, starting with the highest interest rate one. Use the savings from the Recipe section and Cashflow Cookbook to free up cash to eliminate these debts.'},
                    'Net Worth':  {'xlsx': 'CFCB_net_worth.xlsx', 'img': 'CFCB_net_worth_img.png',
                             'text': 'Keeping a monthly budget is painful. Like a case of food poisoning from post-peak Thanksgiving leftovers. Easier to find new ways to save and apply them to debt reduction and increased savings. So how do you track all of this to see if it is working? By downloading the Cashflow Cookbook Net Worth Sheet. Fill in everything you owe and everything you own. Update it every few months and see how you are doing. Takes an hour or 2 a year and it will change the way you look at spending and saving.'}}
    return render_template('utensils.html', utensils=all_utensils)

@app.route("/get_excel/<filename>")
def get_excel(filename):
    """This method was the only one that worked on both Safari and Chrome
    (note that Safari does not support the download html tag)
    """
    excelDownload = open("/var/www/cf_cookbook/static/%s" % filename,'rb').read()
    return Response(
        excelDownload,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition":
                 "attachment; filename=%s" % filename})

@app.route('/about')
def about():
    app.logger.info("About page requested")
    return render_template('about.html')

@app.route('/ingredients')
def ingredients():
    app.logger.info("Ingredient page requested")
    return render_template('ingredients.html')

@app.route('/full_recipe/<recipe_id>', methods=['GET', 'POST'])
def full_recipe(recipe_id):
    if request.method == 'POST':
        app.logger.info("Received a comment {} --> {}".format(request.form['commentor_name'], request.form['comment']))
        # TODO: Email this comment to be approved
        # Need a script running in the background which checks email periodically for "New comment" with reply OK, then populate
        # the DB accordingly
        send_mail(email_user, email_user,
                  "New comment from reader!", 
                  ("Reader {} would like to comment the following on "
                   "recipe {}: {}").format(request.form['commentor_name'], Recipe.query.filter_by(id=recipe_id).first().title,
                  request.form['comment']),
                  username=email_user, password=email_pass)
    recipe = Recipe.query.filter_by(id=recipe_id).first()
    comments = Comment.query.filter_by(recipe_id=recipe_id)
    app.logger.info("{}".format(comments))
    return render_template('recipe.html', recipe=recipe, comments=comments)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        app.logger.info(request)
        app.logger.info(request.files)
        if request.form['title'] and request.form['text'] and 'recipe_img' in request.files:
            if request.form['title'] not in [r.title for r in Recipe.query.all()] and \
                request.files['recipe_img'] not in [r.img_path for r in Recipe.query.all()]:
                f = request.files['recipe_img']
                if f and allowed_file(f.filename):
                    filename = secure_filename(f.filename)
                    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    f.save(path)
                    flash("Success creating article {}".format(request.form['title']))

                    add_new_recipe(request.form['title'], request.form['text'], path)
                else:
                    flash("Invalid file extension, must be in {}".format(ALLOWED_EXTENSIONS))
                    app.logger.info("File not allowed to be uploaded")
            else:
                flash("{} or {} have already been used, please choose a unique recipe title and image name".format(request.form['title'], request.files['recipe_img']))
                app.logger.info("Image file name or title already used")
        elif request.form['title_to_delete']:
            flash("Successfully deleted article {}".format(request.form['title_to_delete']))
            delete_recipe(request.form['title_to_delete'])
        elif request.form['comment_to_delete']:
            flash("Successfully deleted comment")
            delete_comment(request.form['comment_to_delete'])
        else:
            flash("Image file is required!")
            app.logger.info("May be missing image file")
    return render_template('edit.html')


@app.route('/email', methods=['GET', 'POST'])
def email():
    if request.method == 'POST':
        app.logger.info(request)
        app.logger.info(request.form['subject'])
        app.logger.info(request.form['text'])
        for sub in Subscriber.query.all():
            app.logger.info("Sub %s")
        app.logger.info("Sending to {}", [sub.email for sub in Subscriber.query.all()])
        try:
            send_mail(email_user, [sub.email for sub in Subscriber.query.all()],
                      request.form['subject'] , request.form['text'],
                      username=email_user, password=email_pass)
        except Exception as e:
            app.logger.info("Unable to send to some recipients {} --> {}".format(type(e), e))
    return render_template('email.html')

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    if request.method == 'POST':
        app.logger.info(request)
        app.logger.info(request.form['email'])
        if request.form['email'] not in [sub.email for sub in Subscriber.query.all()]:
            if basic_valid_email_check(request.form['email']):
                new_sub = Subscriber(request.form['email'])
                app.logger.info("New subscriber %s", new_sub)
                db.session.add(new_sub)
                db.session.commit()
                flash("{} is now subscribed!".format(request.form['email']))
            else:
                flash("{} is not a valid email!".format(request.form['email']))
        else:
            flash("{} is already subscribed!".format(request.form['email']))
    return render_template('subscribe.html')

@app.errorhandler(404)
def page_not_found(e):
    app.logger.error("Page not found {}".format(e))
    return render_template('404.html'), 404

def setup_logging():
    app.logger.setLevel(logging.DEBUG) # Without this you will see no logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # TODO: fix log rotate permission bug
    handler = RotatingFileHandler(log_location, maxBytes=1000000, backupCount=1)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

def init():
    setup_logging()
    if app.testing is True:
        db.create_all()

if __name__ == "__main__":
    init()
    app.run(debug=True, host="0.0.0.0")
