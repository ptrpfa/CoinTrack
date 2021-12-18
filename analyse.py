import os, re, json, datetime
import pandas as pd

# Constants
file_dir = 'history'
regex_trade = '^trade_history.+\.csv'
regex_wallet = '^wallet_history.+\.csv'
overall_wallet = {'SGD':0}

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
df_trade.sort_values(by="Time & Date", inplace=True)

df_wallet = pd.read_csv("%s/%s" % (file_dir,file_wallet))
df_wallet = df_wallet[df_wallet['Status (All)']=='Completed']
df_wallet.drop(columns=['Transaction Hash', 'To Address', 'Received by Address', 'Fee', 'Note', 'Status (All)'], inplace=True)
df_wallet.sort_values(by="Date & Time (*-*)", inplace=True)

js_trade = json.loads(df_trade.to_json(orient='records'))
js_wallet = json.loads(df_wallet.to_json(orient='records'))

# Iterate wallet transactions (To figure out)
for item in js_wallet:
    if (item['Currency(All)']=='SGD'):
        if (item['Type (All)']=='Fiat Deposit' or item['Type (All)']=='Referral Commission'):
            # Add to wallet
            overall_wallet['SGD']+=item['Amount']
            print ("Addition:")
            print (item)
            print ("Wallet: ", overall_wallet['SGD'])
        elif (item['Type (All)']=='Fiat Withdrawal'):
            # Remove from wallet
            # overall_wallet['SGD']-=item['Amount']
            # print ("Removal:")
            # print (item)
            # print ("Wallet: ", overall_wallet['SGD'])
            pass
    else:
        pass