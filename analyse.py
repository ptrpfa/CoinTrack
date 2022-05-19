from config import *
from api import CoinhakoAPI, CoingeckoAPI
import os, re, json
import pandas as pd

# ** Variables **
overall_wallet = {  'Fiat': 0, 'Deposit':0, 'Withdrawal': 0, 
                    'Referral': 0, 'Fees': 0, 'Card Purchase': 0, 
                    'Overall': 0, 'Principal': 0, 'Portfolio': 0, 
                    'Returns': 0, 'Returns Ticker': 0}
overall_crypto = {}
baseline_crypto = {'Bought': 0, 'Sold': 0, 'Reward': 0, 'Send': 0, 'Receive': 0, 'Referral': 0, 'Staked': 0, 'Redeemed': 0, 'Earned': 0, 'Overall': 0, 'Fees': 0} # Fees are not further broken down into the sub-categories of Transfer Fees / Swap Fees
current_crypto = {}
past_crypto = {}

# ** APIs **
ch_api = CoinhakoAPI()
cg_api = CoingeckoAPI()
ch_cgid_mappings = {} # Coinhako token listings' mapping to their equivalent Coingecko IDs

# ** Functions **
def summarise ():

    ticker = ''
    if (overall_wallet['Returns Ticker'] > 0):
        ticker = '+ '
    elif (overall_wallet['Returns Ticker'] < 0):
        ticker = '- '

    print (f"Report generated on: {ch_api.last_update}\n")
    
    print ('-' * 8, 'Summary', '-' * 8, sep='\n')
    print(f"Portfolio Value: ${overall_wallet['Portfolio']}\nReturns: {ticker}${abs(overall_wallet['Returns'])} ({ticker}{abs(overall_wallet['Returns (%)'])}%)\nPrincipal: ${overall_wallet['Principal']}\n")

    print ('-' * 16, '$ In/Out & Fees', '-' * 16, sep='\n')
    print (f"Current Fiat Holdings: ${overall_wallet['Fiat']}\nCard Purchase: ${overall_wallet['Card Purchase']}\nFiat Deposit: ${overall_wallet['Deposit']}\nWithdrawals: ${overall_wallet['Withdrawal']}\nReferrals Earned: ${overall_wallet['Referral']}\nFees Paid: ${overall_wallet['Fees']}")
    
    print ("\nCurrent crypto holdings:")
    for k, v in current_crypto.items():
        print (k, v)
    
    # Future implementations:
    # 1) Token breakdown
    #   - Purchased # (Holdings)
    #   - Cost basis ($/share and Total $) [weighted average]
    #     ==> Calculated using the First In, First Out method, just tracking the fiat deposit/conversions along the way for ease
    #   - Current price ($/share and Total $)
    # 2) Portfolio allocations (%)

    # Calculate cost basis of each crypto held
    for crypto, holdings in current_crypto.items():
        # Get list of trades involving current crypto token
        trades = df_trade[df_trade['Pair'].str.contains (crypto, regex=False)]
        # Get CoingeckoID of token
        cgid = cg_api.get_token_cgid(crypto, holdings['Name'])
        
        pass

def update_token_mappings():
    mappings = {}
    ch_api.update_prices()
    ch_tokens = ch_api.prices
    for token, value in ch_tokens.items():
        token_cgid = cg_api.get_token_cgid(token, value['name'])
        mappings[token] = token_cgid
    return mappings

# ** Program entrypoint **
list_dir = os.listdir(file_dir)
list_dir.remove('.gitignore')

# ** Process trade and wallet files generated from Coinhako **
# Get exported trade & wallet files
for f in list_dir:
    if (re.match(regex_trade, f)):
        file_trade = f
    elif (re.match(regex_wallet,f)):
        file_wallet = f

