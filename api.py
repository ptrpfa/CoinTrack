from config import api_url
from datetime import datetime
import requests, json

class Api:

    # Class vars
    url = api_url
    prices = {}
    last_update = ''

    def __init__ (self):
        self.update_prices()

    def update_prices(self):
        dump = requests.get(api_url).text
        dump = json.loads(dump)['data']
        for i in dump:
            token = i['base']
            i.pop('base')
            i.pop('counter')
            Api.prices[token] = i
        Api.last_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def get_price(self, token):
        return Api.prices[token]