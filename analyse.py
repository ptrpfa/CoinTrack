from config import *
from api import CoinhakoAPI, CoingeckoAPI
import os, re, json
import pandas as pd

# ** Variables **
overall_wallet = {  
                    'Deposit': 0,       # Total fiat deposited
                    'Card Purchase': 0, # Total fiat paid via card purchases
                    'Withdrawal': 0,    # Total fiat withdrawn
                    'Transfer Out': 0,  # Total fiat transferred out via crypto transfers to other wallet
                    'Referral': 0,      # Fiat obtained from referral commissions
                    'Fees': 0,          # Total fees paid
                    'Fiat': 0,          # Current fiat holdings
                    'Principal': 0,     # Principal (break-even) amount
                    'Portfolio': 0,     # Current portfolio fiat value
                    'Returns': 0        # Current portfolio returns
                }
overall_crypto = {}
baseline_crypto = { 
                    'Bought': 0,            # Total crypto bought 
                    'Sold': 0,              # Total crypto sold
                    'Send': 0,              # Total crypto sent to wallet
                    'Receive': 0,           # Total crypto received from wallet transfer 
                    'Staked': 0,            # Total crypto staked
                    'Redeemed': 0,          # Total crypto redeemed from staking
                    'Earned': 0,            # Total crypto successfully yielded after staking
                    'Reward': 0,            # Total crypto obtained from rewards
                    'Referral': 0,          # Total crypto obtained from referral commissions
                    'Free': 0,              # Total crypto obtained at no cost (rewards, referral commissions, staking yields)
                    'Fees': 0,              # Total fees paid. Fees are not further broken down into the sub-categories of Transfer Fees / Swap Fees
                    'Overall': 0,           # Total crypto that user is currently holding on
                    'Money In': 0,          # For cost basis calculations: Total money (fiat) used to purchase token
                    'Money Out': 0,         # For cost basis calculations: Temporary storage to track movement of money out (sell/swap transactions)
                    'Current': 0,           # For cost basis calculations: Temporary storage to track the amount of tokens at any one time
                    'Average Cost': 0,      # For cost basis calculations: Average cost per token ($/token)
                    'Name': None,           # Token name
                    'Price': None,          # Current token price (either from Coinhako / Coingecko API)
                    'Current Value': None,  # Current value of token holdings (if any)
                    'cgid': None,           # Coingecko ID of token
                }
current_crypto = {} # Dictionary holding references to crypto tokens that the user current owns (changes made will propagate to overall_crypto and vice versa)
past_crypto = {}    # Dictionary holding references to crypto tokens that the user owned previously (changes made will propagate to overall_crypto and vice versa)
total_money_in = 0  # Track total money injected by user per token (for calculating portfolio allocations)

# ** APIs **
ch_api = CoinhakoAPI()
cg_api = CoingeckoAPI()
# Coinhako token mappings to their equivalent Coingecko IDs (to be stored in a database). Note: $LUNA (Terra Luna Classic) has been delisted from Coinhako wef 27/05/2022, token is still reflected as $LUNA, not $LUNC.
ch_cgid_mappings = {'1INCH': '1inch', 'AAVE': 'aave', 'ADA': 'cardano', 'ATOM': 'cosmos', 'AVAX': 'avalanche-2', 
                    'AXS': 'axie-infinity', 'BAND': 'band-protocol', 'BAT': 'basic-attention-token', 'BCH': 'bitcoin-cash', 
                    'BNB': 'binancecoin', 'BTC': 'bitcoin', 'BTTC': 'bittorrent', 'CEL': 'celsius-degree-token', 'CHZ': 'chiliz', 
                    'CLV': 'clover-finance', 'COMP': 'compound-governance-token', 'CRV': 'curve-dao-token', 'DAI': 'dai', 
                    'DOGE': 'dogecoin', 'DOT': 'polkadot', 'DYDX': 'dydx', 'EGLD': 'elrond-erd-2', 'ENJ': 'enjincoin', 
                    'ENS': 'ethereum-name-service', 'ETH': 'ethereum', 'FIL': 'filecoin', 'FLOW': 'flow', 'FTM': 'fantom', 
                    'FTT': 'ftx-token', 'GALA': 'gala', 'GRT': 'the-graph', 'HBAR': 'hedera-hashgraph', 'ICP': 'internet-computer', 
                    'IMX': 'immutable-x', 'IOTA': 'iota', 'KLAY': 'klay-token', 'KSM': 'kusama', 'LINK': 'chainlink', 'LRC': 'loopring', 
                    'LTC': 'litecoin', 'MANA': 'decentraland', 'MATIC': 'matic-network', 'MKR': 'maker', 'NEAR': 'near', 'NEO': 'neo', 
                    'OMG': 'omisego', 'RUNE': 'rune', 'SAND': 'the-sandbox', 'SC': 'siacoin', 'SHIB': 'shiba-inu', 'SNX': 'havven', 
                    'SOL': 'solana', 'SRM': 'serum', 'THETA': 'theta-token', 'UNI': 'uniswap', 'USDC': 'usd-coin', 'USDT': 'tether', 
                    'VET': 'vechain', 'XLM': 'stellar', 'XMR': 'monero', 'XNO': 'nano', 'XRP': 'ripple', 'XTZ': 'tezos', 
                    'YFI': 'yearn-finance', 'ZEC': 'zcash', 'ZIL': 'zilliqa', 'LUNA': 'terra-luna'}

