from config import ch_api_url, cg_api_url
from datetime import datetime
import requests, json

class CoinhakoAPI: # Simply for getting prices offered on Coinhako platform

    # Class vars
    url = ch_api_url
    prices = {}
    last_update = ''

    def __init__ (self):
        self.update_prices()

    def update_prices(self):
        dump = requests.get(ch_api_url).text
        dump = json.loads(dump)['data']
        for i in dump:
            token = i['base']
            i.pop('base')
            i.pop('counter')
            CoinhakoAPI.prices[token] = i
        CoinhakoAPI.last_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def get_price(self, token):
        return CoinhakoAPI.prices[token.upper()]

class CoingeckoAPI: # For more advanced features

    # Class vars
    base_url = cg_api_url
    
    # Coingeko endpoints
    token_map_url = base_url + '/coins/list'

    def get_token_cgid(self, token, name):
        cgid = None
        cg_tokens = json.loads(requests.get(CoingeckoAPI.token_map_url).text)
        for t in cg_tokens:
            if ((t['symbol'].lower() == token.lower()) and (t['name'].lower() == name.lower())):
                cgid = t['id']
                break
        return cgid

    def get_token_price(self, token_cgid, date):
        payload = {'id': token_cgid, 'date': date, 'localization': False}
        token_history_url = f'{CoingeckoAPI().base_url}/coins/{token_cgid}/history'
        response = json.loads(requests.get(token_history_url, params=payload).text)
        token_price = response['market_data']['current_price']['sgd']
        return token_price