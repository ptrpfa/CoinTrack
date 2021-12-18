import os, re, json, datetime
import pandas as pd

# Constants
file_dir = 'history'
regex_trade = '^trade_history.+\.csv'
regex_wallet = '^wallet_history.+\.csv'
regex_token = '^(.+)\/SGD'
regex_swap = '^(.+)\/(.+)'
overall_wallet = {'Deposit':0, 'Withdrawal': 0, 'Referral': 0, 'Overall': 0, 'Fees': 0}
overall_crypto = {} # Bought, Sold, Overall, Reward

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
df_trade['Time & Date'] = pd.to_datetime (df_trade['Time & Date'], format="%d/%m/%Y %H:%M")
df_trade.sort_values(by="Time & Date", inplace=True)

df_wallet = pd.read_csv("%s/%s" % (file_dir,file_wallet))
df_wallet = df_wallet[df_wallet['Status (All)']=='Completed']
df_wallet.drop(columns=['Transaction Hash', 'To Address', 'Received by Address', 'Fee', 'Note', 'Status (All)'], inplace=True)
df_wallet.sort_values(by="Date & Time (*-*)", inplace=True)

js_trade = json.loads(df_trade.to_json(orient='records'))
js_wallet = json.loads(df_wallet.to_json(orient='records'))

# Iterate wallet transactions
for item in js_wallet:
    if (item['Currency(All)']=='SGD'):
        if (item['Type (All)']=='Fiat Deposit'):
            overall_wallet['Deposit'] += item['Amount']
        elif (item['Type (All)']=='Referral Commission'):
            overall_wallet['Referral'] += item['Amount']
        elif (item['Type (All)']=='Fiat Withdrawal'):
            overall_wallet['Withdrawal'] += item['Amount']
    else:
        if (item['Currency(All)'] not in overall_crypto.keys()):
            overall_crypto[item['Currency(All)']] = {'Bought': 0, 'Sold': 0, 'Reward': item['Amount'], 'Overall': 0}
        else:
            overall_crypto[item['Currency(All)']]['Reward'] += item['Amount']

# Iterate trade transactions
for item in js_trade:
    if (item['Side']=='Buy'):
        token = re.match(regex_token, item['Pair']).group(1)
        overall_wallet['Fees'] += float(item['Fee'])
        if (token not in overall_crypto.keys()):
            overall_crypto[token] = {'Bought': item['Total'], 'Sold': 0, 'Reward': 0, 'Overall': 0}
        else:
             overall_crypto[token]['Bought'] += item['Total']
    elif (item['Side']=='Sell'):
        overall_crypto[token]['Sold'] += item['Amount']
    elif (item['Side']=='Swap'):
        # Format: BTC/DOGE (BTC to DOGE) or DOGE/BTC (DOGE to BTC)
        token_from = re.match(regex_swap, item['Pair']).group(1)
        token_to = re.match(regex_swap, item['Pair']).group(2)
        overall_crypto[token_to]['Bought'] += item['Total']
        overall_crypto[token_from]['Sold'] += item['Amount']

# Calculate overall crypto holdings
pass

overall_wallet['Overall'] = round (overall_wallet['Deposit'] + overall_wallet['Referral'] - overall_wallet['Withdrawal'], 2)
print (overall_wallet)
print (overall_crypto)