# Clean trade history
df_trade = pd.read_csv("%s/%s" % (file_dir,file_trade))
df_trade = df_trade[df_trade['Status']=='Completed'] # Only get completed trades. Possible values include: Completed, Cancelled, Pending, Waiting for refund, Refunded
df_trade.drop(columns=['Type', 'Average Price', 'Executed', 'Status'], inplace=True)
# df_trade['Time & Date'] = pd.to_datetime (df_trade['Time & Date'], format="%d/%m/%Y %H:%M")
df_trade.sort_values(by="Time & Date", inplace=True)

# Clean wallet history
df_wallet = pd.read_csv("%s/%s" % (file_dir,file_wallet))
df_wallet = df_wallet[df_wallet['Status (All)']=='Completed'] # Only get completed transactions
df_wallet.drop(columns=['Transaction Hash', 'To Address', 'Received by Address', 'Note', 'Status (All)'], inplace=True)
df_wallet.sort_values(by="Date & Time (*-*)", inplace=True)

# Convert dataframes to json
js_trade = json.loads(df_trade.to_json(orient='records'))
js_wallet = json.loads(df_wallet.to_json(orient='records'))

# Update Coinhako-Coingecko token ID mappings
ch_cgid_mappings = update_token_mappings()

# Iterate through wallet transactions
for item in js_wallet:
    # Transaction types: 
    # Receive, Send, Fiat Deposit, Fiat Withdrawal, Sign up credit, Referral Reward, Referral Commission, 
    # Reward Redemption, Recovery fee, Withdrawal Correction Debit, Withdrawal Correction Credit, Deposit Correction Debit, 
    # Deposit Correction Credit, Currency Conversion Credit, Currency Conversion Debit, Withdrawal, Deposit, Redeem Code, 
    # Earn, Redemption, OTC Debit, OTC Credit, Coinhako Bonus Credit, Coinhako Bonus Debit, Internal Transfer Credit, 
    # Internal Transfer Debit, Company Purchase Credit, Company Purchase Debit, Account Merger Credit, Account Merger Debit, Refund
    # 
    # Supported transaction types: 
    #   Fiat:     Fiat Deposit, Fiat Withdrawal, Referral Commission
    #   Token:    Send, Receive, Referral Commission, Earn, Redemption, Reward Redemption, Coinhako Bonus Credit

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
            overall_crypto[item['Currency(All)']] = baseline_crypto.copy()
            if (item['Type (All)']=='Earn'): # Check if any crypto is being staked
                overall_crypto[item['Currency(All)']]['Staked'] = item['Amount']
            elif (item['Type (All)']=='Referral Commission'): # Check if any crypto is obtained through referral commissions
                overall_crypto[item['Currency(All)']]['Referral'] = item['Amount']
            elif (item['Type (All)']=='Receive'): # Check for any crypto received (wallet transfer)
                overall_crypto[item['Currency(All)']]['Receive'] = item['Amount']
            elif (item['Type (All)']=='Reward Redemption') or (item['Type (All)']=='Coinhako Bonus Credit'): # Track free crypto gained through Coinhako rewards
                overall_crypto[item['Currency(All)']]['Reward'] = item['Amount']
        else:
            if (item['Type (All)']=='Earn'): # Check if any crypto is being staked
                overall_crypto[item['Currency(All)']]['Staked'] += item['Amount']
            elif (item['Type (All)']=='Redemption'): # Check if any crypto staked has been yielded
                overall_crypto[item['Currency(All)']]['Redeemed'] += item['Amount']
            elif (item['Type (All)']=='Referral Commission'): # Check if any crypto is obtained through referral commissions
                overall_crypto[item['Currency(All)']]['Referral'] += item['Amount']
            elif (item['Type (All)']=='Receive'): # Check for any crypto received (wallet transfer)
                overall_crypto[item['Currency(All)']]['Receive'] += item['Amount']
            elif (item['Type (All)']=='Send'): # Check for any crypto sent (wallet transfer)
                overall_crypto[item['Currency(All)']]['Send'] += item['Amount']
                # Get fees for transfer of tokens
                overall_crypto[item['Currency(All)']]['Fees'] += item['Fee']
            elif (item['Type (All)']=='Reward Redemption') or (item['Type (All)']=='Coinhako Bonus Credit'): # Track free crypto gained through Coinhako rewards
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
            overall_crypto[token] = baseline_crypto.copy()
            overall_crypto[token]['Bought'] = item['Total']
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
        if (token_to not in overall_crypto.keys()):
            overall_crypto[token_to] = baseline_crypto.copy()
            overall_crypto[token_to]['Bought'] = item['Total']
        else:
            overall_crypto[token_to]['Bought'] += item['Total']
        overall_crypto[token_from]['Sold'] += item['Amount']
        # Get fees for token swap (Note: Fees are paid in the new token's currency, not the previous token's currency. Fees are not converted to fiat)
        overall_crypto[token_to]['Fees'] += item['Fee']

