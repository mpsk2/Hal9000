import fileinput
import requests
from requests.auth import HTTPDigestAuth
import sys
import time
from threading import Thread


class RobotMover(object):
    def __init__(self, host='13.95.29.162', user='Default User', password='robotics'):
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
        url = '{url}/{arm}/Remote/{variable}?json=1'.format(url=self.url, arm=arm, variable=variable)
        r = self.session.get(url)
        assert r.status_code == 200, (r, r.content, url)
        return r.json()['_embedded']['_state'][0]['value']

    def check_bool(self, arm, variable):
        return self.check(arm, variable) == "TRUE"

    def set_string(self, arm, variable, text):
        payload = {'value': '"{text}"'.format(text=text)}
        url = '{url}/{arm}/Remote/{variable}?action=set'.format(url=self.url, arm=arm, variable=variable)
        r = self.session.post(url, data=payload)
        assert (r.status_code == 204)
        return r

    def set_bool(self, arm, variable, state):
        payload = {'value': 'true' if state else 'false'}
        url = '{url}/{arm}/Remote/{variable}?action=set'.format(url=self.url, arm=arm, variable=variable)
        r = self.session.post(url, data=payload)
        assert (r.status_code == 204)
        return r

    def move_robot(self, arm, action):
        print(arm, action)
        self.set_string(arm, 'stName', action)

        self.set_bool(arm, 'bStart', True)
        time.sleep(0.5)

        running = self.check_bool(arm, 'bRunning')
        while running:
            running = self.check_bool(arm, 'bRunning')
            time.sleep(0.4)


# the trick seems to run both arms in parralel because of the
# waitAsyncTask directive in the RAPID code


slide = {
    'left': 'T_ROB_L',
    'right': 'T_ROB_R',
}


class RobotArm(Thread):
    def __init__(self, robot_mover, command='None', arm=slide['left']):
        self.command = command
        self.arm = arm
        Thread.__init__(self)

        self.robot_mover = robot_mover

    def run(self):
        self.robot_mover.move_robot(self.arm, self.command)


commandsOneHand = {
    'IKillYou': 11.266000032424927,
    'Kiss': 3.437999963760376,
    'SayHello': 10.531000137329102,
    'SayNo': 5.5,
    'ShakingHands': 5.546999931335449,
}
commandsTwoHands = {
    'Anger': 4.375,
    'Contempt': 3.921999931335449,
    'Excited': 10.57800006866455,
    'GiveMeAHug': 10.203999996185303,
    'GoAway': 9.031000137329102,
    'HandsUp': 5.640999794006348,
    'Happy': 11.07800006866455,
    'Home': 0.5310001373291016,
    'NoClue': 5.171999931335449,
    'Powerful': 11.968999862670898,
    'Scared': 7.7190001010894775,
    'Surprised': 0.5309998989105225,
    'ToDiss': 3.9070000648498535,
}

def parse_command(command, robot_mover):
    command = command.strip()
    if command in commandsOneHand:
        arm = RobotArm(robot_mover, command, slide['right'])
        arm.start()
        arm.join()
    elif command in commandsTwoHands:
        left = RobotArm(robot_mover, command, slide['left'])
        right = RobotArm(robot_mover, command, slide['right'])
        left.start()
        right.start()
        left.join()
        right.join()
    else:
        print('INVALID COMMAND: ' + command)
        parse_command('NoClue', robot_mover)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        robot_mover = RobotMover(host=sys.argv[1])
    else:
        robot_mover = RobotMover()

    for line in fileinput.input():
        try:
            parse_command(line, robot_mover)
        except Exception as ex:
            print(ex)
