import logging
from logging.handlers import RotatingFileHandler

from oauth import OAuthSignIn
from keys import APP, FB_APP, FB_SECRET

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)

app.config['SECRET_KEY'] = APP
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cf_cookbook.db'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': FB_APP,
        'secret': FB_SECRET
    }
}

db = SQLAlchemy(app)
lm = LoginManager(app)

class User(UserMixin, db.Model):
    """Inheiriting from UserMixin will cause is_authenticated, 
    is_active, is_anonymous, and get_id to have default implementations. 
    The current_user object will have access to social_id, username and
    email based on the id. 
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def home():
    app.logger.info("Current user anonymous: %s" % (current_user.is_anonymous))  
    return render_template('index.html') 

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    app.logger.info("Attempting to authorize")
    if not current_user.is_anonymous:
        return redirect(url_for('home'))
    # Get the appropriate OAuthSignIn subclass
    # depending on how which provider the user has selected
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    """Authorize user and then login with login manager. Create user
    in users table of cf_cookbook.db if that user does not exit already
    """
    if not current_user.is_anonymous:
        return redirect(url_for('home'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('home'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, username=username, email=email)
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    app.logger.info("Logged in %s" % (current_user.username))
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    user = current_user
    user.authenticated = False
    app.logger.info("Logging out %s" % (current_user.username))
    logout_user()
    return redirect(url_for('home'))



if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = RotatingFileHandler('cf_cookbook.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    db.drop_all()
    db.create_all()
    app.run(debug=True, port=5000)
  