# ** Functions **
def calculate_token_balance(token_holdings, include_send = False): # Calculate overall token holdings
    incoming  = token_holdings['Bought'] +  token_holdings['Earned'] + token_holdings['Reward'] + token_holdings['Referral'] + token_holdings['Receive']
    outgoing = token_holdings['Sold'] if not include_send else (token_holdings['Sold'] + token_holdings['Send']) # By default, don't include token that were sent out
    overall = incoming - outgoing
    return overall

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

# Iterate through wallet transactions
for item in js_wallet:
    # Coinhako transaction types: 
    #   Fiat: Fiat Deposit, Fiat Withdrawal, Referral Commission
    #   Token: Send, Receive, Referral Commission, Earn, Redemption, Reward Redemption, Coinhako Bonus Credit
    #   Misc: Sign up credit, Referral Reward, , Recovery fee, Withdrawal Correction Debit, Withdrawal Correction Credit, 
    #         Deposit Correction Debit, Deposit Correction Credit, Currency Conversion Credit, Currency Conversion Debit, Withdrawal, Deposit, 
    #         Redeem Code, OTC Debit, OTC Credit, Coinhako Bonus Debit, Internal Transfer Credit, Internal Transfer Debit, Company Purchase Credit, 
    #         Company Purchase Debit, Account Merger Credit, Account Merger Debit, Refund
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
        # Check for new tokens
        if (item['Currency(All)'] not in overall_crypto.keys()):
            overall_crypto[item['Currency(All)']] = baseline_crypto.copy()
            if (item['Type (All)']=='Earn'): # Check if any crypto is being staked
                overall_crypto[item['Currency(All)']]['Staked'] = item['Amount']
            elif (item['Type (All)']=='Referral Commission'): # Check if any crypto is obtained through referral commissions
                overall_crypto[item['Currency(All)']]['Referral'] = item['Amount']
            elif (item['Type (All)']=='Receive'): # Check for any crypto received (wallet transfer)
                overall_crypto[item['Currency(All)']]['Receive'] = item['Amount']
                # to implement fees for transfer of tokens (if any)
            elif (item['Type (All)']=='Send'): # Check for any crypto sent (wallet transfer)
                overall_crypto[item['Currency(All)']]['Send'] = item['Amount']
                # Get fees for transfer of tokens
                overall_crypto[item['Currency(All)']]['Fees'] = item['Fee']
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
                # to implement fees for transfer of tokens (if any)
            elif (item['Type (All)']=='Send'): # Check for any crypto sent (wallet transfer)
                overall_crypto[item['Currency(All)']]['Send'] += item['Amount']
                # Get fees for transfer of tokens
                overall_crypto[item['Currency(All)']]['Fees'] += item['Fee']
            elif (item['Type (All)']=='Reward Redemption') or (item['Type (All)']=='Coinhako Bonus Credit'): # Track free crypto gained through Coinhako rewards
                overall_crypto[item['Currency(All)']]['Reward'] += item['Amount']

# Calculate preliminary fiat wallet holdings (total incoming fiat)
overall_wallet['Fiat'] = overall_wallet['Deposit'] + overall_wallet['Referral']

