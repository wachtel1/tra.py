import requests
import uuid


class MicrosoftTranslator():
    def __init__(self, url=None, apiKey=None, location=None):
        self.url = url
        self.apiKey = apiKey
        self.location = location

    def translate(self, q, source=None, target="en"):
        path = "/translate"
        url = self.url + path

        headers = {
            'Ocp-Apim-Subscription-Key': self.apiKey,
            'Ocp-Apim-Subscription-Region': self.location,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        if source == None:
            params = {
                'api-version': '3.0',
                'to': [target]
            }
        else:
            params = {
                'api-version': '3.0',
                'from': source,
                'to': [target]
            }

        body = [{
            'text': q
        }]

        request = requests.post(
            url, params=params, headers=headers, json=body)
        response = request.json()
        return response[0]['translations'][0]['text']

    def detect(self, q):
        path = '/detect'
        url = self.url + path

        headers = {
            'Ocp-Apim-Subscription-Key': self.apiKey,
            'Ocp-Apim-Subscription-Region': self.location,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        params = {
            'api-version': '3.0'
        }

        body = [{
            'text': q
        }]

        request = requests.post(
            url, params=params, headers=headers, json=body)
        response = request.json()
        return response[0]['language']
