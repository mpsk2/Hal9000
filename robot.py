import requests
from requests.auth import HTTPDigestAuth
import urllib
import time
from threading import Thread

# Thanks to Phaiax for the code fixing  https://github.com/Phaiax/OhOnlyMusli/tree/master/pytest

url = 'http://13.95.29.162/rw'
auth = HTTPDigestAuth('Default User', 'robotics')

session = requests.session()


# Get authenticated
r0 = session.get(url + '/rapid/symbol/data/RAPID/'+'T_ROB_R'+'/Remote/bStart?json=1',
                   auth=auth)
assert(r0.status_code == 200)


def check(arm, variable):
    r = session.get(url + '/rapid/symbol/data/RAPID/'+arm+'/Remote/'+variable+'?json=1')
    assert(r.status_code == 200)
    return r.json()['_embedded']['_state'][0]['value']

def checkBool(arm, variable):
    return True if check(arm, variable) == "TRUE" else False

def setString(arm, variable, text):
    payload={'value':'"'+text+'"'}
    r = session.post(url + '/rapid/symbol/data/RAPID/'+arm+'/Remote/'+variable+'?action=set',
                     data=payload)
    print(r)
    print(r.text)
    assert(r.status_code == 204)
    return r

def setBool(arm, variable, state):
    payload={'value': 'true' if state else 'false' }
    r = session.post(url + '/rapid/symbol/data/RAPID/'+arm+'/Remote/'+variable+'?action=set',
                     data=payload)
    print(r)
    print(r.text)
    assert(r.status_code == 204)
    return r

def moveRobot(arm,action):
    print("RUNNING:" + check(arm, 'bRunning'))

    setString(arm, 'stName', action)

    print("bStart:" + check(arm, 'bStart'))

    setBool(arm, 'bStart', True);

    print("bStart:" + check(arm, 'bStart'))
    time.sleep(0.5)

    running = checkBool(arm, 'bRunning')
    while running:
        running = checkBool(arm, 'bRunning')
        print("RUNNING:" + str(running))
        time.sleep(0.4)


# the trick seems to run both arms in parralel because of the
# waitAsyncTask directive in the RAPID code

class otherArm(Thread):
    def run(self):
        moveRobot('T_ROB_L','NoClue')


other = otherArm()
other.start()
moveRobot('T_ROB_R','NoClue')