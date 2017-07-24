import sys
import sqlite3
# First arg is the db location
conn = sqlite3.connect(sys.argv[1])
c = conn.cursor()
if len(sys.argv) == 3:
    # Table specified
    table = sys.argv[2]
    c.execute("select * from {}".format(table))
    print(c.fetchall())
else:
    # Default print all tables
    c.execute("select name from sqlite_master where type = 'table'")
    for table in c.fetchall():
        s = "select * from {}".format(table[0])
        c.execute(s)
        print(c.fetchall())
