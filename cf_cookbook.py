"""Backend for cashflowcookbook.ca
"""
import logging
from logging.handlers import RotatingFileHandler

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_bootstrap import Bootstrap
from flask_basicauth import BasicAuth
from keys import user, pwd, db_location, log_location, app

app = Flask(__name__)
Bootstrap(app)
BasicAuth(app)

app.config['SECRET_KEY'] = app
app.config['SQLALCHEMY_DATABASE_URI'] = db_location
app.config['BASIC_AUTH_USERNAME'] = user
app.config['BASIC_AUTH_PASSWORD'] = pwd
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)
db = SQLAlchemy(app)

class Recipe(db.Model): # pylint: disable=too-few-public-methods
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True)
    text = db.Column(db.String)

    def __init__(self, title, text):
        self.title = title
        self.text = text

@app.route('/')
def home():
    app.logger.info("Home page requested")
    return render_template('index.html')

@app.route('/recipes')
def recipes():
    app.logger.info("Recipes requested")
    all_recipes = Recipe.query.all()
    app.logger.info("%s", str(all_recipes))
    return render_template('recipes.html', recipes=all_recipes)

@app.route('/utensils')
def utensils():
    app.logger.info("Utensils requested")
    all_utensils = {'Debt sheet to organize what you owe' : 'CFCB_debt_sheet.xlsx',\
                'Net worth sheet to track your finances' : 'CFCB_net_worth.xlsx',\
                'Understanding debt scheduling' : 'CFCB_debt_sched.xlsx'}
    return render_template('utensils.html', utensils=all_utensils)

@app.route("/get_excel/<filename>")
def get_excel(filename):
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

def add_new_recipe(title, text):
    new_recipe = Recipe(title, text)
    app.logger.info("New article upload %s", new_recipe)
    db.session.add(new_recipe)
    db.session.commit()

def delete_recipe(title):
    to_delete = Recipe.query.filter_by(title=title).first()
    if to_delete:
        db.session.delete(to_delete)
        db.session.commit()

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        if request.form['title'] and request.form['text']:
            add_new_recipe(request.form['title'], request.form['text'])
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

def main():
    setup_logging()
    db.drop_all()
    db.create_all()
    app.run(debug=True)

if __name__ == '__main__':
    main()
else:
    setup_logging()
    db.create_all()
