# Minimum precision point for crypto held to be considered non-zero
min_precision = 7

# Constants
file_dir = 'history'
regex_trade = '^trade_history.+\.csv'
regex_wallet = '^wallet_history.+\.csv'
regex_token = '^(.+)\/SGD'
regex_swap = '^(.+)\/(.+)'

# Coinhako
withdrawal_fee = 2 # Fees incurred upon withdrawal from wallet to bank account
api_url = 'https://www.coinhako.com/api/v3/price/all_prices_for_mobile?counter_currency=sgd'