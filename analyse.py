from config import *
from api import Api
import os, re, json
import pandas as pd

# Variables
overall_wallet = {  'Fiat': 0, 'Deposit':0, 'Withdrawal': 0, 
                    'Referral': 0, 'Fees': 0, 'Card Purchase': 0, 
                    'Overall': 0, 'Principal': 0, 'Portfolio': 0, 
                    'Returns': 0, 'Returns Ticker': 0}
overall_crypto = {} # {'Token': {'Bought': 0, 'Sold': 0, 'Reward': 0, 'Staked': 0, 'Redeemed': 0, 'Earned': 0, 'Overall': 0}, {..}}
current_crypto = {}
past_crypto = {}

def summarise ():

    ticker = ''
    if (overall_wallet['Returns Ticker'] > 0):
        ticker = '+ '
    elif (overall_wallet['Returns Ticker'] < 0):
        ticker = '- '

    print (f"Report generated on: {ch_api.last_update}\n")
    
    print ('-' * 8, 'Summary', '-' * 8, sep='\n')
    print(f"Portfolio Value: ${overall_wallet['Portfolio']}\nReturns: {ticker}${overall_wallet['Returns']} ({ticker}{round(100 * (overall_wallet['Returns'] / overall_wallet['Principal']), 2)}%)\nPrincipal: ${overall_wallet['Principal']}\n")

    print ('-' * 6, 'Wallet', '-' * 6, sep='\n')
    print (f"Overall: ${overall_wallet['Overall']} (Principal + Fiat Holdings)\nFiat Holdings: ${overall_wallet['Fiat']}\n")

    print ('-' * 16, '$ In/Out & Fees', '-' * 16, sep='\n')
    print (f"Card Purchase: ${overall_wallet['Card Purchase']}\nFiat Deposit: ${overall_wallet['Deposit']}\nWithdrawals: ${overall_wallet['Withdrawal']}\nReferrals: + ${overall_wallet['Referral']}\nFees: - ${overall_wallet['Fees']}")
    
    print ("\nCurrent crypto holdings:")
    for k, v in current_crypto.items():
        print (k, v)
    
    # Future implementations:
    # 1) Token breakdown
    #   - Purchased # (Holdings)
    #   - Cost basis ($/share and Total $) [weighted average]
    #   - Current price ($/share and Total $)
    # 2) Portfolio allocations (%)

# Program entrypoint
list_dir = os.listdir(file_dir)
list_dir.remove('.gitignore')
ch_api = Api()

for f in list_dir:
    if (re.match(regex_trade, f)):
        file_trade = f
    elif (re.match(regex_wallet,f)):
        file_wallet = f

# Clean trade history
df_trade = pd.read_csv("%s/%s" % (file_dir,file_trade))
df_trade = df_trade[df_trade['Status']=='Completed']
df_trade.drop(columns=['Type', 'Average Price', 'Executed', 'Status'], inplace=True)
# df_trade['Time & Date'] = pd.to_datetime (df_trade['Time & Date'], format="%d/%m/%Y %H:%M")
df_trade.sort_values(by="Time & Date", inplace=True)

# Clean wallet history
df_wallet = pd.read_csv("%s/%s" % (file_dir,file_wallet))
df_wallet = df_wallet[df_wallet['Status (All)']=='Completed']
df_wallet.drop(columns=['Transaction Hash', 'To Address', 'Received by Address', 'Fee', 'Note', 'Status (All)'], inplace=True)
df_wallet.sort_values(by="Date & Time (*-*)", inplace=True)

# Convert dataframes to json
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
            overall_wallet['Fees'] += withdrawal_fee
    else:
        if (item['Currency(All)'] not in overall_crypto.keys()):
            if (item['Type (All)']=='Earn'): # Check if any crypto is being staked
                overall_crypto[item['Currency(All)']] = {'Bought': 0, 'Sold': 0, 'Reward': 0, 'Staked': item['Amount'], 'Redeemed': 0, 'Earned': 0, 'Overall': 0}
            else:
                overall_crypto[item['Currency(All)']] = {'Bought': 0, 'Sold': 0, 'Reward': item['Amount'], 'Staked': 0, 'Redeemed': 0, 'Earned': 0, 'Overall': 0}
        else:
            if (item['Type (All)']=='Earn'): # Check if any crypto is being staked
                overall_crypto[item['Currency(All)']]['Staked'] += item['Amount']
            elif (item['Type (All)']=='Redemption'): # Check if any crypto staked has been redeemed
                overall_crypto[item['Currency(All)']]['Redeemed'] += item['Amount']
            else:
                overall_crypto[item['Currency(All)']]['Reward'] += item['Amount']

