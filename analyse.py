import os, re, json, datetime
import pandas as pd
from config import *

# Constants
file_dir = 'history'
regex_trade = '^trade_history.+\.csv'
regex_wallet = '^wallet_history.+\.csv'
regex_token = '^(.+)\/SGD'
regex_swap = '^(.+)\/(.+)'
overall_wallet = {'Deposit':0, 'Withdrawal': 0, 'Referral': 0, 'Overall': 0, 'Fees': 0}
overall_crypto = {} # {'Token': {'Bought': 0, 'Sold': 0, 'Overall': 0, 'Reward': 0}, {..}}
current_crypto = {}
past_crypto = {}

# Functions
def date_difference (start, end=datetime.datetime.today()):
    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M')
    diff = end - start
    diff_month = end.month - start.month
    diff_day = diff.days - (diff_month * 28) # 1 month hardcoded as 28 days
    return "%s month(s) & %s day(s)" % (diff_month, diff_day)

# Entrypoint
list_dir = os.listdir(file_dir)
list_dir.remove('.gitignore')

for f in list_dir:
    if (re.match(regex_trade, f)):
        file_trade = f
    elif (re.match(regex_wallet,f)):
        file_wallet = f

df_trade = pd.read_csv("%s/%s" % (file_dir,file_trade))
df_trade = df_trade[df_trade['Status']=='Completed']
df_trade.drop(columns=['Type', 'Average Price', 'Executed', 'Status'], inplace=True)
# df_trade['Time & Date'] = pd.to_datetime (df_trade['Time & Date'], format="%d/%m/%Y %H:%M")
df_trade.sort_values(by="Time & Date", inplace=True)
# df_trade = df_trade.round(dp_precision)

df_wallet = pd.read_csv("%s/%s" % (file_dir,file_wallet))
df_wallet = df_wallet[df_wallet['Status (All)']=='Completed']
df_wallet.drop(columns=['Transaction Hash', 'To Address', 'Received by Address', 'Fee', 'Note', 'Status (All)'], inplace=True)
df_wallet.sort_values(by="Date & Time (*-*)", inplace=True)
# df_wallet = df_wallet.round(dp_precision)

js_trade = json.loads(df_trade.to_json(orient='records'))
js_wallet = json.loads(df_wallet.to_json(orient='records'))

# Iterate through wallet transactions
for item in js_wallet:
    if (item['Currency(All)']=='SGD'):
        if (item['Type (All)']=='Fiat Deposit'):
            overall_wallet['Deposit'] += item['Amount']
        elif (item['Type (All)']=='Referral Commission'):
            overall_wallet['Referral'] += item['Amount']
        elif (item['Type (All)']=='Fiat Withdrawal'):
            overall_wallet['Withdrawal'] += item['Amount']
    else:
        if ('earn' not in item['Type (All)'].lower()):
            if (item['Currency(All)'] not in overall_crypto.keys()):
                overall_crypto[item['Currency(All)']] = {'Bought': 0, 'Sold': 0, 'Reward': item['Amount'], 'Overall': 0}
            else:
                overall_crypto[item['Currency(All)']]['Reward'] += item['Amount']

# Iterate through trade transactions
for item in js_trade:
    if (item['Side']=='Buy'):
        token = re.match(regex_token, item['Pair']).group(1)
        overall_wallet['Fees'] += float(item['Fee'])
        if (token not in overall_crypto.keys()):
            overall_crypto[token] = {'Bought': item['Total'], 'Sold': 0, 'Reward': 0, 'Overall': 0}
        else:
             overall_crypto[token]['Bought'] += item['Total']
    elif (item['Side']=='Sell'):
        token = re.match(regex_token, item['Pair']).group(1)
        overall_wallet['Fees'] += float(item['Fee'])
        overall_crypto[token]['Sold'] += item['Amount']
    elif (item['Side']=='Swap'):
        # Format: BTC/DOGE (BTC to DOGE) or DOGE/BTC (DOGE to BTC)
        token_from = re.match(regex_swap, item['Pair']).group(1)
        token_to = re.match(regex_swap, item['Pair']).group(2)
        overall_crypto[token_to]['Bought'] += item['Total']
        overall_crypto[token_from]['Sold'] += item['Amount']
        # Get fees of crypto and convert to fiat
        pass

# Calculate overall crypto holdings
for token, holdings in overall_crypto.items():
    overall = round(holdings['Bought'] + holdings['Reward'] - holdings['Sold'], min_precision)
    overall_crypto[token]['Overall'] = overall
    if (overall > 0):
        current_crypto[token] = overall_crypto[token]
    else:
        past_crypto[token] = overall_crypto[token]

# Calculate overall investment
overall_wallet['Overall'] = round (overall_wallet['Deposit'] + overall_wallet['Referral'] - overall_wallet['Withdrawal'], 2)
for k, v in overall_wallet.items():
    overall_wallet[k] = round (overall_wallet[k], 2)

print ("Wallet:", overall_wallet)
print ("Current crypto holdings:")
for k, v in current_crypto.items():
    print (k, v)
print ("Past crypto Holdings:")
for k, v in past_crypto.items():
    print (k, v)

# Get overall investment/trading duration
start_date = js_trade[0]['Time & Date'] if js_trade[0]['Time & Date'] < js_wallet[0]['Date & Time (*-*)'] else js_wallet[0]['Date & Time (*-*)']
print ('Duration:', date_difference(start_date))
