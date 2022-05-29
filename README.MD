# Coin Track - Personal Cryptocurrency portfolio
Better understand your personal cryptocurrency portfolio and transactions made on **Coinhako**!

## 👀 Portfolio Analysis / Features
- Principal value of portfolio (valuation for user to break even)
- Crypto portfolio
    - Overall valuation
    - Performance against principal value
- Fiat wallet analysis
    - Current wallet holdings
    - Cash injected and breakdown of means of injection
    - Cash withdrawn to user's bank account
    - Cash transferred out to external crypto wallets
    - Referral commissions earned
    - Fees paid
- Token analysis
    - Current token holdings
    - Transactions breakdown
    - Portfolio allocations
    - Cost basis (minimum price per unit token for user to break even)

## 🚀 Start here! 
1. Download a copy of this Git repository!
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

### Notes
1. Cost basis for each token is calculated by tracking the movement of fiat deposits/conversions along each transaction. The cost basis is calculated by dividing the total money the user injected into a token over the total token holdings.
2. The cost basis calculations for each token will include crypto holdings received from wallet transfers. However, the fiat value (or money injected) for such tokens will not be included into the principal value. This is due to the lack of information on how much these tokens were purchased for from their previous wallet/exchanges.
    - For example if $10 worth of $ETH was purchased from an exchange and transferred to a user, this extra $10 will not be included in the calculation of the user's principal value. However, the $ETH transferred will be included in the calculations for $ETH's cost basis.
3. The principal value calculated will not include past crypto holdings that have been transferred out to other wallets.
    - For example if $20 worth of $BTC was transferred out to the user's external wallet, this $20 will be excluded during the calculation of the user's principal value.

### Warnings & Advisory / Known Issues
1. This program utilises the Coinhako and Coingecko APIs. Limitations of each API will naturally result in limited functionalities, where appropriate.
2. This program may not be able to accurately determine your current crypto holdings. The overall value of each token is rounded to a specified amount of precision to quantitively determine if you hold a particular token. This is necessary due to the precision inconsistencies of Coinhako's exported files. As result, very small token holdings may be missed.
3. This program may not be able to provide an accurate representation of your current fiat holdings and purchases made via card. This is due to the lack of proper representations within Coinhako's exported files.
4. The cost basis calculated for each token represents the **average cost per unit token**. It basically means the minimum amount the token should be valued at, for the user to break even. If the cost basis is zero, this means that the user has already broken even and can sell the token for a profit! There are a few things to note regarding tokens' cost basis:
    - Coinhako charges a fee for every transaction made. This fee is not taken into consideration during the calculation of a token's cost basis. As a result, the cost basis reflected *may be higher* than the true cost basis of a token, depending on the amount of fees paid.
    - Free crypto obtained through staking yields, rewards and referral commissions are included in the calculation of a token's cost basis. As a result, the cost basis reflected *may be lower* than the true cost basis of a token, depending on how much free crypto was obtained.
    - Taking into account of these factors, the cost basis of a token may not be 100% accurate. However, the margin of error should be fairly negligble.
5. Due to the reasons mentioned in (4), the sum of the calculated amount of money that a user injects into each token that they are holding may not be the same as the derived principal value. In this case, users should adopt a maximalist approach and take the higher value as their principal amount to ensure that their holdings break-even/profit!
    