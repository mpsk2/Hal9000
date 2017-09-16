import requests
import sys


class Intent(object):
    def __init__(self, full_response):
        self.full_response = full_response

    def get_summary(self):
        result = {
            'intent': self.full_response['topScoringIntent']['intent'],
            'entities': {
                entity['type']: entity['entity']
                for entity in self.full_response['entities']
            }
        }
        return result


class LUISManager(object):
    def __init__(self, endpoint, subscription_key, staging=True, verbose=True, timezone_offset=60):
        self.endpoint = endpoint
        self.subscription_key = subscription_key
        self.timezone_offset = timezone_offset
        self.staging = staging
        self.verbose = verbose

    def get_intent(self, query):
        params = {
            'subscription-key': self.subscription_key,
            'staging': self.staging,
            'verbose': self.verbose,
            'timezoneOffset': self.timezone_offset,
            'q': query
        }
        r = requests.get(self.endpoint, params=params)
        print r.url
        return Intent(r.json())


default_luis_manager = LUISManager(
    endpoint='https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/4c093489-e725-48c6-b675-aa6281bc4cf9',
    subscription_key='a58b814c31ce4c74b7d33e37be1aeea6'
)


if __name__ == '__main__':
    luis = default_luis_manager
    intent = luis.get_intent(sys.argv[1])
    print intent.get_summary()

