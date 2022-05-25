# Coin Track - Personal Cryptocurrency portfolio
Better understand your personal cryptocurrency portfolio and transactions made on **Coinhako**!

## 🚀 Start here! 
1. Save a copy of this Git repository!
2. Download a copy of your trading and wallet history from Coinhako. Save the two files under the *history* folder (ensure that there is only one wallet and one trade file in this folder at any moment!)
    - [Trade History](https://www.coinhako.com/wallet/history/trade)
    - [Wallet History](https://www.coinhako.com/wallet/history/wallet)
3. Install all the required dependencies for this project.
    ```python
    pip install -r requirements.txt
    ```
4. Run **analyse.py** and view your portfolio!
    ```python 
    python3 analyse.py
    ```

### Features to implement:
- Cost per token
- Improve date functions
- Compare prices from various exchanges

#### Warnings & Advisory / Known Issues
1. This program utilises the Coinhako and Coingecko APIs. Limitations of each API will naturally result in limited functionality for particular tokens (ie token not supported in either platform).
2. This program may not be able to accurately determine your current crypto holdings. The overall value of each token is rounded to a specified amount of precision to quantitively determine if you hold a particular token. As such, very small token holdings may be missed. The rounding of each token is necessary due to precision inconsistencies within Coinhako's exported files.
3. This program may not be able to provide an accurate representation of your current fiat holdings and purchases made via card. This is due to the lack of proper representations within Coinhako's exported files.