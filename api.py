from multiprocessing.dummy import current_process
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
        return CoinhakoAPI.prices[token.upper()] if token.upper() in CoinhakoAPI.prices.keys() else None

class CoingeckoAPI: # For more advanced features

    # Class vars
    base_url = cg_api_url
    cg_tokens = None
    
    # Coingeko endpoints
    token_map_url = base_url + '/coins/list'
    current_price_url = base_url + '/simple/price'

    def __init__(self):
        CoingeckoAPI.cg_tokens = json.loads(requests.get(CoingeckoAPI.token_map_url).text)

    def get_token_cgid(self, token, name):
        cgid = None
        for t in CoingeckoAPI.cg_tokens: # Check for exact matches
            if ((t['symbol'].lower() == token.lower() or t['symbol'].lower() == name.lower()) and (t['name'].lower() == name.lower() or t['name'].lower() == token.lower())):
                cgid = t['id']
                break
        if (cgid is None): # Second pass: check for any token name matches
            for t in CoingeckoAPI.cg_tokens:
                if ((t['symbol'].lower() == token.lower()) and (t['name'].lower() in name.lower() or name.lower() in t['name'].lower())):
                    cgid = t['id']
                    break
        if (cgid is None): # Third pass: check for any one match otherwise
            for t in CoingeckoAPI.cg_tokens:
                if ((t['symbol'].lower() == token.lower()) or (t['name'].lower() == name.lower())):
                    cgid = t['id']
                    break
        return cgid

    def get_token_details(self, token_cgid): # Get details for a token (name and current price)
        details = {'name': None, 'price': None}
        payload = {'id': token_cgid, 'localization': False, 'tickers': False, 'community_data': False, 'developer_data': False, 'sparkline': False}
        token_details_url = f'{CoingeckoAPI().base_url}/coins/{token_cgid}'
        response = json.loads(requests.get(token_details_url, params=payload).text)
        details['name'] = response['name']
        details['price'] = response['market_data']['current_price']['sgd']
        return details

    def get_token_price(self, token_cgid): # Get current price for a token
        payload = {'ids': token_cgid, 'vs_currencies': 'sgd'}
        response = json.loads(requests.get(CoingeckoAPI.current_price_url, params=payload).text)
        current_price = response[token_cgid]['sgd']
        return current_price

    def get_token_historical_price(self, token_cgid, date): # Get historical price for a token
        payload = {'id': token_cgid, 'date': date, 'localization': False}
        token_history_url = f'{CoingeckoAPI().base_url}/coins/{token_cgid}/history'
        response = json.loads(requests.get(token_history_url, params=payload).text)
        token_price = response['market_data']['current_price']['sgd']
        return token_price