# Calculate preliminary fiat wallet holdings
overall_wallet['Fiat'] = overall_wallet['Deposit'] + overall_wallet['Referral']

# Iterate through trade transactions
for item in js_trade:
    if (item['Side']=='Buy'):
        token = re.match(regex_token, item['Pair']).group(1)
        overall_wallet['Fees'] += float(item['Fee'])
        overall_wallet['Fiat'] -= item['Amount']
        if (token not in overall_crypto.keys()):
            overall_crypto[token] = {'Bought': item['Total'], 'Sold': 0, 'Reward': 0, 'Staked': 0, 'Redeemed': 0, 'Earned': 0, 'Overall': 0}
        else:
             overall_crypto[token]['Bought'] += item['Total']
    elif (item['Side']=='Sell'):
        token = re.match(regex_token, item['Pair']).group(1)
        overall_wallet['Fees'] += float(item['Fee'])
        overall_wallet['Fiat'] += item['Total']
        overall_crypto[token]['Sold'] += item['Amount']
    elif (item['Side']=='Swap'):
        # Format: BTC/DOGE (BTC to DOGE) or DOGE/BTC (DOGE to BTC)
        token_from = re.match(regex_swap, item['Pair']).group(1)
        token_to = re.match(regex_swap, item['Pair']).group(2)
        overall_crypto[token_to]['Bought'] += item['Total']
        overall_crypto[token_from]['Sold'] += item['Amount']
        # Get fees of token swap and convert to fiat (Note: Fees are paid in the new token's currency)
        new_token_price = ch_api.get_price(token_to)['buy_price']
        fees = item['Fee'] * float(new_token_price)
        overall_wallet['Fees'] += fees

# Get fiat wallet holdings
overall_wallet['Fiat'] -= overall_wallet['Withdrawal']
if (overall_wallet['Fiat'] < 0): # negative wallet balance would indicate purchase through card, which is not indicated by Coinhako's exported file
    overall_wallet['Card Purchase'] = abs(overall_wallet['Fiat'])
    overall_wallet['Fiat'] = 0

# Calculate overall crypto holdings
for token, holdings in overall_crypto.items():
    # Calculate staked earnings
    overall_crypto[token]['Earned'] = holdings['Redeemed'] - holdings['Staked'] if (holdings['Redeemed'] > holdings['Staked']) else holdings['Earned']
    holdings['Earned'] = overall_crypto[token]['Earned']
    overall = round(holdings['Bought'] + holdings['Reward'] + holdings['Earned'] - holdings['Sold'], min_precision)
    overall_crypto[token]['Overall'] = overall
    if (overall > 0):
        current_crypto[token] = overall_crypto[token]
    else:
        past_crypto[token] = overall_crypto[token]

# Calculate overall investment
overall_wallet['Overall'] = round (overall_wallet['Deposit'] + overall_wallet['Referral'] + overall_wallet['Fiat'] - overall_wallet['Withdrawal'], 2)
overall_wallet['Principal'] = round (overall_wallet['Overall'] - overall_wallet['Fiat'], 2)
for k, v in overall_wallet.items():
    overall_wallet[k] = round (overall_wallet[k], 2)

# Calculate current crypto holdings valuation
ch_api.update_prices()
for token in current_crypto.keys():
    current_crypto[token]['Price'] = float(ch_api.get_price(token)['sell_price'])
    current_crypto[token]['Current Value'] = round(current_crypto[token]['Price'] * current_crypto[token]['Overall'], 2)
    overall_wallet['Portfolio'] = round(overall_wallet['Portfolio'] + current_crypto[token]['Current Value'], 2)
    
overall_wallet['Returns'] = round(overall_wallet['Portfolio'] - overall_wallet['Overall'], 2)
if (overall_wallet['Returns'] > 0):
    overall_wallet['Returns Ticker'] = 1
elif (overall_wallet['Returns'] < 0):
    overall_wallet['Returns Ticker'] = -1

# Output
summarise()