# Calculate staking yields and crypto obtained for free
for token, holdings in overall_crypto.items():
    # Calculate staked earnings
    holdings['Earned'] = (holdings['Redeemed'] - holdings['Staked']) if (holdings['Redeemed'] > holdings['Staked']) else holdings['Earned']
    overall_crypto[token]['Earned'] = holdings['Earned']
    # Crypto obtained for free includes: staked earnings, referral commissions, rewards
    overall_crypto[token]['Free'] = holdings['Earned'] + holdings['Referral'] + holdings['Reward']

# Iterate through trade transactions
for item in js_trade:
    if (item['Side']=='Buy'):
        token = re.match(regex_token, item['Pair']).group(1)
        overall_wallet['Fees'] += float(item['Fee'])
        transaction_percentage_fee = item['Fee'] / item['Amount']
        # Check if transaction was made via card or fiat holdings
        if (transaction_percentage_fee > card_percentage_fee): 
            overall_wallet['Card Purchase'] = item['Amount'] # Card purchases are do not result in changes in the user's current fiat holdings (direct deduction through card)
        else:
            overall_wallet['Fiat'] -= item['Amount']
        # Check for new tokens
        if (token not in overall_crypto.keys()):
            overall_crypto[token] = baseline_crypto.copy()
            overall_crypto[token]['Bought'] = item['Total']
        else:
             overall_crypto[token]['Bought'] += item['Total']
        # Cost basis calculations
        overall_crypto[token]['Money In'] += item['Amount']
        overall_crypto[token]['Current'] = calculate_token_balance(overall_crypto[token])
        if (overall_crypto[token]['Money In'] > 0 and overall_crypto[token]['Current'] > 0):
            overall_crypto[token]['Average Cost'] = overall_crypto[token]['Money In'] / overall_crypto[token]['Current']
        else:
            overall_crypto[token]['Average Cost'] = 0
    elif (item['Side']=='Sell'):
        token = re.match(regex_token, item['Pair']).group(1)
        overall_wallet['Fees'] += float(item['Fee'])
        overall_wallet['Fiat'] += item['Total']
        overall_crypto[token]['Sold'] += item['Amount']
        # Cost basis calculations
        overall_crypto[token]['Current'] = calculate_token_balance(overall_crypto[token])
        overall_crypto[token]['Money Out'] = item['Total'] # Money out doesn't account for fees paid, so break-even price will always be slightly higher!
        if (overall_crypto[token]['Money In'] > 0): 
            if (overall_crypto[token]['Money In'] > item['Total'] and overall_crypto[token]['Current'] > 0): 
                overall_crypto[token]['Money In'] -= item['Total']
                overall_crypto[token]['Average Cost'] = overall_crypto[token]['Money In'] / overall_crypto[token]['Current']
            else: # If the amount sold is more than the money in, it means the token is being sold for a profit/broke even
                overall_crypto[token]['Money In'] = 0
                overall_crypto[token]['Average Cost'] = 0
        else: # If the total money in is 0 (broke-even), don't do anything
            overall_crypto[token]['Money In']= 0
            overall_crypto[token]['Average Cost'] = 0
    elif (item['Side']=='Swap'):
        # Format: FROM/TO ie BTC/DOGE (BTC to DOGE) or DOGE/BTC (DOGE to BTC)
        token_from = re.match(regex_swap, item['Pair']).group(1)
        token_to = re.match(regex_swap, item['Pair']).group(2)
        # Check for new tokens
        if (token_to not in overall_crypto.keys()):
            overall_crypto[token_to] = baseline_crypto.copy()
            overall_crypto[token_to]['Bought'] = item['Total']
        else:
            overall_crypto[token_to]['Bought'] += item['Total']
        overall_crypto[token_from]['Sold'] += item['Amount']
        # Get fees for token swap (Note: Fees are paid in the new token's currency, not the previous token's currency. Fees are not converted to fiat)
        overall_crypto[token_to]['Fees'] += item['Fee']
        # Cost basis calculations
        # old token calculations
        overall_crypto[token_from]['Current'] = calculate_token_balance(overall_crypto[token_from])
        if (overall_crypto[token_from]['Money In'] > 0): # Check if there is money injected into the token by the user
            overall_crypto[token_from]['Money Out'] = item['Amount'] * overall_crypto[token_from]['Average Cost'] # Calculate movement of money out of old token
            if (overall_crypto[token_from]['Money In'] > overall_crypto[token_from]['Money Out'] and overall_crypto[token_from]['Current'] > 0): 
                overall_crypto[token_from]['Money In'] -= overall_crypto[token_from]['Money Out']
                overall_crypto[token_from]['Average Cost'] = overall_crypto[token_from]['Money In'] / overall_crypto[token_from]['Current']
            else: # If money out is more than money in, this means the token is being sold for a profit/broke even
                overall_crypto[token_from]['Money In'] = 0
                overall_crypto[token_from]['Average Cost'] = 0
        else: # Break even / Profits
            overall_crypto[token_from]['Money Out'] = 0
            overall_crypto[token_from]['Money In'] = 0
            overall_crypto[token_from]['Average Cost'] = 0
        # new token calculations
        overall_crypto[token_to]['Current'] = calculate_token_balance(overall_crypto[token_to])
        if (overall_crypto[token_from]['Money Out'] > 0 and overall_crypto[token_to]['Current'] > 0): # Check if there are money movement
            overall_crypto[token_to]['Money In'] += overall_crypto[token_from]['Money Out']
            overall_crypto[token_to]['Average Cost'] = overall_crypto[token_to]['Money In'] / overall_crypto[token_to]['Current']

