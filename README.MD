# Coin Track - Personal Cryptocurrency portfolio
Better understand your personal cryptocurrency portfolio and transactions made on **Coinhako**.

### Features to implement:
- Cost per token

### Potential/future add-ons:
- Get prices from Coinhako API
- Get prices from CoinMarketCap API
- Compare prices from various exchanges

### Known issues:
- Additional fees incurred from transactions made through Credit/Debit Card (VISA) are **not reflected**. Coinhako always charges a base transaction fee of 1%, which is included in the files exported from their website. However, the additional 3% fee incurred for VISA transactions is not included in the exported files, resulting in their omission.

> Documentation

1. Download a copy of your trading and wallet history from Coinhako. Save the 2 files under the *history* folder
    - [Trade History](https://www.coinhako.com/wallet/history/trade)
    - [Wallet History](https://www.coinhako.com/wallet/history/wallet)
2. Create and update **config.py** with the necessary API keys (refer to *sample-config.py*)
3. Run **analyse.py**

