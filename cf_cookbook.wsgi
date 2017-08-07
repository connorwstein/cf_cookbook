activate_this = '/var/www/cf_cookbook/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys

flaskfirst = "/var/www/cf_cookbook"
if not flaskfirst in sys.path:
    sys.path.insert(0, flaskfirst)
import cf_cookbook
cf_cookbook.init()
from cf_cookbook import app as application
