from flask import Flask
from flask import jsonify
from flask import render_template
import requests
from requests.auth import HTTPDigestAuth
import sys
import time
from threading import Thread

app = Flask(__name__)

ROBOT_IP = '172.20.0.224'


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


commands_one_hand = {
    'IKillYou': (11.266000032424927, False),
    'Kiss': (3.437999963760376, False),
    'SayHello': (10.531000137329102, True),
    'SayNo': (5.5, True),
    'ShakingHands': (5.546999931335449, False),
}
commands_two_hands = {
    'Anger': (4.375, False),
    'Contempt': (3.921999931335449, False),
    'Excited': (10.57800006866455, True),
    'GiveMeAHug': (10.203999996185303, False),
    'GoAway': (9.031000137329102, False),
    'HandsUp': (5.640999794006348, True),
    'Happy': (11.07800006866455, True),
    'Home': (0.5310001373291016, False),
    'NoClue': (5.171999931335449, True),
    'Powerful': (11.968999862670898, True),
    'Scared': (7.7190001010894775, False),
    'Surprised': (0.5309998989105225, False),
    'ToDiss': (3.9070000648498535, True),
}

commands_all = dict(commands_two_hands, **commands_one_hand)

def parse_command(command, robot_mover):
    command = command.strip()
    if command in commands_one_hand:
        arm = RobotArm(robot_mover, command, slide['right'])
        arm.start()
        arm.join()
    elif command in commands_two_hands:
        left = RobotArm(robot_mover, command, slide['left'])
        right = RobotArm(robot_mover, command, slide['right'])
        left.start()
        right.start()
        left.join()
        right.join()
    else:
        print('INVALID COMMAND: ' + command)
        parse_command('NoClue', robot_mover)



if len(sys.argv) > 1:
    robot_mover = RobotMover(host=sys.argv[1])
else:
    robot_mover = RobotMover()


@app.route('/cmds/<cmd>')
def command(cmd):
    try:
        start = time.time()
        parse_command(cmd, robot_mover)
        end = time.time()
    except Exception as ex:
        return jsonify({'error': str(ex)})
    else:
        return jsonify({'time': end - start})


@app.route('/cmds')
def commands():
    return render_template('list_commands.html', commands=sorted(commands_all.iteritems()))

@app.route('/times')
def times():
    return jsonify(dict(commands_one_hand, **commands_two_hands))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
