"""Backend for cashflowcookbook.ca
"""
import logging
import time
import os
from logging.handlers import RotatingFileHandler

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_bootstrap import Bootstrap
from flask_basicauth import BasicAuth
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from keys import user, pwd, db_location, log_location, app



app = Flask(__name__)
Bootstrap(app)
BasicAuth(app)

app.config['SECRET_KEY'] = app
app.config['SQLALCHEMY_DATABASE_URI'] = db_location
app.config['BASIC_AUTH_USERNAME'] = user
app.config['BASIC_AUTH_PASSWORD'] = pwd
app.config['BASIC_AUTH_FORCE'] = True
app.config['UPLOAD_FOLDER'] = '/home/ubuntu/cf_cookbook/static'

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

basic_auth = BasicAuth(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Recipe(db.Model): # pylint: disable=too-few-public-methods
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True)
    text = db.Column(db.String)
    date = db.Column(db.String)
    img_path = db.Column(db.String, default='')

    def __init__(self, title, text, date, img_path=None):
        self.title = title
        self.text = text
        self.date = date
        if img_path:
            self.img_path = img_path

    def __repr__(self):
        return "<Recipe <Title %s> <Date %s> <Img %s>>" % (self.title, self.date, self.img_path)

@app.route('/')
def home():
    app.logger.info("Home page requested")
    return render_template('index.html')

@app.route('/recipes')
def recipes():
    app.logger.info("Recipes requested")
    all_recipes = Recipe.query.all()
    all_recipes_and_imgs = [(r, os.path.basename(r.img_path) if r.img_path is not None else None) for r in all_recipes]
    app.logger.info("%s", str(all_recipes))
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

def add_new_recipe(title, text, path=None):
    date = time.strftime("%d/%m/%Y %H:%M:%S")
    if path:
        new_recipe = Recipe(title, text, date, img_path=path)
    else:
        new_recipe = Recipe(title, text, date)
    app.logger.info("New article upload %s", new_recipe)
    db.session.add(new_recipe)
    db.session.commit()

def delete_recipe(title):
    to_delete = Recipe.query.filter_by(title=title).first()
    if to_delete:
#         try:
#             # TODO: check if no other article is using that image, if so then delete it
#             os.remove(to_delete.img_path)
#         except:
#             app.logger.info("Tried to delete an image which doesnt exist %s", to_delete.img_path)
        db.session.delete(to_delete)
        db.session.commit()

@app.route('/full_recipe/<recipe_id>')
def full_recipe(recipe_id):
    recipe = Recipe.query.filter_by(id=recipe_id).first()
    app.logger.info('%s' % recipe.text)
    return render_template('recipe.html', recipe=recipe)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        app.logger.info(request)
        app.logger.info(request.files)
        if request.form['title'] and request.form['text'] and 'recipe_img' in request.files:
            f = request.files['recipe_img'] 
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(path)
                add_new_recipe(request.form['title'], request.form['text'], path)
            else:
                app.logger.info("File not allowed to be uploaded")
        elif request.form['title_to_delete']:
            delete_recipe(request.form['title_to_delete'])
        return redirect(url_for('recipes'))
    return render_template('edit.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def setup_logging():
    app.logger.setLevel(logging.DEBUG) # Without this you will see no logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = RotatingFileHandler(log_location, maxBytes=10000, backupCount=1)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

def init():
    setup_logging()
    db.create_all()
    db.session.commit()

if __name__ == "__main__":
    init() 
    app.run(debug=True, host="0.0.0.0")
