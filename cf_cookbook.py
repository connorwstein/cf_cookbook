"""Backend for cashflowcookbook.ca
"""
import logging
from logging.handlers import RotatingFileHandler

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recipes')
def recipes():
    return render_template('recipes.html')

@app.route('/about')
def about():
    return render_template('about.html')

def main():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = RotatingFileHandler(log_location, maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    db.drop_all()
    db.create_all()
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    main()
