from flask import Flask, render_template
from flask_bootstrap import Bootstrap
app = Flask(__name__)

Bootstrap(app)
@app.route('/')
def hello_world():
    return render_template('index.html') 

@app.route('/test')
def hello_world_2():
    return render_template('test.html') 

if __name__ == '__main__':
    Bootstrap(app)
    app.run(port=5000)
  





