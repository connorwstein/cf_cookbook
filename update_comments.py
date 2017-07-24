#!/usr/bin/env python
import pexpect
from keys import user, pwd
child = pexpect.spawn('/usr/bin/curl -vvv -u {} http://localhost/update_comments'.format(user))
child.expect('Enter host password for user .*:')
child.sendline(pwd)
child.sendline()
child.close()