ch_api.update_prices() # Get current market prices from Coinhako
# Calculate overall crypto holdings
for token, holdings in overall_crypto.items():
    # Overall value is rounded to a specified amount of precision to 'quantitively determine' that the user holds a particular token. This is done due to precision inconsistencies within Coinhako's exported files
    overall = round(calculate_token_balance(holdings), min_precision)
    overall_crypto[token]['Overall'] = overall
    # Clean up cost basis
    overall_crypto[token]['Money Out'] = 0 # reset
    overall_crypto[token]['Current'] = overall
    overall_crypto[token]['Money In'] = round(overall_crypto[token]['Money In'], 2)
    if (overall_crypto[token]['Money In'] > 0 and overall > 0):
        overall_crypto[token]['Average Cost'] = round(overall_crypto[token]['Money In'] / overall, min_precision)
    else:
        overall_crypto[token]['Average Cost'] = 0
    # Separate current and past token holdings into two dicts
    if (overall > 0):
        if (overall_crypto[token]['Send'] > 0): # Check if any crypto was transferred out
            if (overall_crypto[token]['Average Cost'] > 0): # get fiat value being transferred away
                overall_wallet['Transfer Out'] += overall_crypto[token]['Send'] * overall_crypto[token]['Average Cost']
            overall = round(calculate_token_balance(holdings, True), min_precision) # re-calculate current token holdings
            overall_crypto[token]['Overall'] = overall
            overall_crypto[token]['Current'] = overall
            if (overall_crypto[token]['Money In'] > 0 and overall > 0): # re-calculate cost basis
                overall_crypto[token]['Average Cost'] = round(overall_crypto[token]['Money In'] / overall, min_precision)
            else:
                overall_crypto[token]['Average Cost'] = 0
            if (overall > 0):  # check remaining amount of crypto after transfers
                current_crypto[token] = overall_crypto[token]
                total_money_in += current_crypto[token]['Money In']
            else:
                past_crypto[token] = overall_crypto[token]
        else:
            current_crypto[token] = overall_crypto[token]
            total_money_in += current_crypto[token]['Money In']
    else:
        past_crypto[token] = overall_crypto[token]
    # Get token metadata
    current_token = ch_api.get_price(token) # get token details from Coinhako API
    if (current_token != None): # Check if token is supported in Coinhako
        overall_crypto[token]['Name'] = current_token['name']
        overall_crypto[token]['Price'] = float(current_token['sell_price'])
        overall_crypto[token]['Current Value'] = round(overall_crypto[token]['Price'] * overall_crypto[token]['Overall'], 2)
        if (token in ch_cgid_mappings.keys()): # get Coingecko ID
            overall_crypto[token]['cgid'] = ch_cgid_mappings[token]
        else:
            overall_crypto[token]['cgid'] = cg_api.get_token_cgid(token, holdings['Name'])
            if (overall_crypto[token]['cgid'] != None):
                ch_cgid_mappings[token] = overall_crypto[token]['cgid']
    else:
        if (token in ch_cgid_mappings.keys()): # Check if the token's equivalent Coingecko ID can be obtained
            overall_crypto[token]['cgid'] = ch_cgid_mappings[token]
            token_details = cg_api.get_token_details(overall_crypto[token]['cgid'])
            overall_crypto[token]['Name'] = token_details['name']
            overall_crypto[token]['Price'] = float(token_details['price'])
            overall_crypto[token]['Current Value'] = round(overall_crypto[token]['Price'] * overall_crypto[token]['Overall'], 2)

