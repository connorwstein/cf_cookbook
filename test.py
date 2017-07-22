import os
import cf_cookbook
import base64
from StringIO import StringIO
import unittest
import tempfile
import sqlite3
import os
import subprocess
from keys import user, pwd

class CashflowCookbookTest(unittest.TestCase):

    def setUp(self):
        self.db_fd, cf_cookbook.app.config['DATABASE'] = tempfile.mkstemp()
        cf_cookbook.app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///{0}".format(cf_cookbook.app.config["DATABASE"])
        cf_cookbook.app.testing = True
        self.app = cf_cookbook.app.test_client()
        cf_cookbook.init()
        cf_cookbook.setup_logging()

    def test_landing_page(self):
        rv = self.app.get('/', headers=dict(Authorization='Basic ' + base64.b64encode("{0}:{1}".format(user,pwd))))
        assert "Why am I here" in rv.data

    def test_add_del_article(self):
        cf_cookbook.app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "test_img")
        subprocess.call("mkdir -p test_img", shell=True)
        rv = self.app.post('/edit', content_type='multipart/form-data',
                data=dict(title="test recipe", text="my test", recipe_img=(StringIO('test'), 'testimg.jpg')),
                headers=dict(Authorization='Basic ' + base64.b64encode("{0}:{1}".format(user,pwd))))

        assert "Success creating article test recipe" in rv.data
        assert "testimg.jpg" in subprocess.check_output("ls test_img", shell=True)
        conn = sqlite3.connect(cf_cookbook.app.config["DATABASE"])
        c = conn.cursor()
        c.execute("select * from recipe")
        db_results = c.fetchall()
        assert "test recipe" and "my test" and "1" in str(db_results[0])
        # Now delete that article
        rv = self.app.post('/edit', content_type='multipart/form-data',
                data=dict(title="", text="", recipe_img="", title_to_delete="test recipe"),
                headers=dict(Authorization='Basic ' + base64.b64encode("{0}:{1}".format(user,pwd))))

        assert "Successfully deleted" in rv.data
        # Check it is gone from the db
        conn = sqlite3.connect(cf_cookbook.app.config["DATABASE"])
        c = conn.cursor()
        c.execute("select * from recipe")
        db_results = c.fetchall()
        assert db_results == []
        # Check the image file is gone as well
        assert "testimg.jpg" not in subprocess.check_output("ls test_img", shell=True)
        #subprocess.call("rm -rf test_img", shell=True)

    def test_add_invalid_file_name(self):
        cf_cookbook.app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "test_img")
        subprocess.call("mkdir -p test_img", shell=True)
        rv = self.app.post('/edit', content_type='multipart/form-data',
                data=dict(title="test recipe", text="my test", recipe_img=(StringIO('test'), 'testimg.xyz')),
                headers=dict(Authorization='Basic ' + base64.b64encode("{0}:{1}".format(user,pwd))))

        conn = sqlite3.connect(cf_cookbook.app.config["DATABASE"])
        assert "Invalid file extension" in rv.data
        assert "testimg.xyz" not in subprocess.check_output("ls test_img", shell=True)
        subprocess.call("rm -rf test_img", shell=True)

    def test_good_email(self):
        rv = self.app.post('/subscribe', content_type='multipart/form-data',
                data=dict(email="test@example.com"),
                headers=dict(Authorization='Basic ' + base64.b64encode("{0}:{1}".format(user,pwd))))
        conn = sqlite3.connect(cf_cookbook.app.config["DATABASE"])
        c = conn.cursor()
        c.execute("select * from subscriber")
        db_results = c.fetchall()
        print(db_results)
        assert "test@example.com" in str(db_results[0])

    def test_bad_email(self):
        rv = self.app.post('/subscribe', content_type='multipart/form-data',
                data=dict(email="lasdkfalsdkjf"),
                headers=dict(Authorization='Basic ' + base64.b64encode("{0}:{1}".format(user,pwd))))
        conn = sqlite3.connect(cf_cookbook.app.config["DATABASE"])
        c = conn.cursor()
        c.execute("select * from subscriber")
        db_results = c.fetchall()
        assert db_results == []

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(cf_cookbook.app.config['DATABASE'])

if __name__ == '__main__':
    unittest.main()
