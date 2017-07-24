from cf_cookbook import db

class Recipe(db.Model): # pylint: disable=too-few-public-methods
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True)
    text = db.Column(db.String)
    date = db.Column(db.String)
    img_path = db.Column(db.String, unique=True)
    comments = db.relationship('Comment', backref='title', lazy='dynamic')

    def __init__(self, title, text, date, img_path):
        self.title = title
        self.text = text
        self.date = date
        self.img_path = img_path

    def get_comments(self):
        return Comment.query.filter_by(recipe_id=recipe.id).order_by(Comment.timestamp.desc())

    def __repr__(self):
        return "<Recipe <Title %s> <Date %s> <Img %s>>" % (self.title, self.date, self.img_path)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    # Foreign key meaning it references the primary key in another table
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))

    def __init__(self, user, body, timestamp, recipe_id):
        self.user = user
        self.body = body
        self.timestamp = timestamp
        self.recipe_id = recipe_id

    def __repr__(self):
        return '<Post %r>' % (self.body)


class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return "<Subscriber <Email %s>>" % (self.email)
