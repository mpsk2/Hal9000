from enum import Enum
import requests
from requests.auth import HTTPDigestAuth
import time
from threading import Thread
import fileinput

class RobotMover(object):
    def __init__(self, host='13.93.10.114', user='Default User', password='robotics'):
        self.host = host
        self.user = user
        self.password = password
        self.url = 'http://{host}/rw'.format(host=host)
        self.url = '{url}/rapid/symbol/data/RAPID'.format(url=self.url)
        self.auth = HTTPDigestAuth(user, password)

        self.session = requests.session()

        resp = self.session.get(
            '{url}/T_ROB_R/Remote/bStart?json=1'.format(url=self.url),
            auth=self.auth
        )

        assert (resp.status_code == 200)

    def check(self, arm, variable):
        print(self.host)
        r = self.session.get('{url}/{arm}/Remote/{variable}?json=1'
                             .format(url=self.url, arm=arm, variable=variable))
        assert (r.status_code == 200)
        return r.json()['_embedded']['_state'][0]['value']

    def check_bool(self, arm, variable):
        return self.check(arm, variable) == "TRUE"

    def set_string(self, arm, variable, text):
        payload = {'value': '"{text}"'.format(text=text)}
        url = '{url}/{arm}/Remote/{variable}?action=set'.format(url=self.url, arm=arm, variable=variable)
        r = self.session.post(url, data=payload)
        print(url, r, r.text)
        assert (r.status_code == 204)
        return r

    def set_bool(self, arm, variable, state):
        payload = {'value': 'true' if state else 'false'}
        url = '{url}/{arm}/Remote/{variable}?action=set'.format(url=self.url, arm=arm, variable=variable)
        r = self.session.post(url, data=payload)
        print(url, r, r.text)
        assert (r.status_code == 204)
        return r

    def move_robot(self, arm, action):
        print("RUNNING:" + self.check(arm, 'bRunning'))

        self.set_string(arm, 'stName', action)

        print("bStart:" + self.check(arm, 'bStart'))

        self.set_bool(arm, 'bStart', True)

        print("bStart:" + self.check(arm, 'bStart'))
        time.sleep(0.5)

        running = self.check_bool(arm, 'bRunning')
        while running:
            running = self.check_bool(arm, 'bRunning')
            print("RUNNING:" + str(running))
            time.sleep(0.4)


# the trick seems to run both arms in parralel because of the
# waitAsyncTask directive in the RAPID code

class Side(Enum):
    left = 'T_ROB_L'
    right = 'T_ROB_R'


class RobotArm(Thread):
    command = None
    arm = None

    def __init__(self, command='None', arm=Side.left):
        self.command = command
        self.arm = arm
        Thread.__init__(self)

    def run(self):
        RobotMover().move_robot(self.arm, self.command)



commandsOneHand = [
"Kiss",
"SayHello",
"SayNo",
"ShakingHands",
"IKillYou",
]

commandsTwoHands = [
"Home",
"Contempt",
"NoClue",
"HandsUp",
"Surprised",
"ToDiss",
"Anger",
"Excited",
"GiveMeAHug",
"GoAway",
"Happy",
"Powerful",
"Scared",
]

def parse_command(line):
    command = line.strip()
    if command in commandsOneHand:
        arm = RobotArm(command, Side.right)
        arm.start()
        arm.join()
    elif command in commandsTwoHands:
        left = RobotArm(command, Side.left)
        right = RobotArm(command, Side.right)
        left.start()
        right.start()
        left.join()
        right.join()
    else:
        print('INVALID COMMAND: ' + command)
        parse_command('NoClue')


if __name__ == '__main__':
    for line in fileinput.input():
        parse_command(line)