# Calculate overall crypto holdings
for token, holdings in overall_crypto.items():
    # Calculate staked earnings
    overall_crypto[token]['Earned'] = (holdings['Redeemed'] - holdings['Staked']) if (holdings['Redeemed'] > holdings['Staked']) else holdings['Earned']
    holdings['Earned'] = overall_crypto[token]['Earned']

    # Calculate overall holdings (overall value is rounded to a specified amount of precision to 'quantitively determine' that the user holds a particular token. This is done due to precision inconsistencies within Coinhako's exported files)
    overall = round((holdings['Bought'] + holdings['Reward'] + holdings['Earned'] + holdings['Receive'] - holdings['Sold'] - holdings['Send']), min_precision)
    overall_crypto[token]['Overall'] = overall

    # Determine current and past token holdings
    if (overall > 0):
        current_crypto[token] = overall_crypto[token]
    else:
        past_crypto[token] = overall_crypto[token]

# Calculate current fiat wallet holdings
overall_wallet['Fiat'] -= overall_wallet['Withdrawal']
# Requires fixing
if (overall_wallet['Fiat'] < 0): # Check for any card purchases (negative wallet balance indicate purchase through card, such purchases are not tracked/indicated in exported Coinhako files)
    overall_wallet['Card Purchase'] = abs(overall_wallet['Fiat'])
    overall_wallet['Fees'] += overall_wallet['Card Purchase'] * card_percentage_fee
    overall_wallet['Fiat'] = 0

# Calculate current crypto holdings' valuation
ch_api.update_prices() # Get current market prices
for token in current_crypto.keys():
    current_token_value = ch_api.get_price(token)

    current_crypto[token]['Name'] = current_token_value['name']

    current_crypto[token]['Price'] = float(current_token_value['sell_price'])
    current_crypto[token]['Current Value'] = round(current_crypto[token]['Price'] * current_crypto[token]['Overall'], 2)
    overall_wallet['Portfolio'] = round(overall_wallet['Portfolio'] + current_crypto[token]['Current Value'], 2)

# Calculate overall investments (fiat)
overall_wallet['Money In'] = round ((overall_wallet['Deposit'] + overall_wallet['Card Purchase'] + overall_wallet['Referral']), 2)
overall_wallet['Principal'] = round ((overall_wallet['Money In'] - overall_wallet['Withdrawal'] - overall_wallet['Fiat']), 2) # Principal amount is the 'break-even' value (current fiat holdings is not counted in the principal amount as it is considered 'untouched')
overall_wallet['Returns'] = round(overall_wallet['Portfolio'] - overall_wallet['Principal'], 2)
overall_wallet['Returns (%)'] = round(100 * (overall_wallet['Returns'] / overall_wallet['Principal']), 2)

# to be removed
if (overall_wallet['Returns'] > 0):
    overall_wallet['Returns Ticker'] = 1
elif (overall_wallet['Returns'] < 0):
    overall_wallet['Returns Ticker'] = -1

# Clean up
for k, v in overall_wallet.items():
    overall_wallet[k] = round (overall_wallet[k], 2)


# Output
summarise()