# Calculate user's current portfolio (current crypto holdings' valuation)
for k, v in current_crypto.items():
    # Calculate overall portfolio
    if (v['Current Value'] != None):
        overall_wallet['Portfolio'] = round(overall_wallet['Portfolio'] + v['Current Value'], 2)
    # Calculate portfolio allocation
    if (v['Money In'] > 0):
        overall_crypto[k]['Portfolio Allocation'] = round(100 * (v['Money In'] / total_money_in), 2)

# ** Calculate overall investments **
for k, v in overall_wallet.items(): # Clean up wallet
    overall_wallet[k] = round(overall_wallet[k], 2)
overall_wallet['Fiat'] -= overall_wallet['Withdrawal'] # Get current fiat wallet holdings
incoming_cash = overall_wallet['Deposit'] + overall_wallet['Card Purchase'] + overall_wallet['Referral'] # Get total cash user injected into platform
# Calculate overall investment principal amount ('break-even' value). Users' current fiat holdings are not counted in the principal amount as they are 
# considered 'untouched'. The principal value does not include the fiat value of crypto received via wallet transfer. It also does not include the fiat
# value/capital of tokens that have been sent out to personal wallets.
overall_wallet['Principal'] = incoming_cash - overall_wallet['Withdrawal'] - overall_wallet['Fiat'] - overall_wallet['Transfer Out']
overall_wallet['Returns'] = overall_wallet['Portfolio'] - overall_wallet['Principal'] # Calculate investment returns
for k, v in overall_wallet.items(): # Clean up wallet
    overall_wallet[k] = round(overall_wallet[k], 2)

# ** In-depth analysis **
# for crypto, holdings in overall_crypto.items():
#     # Get list of trades involving current crypto token
#     trades = df_trade[df_trade['Pair'].str.contains(crypto, regex=False)]
#     # to implement error handling when the token metadata are None (name, price, current value, cgid)
#     # Past tokens whose money in value > 0 indicates that they were sold/swapped at a LOSS (value indicates loss incurred)

# ** Report **
print(f"Report generated on: {ch_api.last_update}")
print('-' * 8, 'Summary', '-' * 8, sep='\n')
print(f"Principal Value: ${overall_wallet['Principal']}\nCurrent Portfolio Valuation: ${overall_wallet['Portfolio']}\nPortfolio Performance: {overall_wallet['Returns']} ({round(100 * (overall_wallet['Returns'] / overall_wallet['Principal']), 2)}%)\n")
print('-' * 11, 'Fiat Wallet', '-' * 11, sep='\n')
print(f"Total Cash Injected: ${overall_wallet['Deposit'] + overall_wallet['Card Purchase']}\n  - Fiat Deposit: ${overall_wallet['Deposit']}\n  - Card Purchase: ${overall_wallet['Card Purchase']}\nTotal Cash Out: ${overall_wallet['Withdrawal'] + overall_wallet['Transfer Out']}\n  - Cash Withdrawn: ${overall_wallet['Withdrawal']}\n  - Cash Transferred Out: ${overall_wallet['Transfer Out']}\nCurrent Fiat Holdings: ${overall_wallet['Fiat']}\nReferral Commissions Earned: ${overall_wallet['Referral']}\nFees Paid: ${overall_wallet['Fees']}\n")
if (len(current_crypto.keys()) > 0):
    print('-' * 14, 'Crypto Holdings', '-' * 14, sep='\n')
    for k, v in current_crypto.items():
        print(f"{v['Name']} (${k}):")
        print(f"  Portfolio Allocation: {v['Portfolio Allocation']}%\n  Holdings: {v['Overall']}\n  Total money in: ${v['Money In']}\n  Current value: ${v['Current Value']}\n  Average Cost: ${v['Average Cost']}/{k}\n  Current Price: ${v['Price']}/{k}")