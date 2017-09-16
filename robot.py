import requests
from requests.auth import HTTPDigestAuth
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


class otherArm(Thread):
    def run(self):
        RobotMover().move_robot('T_ROB_L', 'NoClue')


if __name__ == '__main__':
    other = otherArm()
    other.start()
    RobotMover().move_robot('T_ROB_R', 'NoClue')
