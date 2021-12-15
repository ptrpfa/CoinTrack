import os
import pandas as pd
import re

# Constants
file_dir = 'history'
regex_trade = '^trade_history.+\.csv'
regex_wallet = '^wallet_history.+\.csv'

# To set column names
trade_cols = ['Pair', 'Side', 'Type', 'Average Price', 'Price', 'Amount', 'Executed', 'Fee', 'Total', 'Status', 'Time & Date']

# Entrypoint
list_dir = os.listdir(file_dir)
list_dir.remove('.gitignore')

for f in list_dir:
    if (re.match(regex_trade, f)):
        file_trade = f
    elif (re.match(regex_wallet,f)):
        file_wallet = f

df_trade = pd.read_csv("%s/%s" % (file_dir,file_trade))
df_wallet = pd.read_csv("%s/%s" % (file_dir,file_wallet))

# To drop unusable columns
