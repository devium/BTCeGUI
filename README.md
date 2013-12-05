BTCeGUI
=======

*Disclaimer: This project is relatively young and not extensively tested yet. Use at your own risk!*

A Python GUI tool for real-time market information and trading on BTC-e.com.

!(/screenshot.png)

Installation
------------
1. Install Python 3 from http://www.python.org/

Optional:
1. Get an API key and secret from https://btc-e.com/profile#api_keys and configure its permissions.
2. Copy both the key and the secret to the *BTCe.ini* file (ignore the nonce parameter).
3. Make sure this .ini file is stored safely, as it will enable anyone with its information to request your account's information or place orders in your name **even without knowing your password or account name**.

Run
---
1. Run BTCeGUI.py.

Features
--------
Shortly after the program starts it will request a list of available currency pairs from BTC-e. You can then choose a currency pair from the Combobox in the upper left corner.

The program will then update the current market depth data as often as possible for the currently selected currency pair.

If no API key/secret pair is available or a present key/secret pair does not have info or trade permissions you will only be able to access public data:
* Available currency pairs.
* Market depth (bid/ask orders) for the current currency pair.
* Off-line calculation of prices and fees for buy and sell orders.
* Double-clicking any ask or bid offer will copy its rate to the respective order frame.

An API key with *Info* permission will furthermore make the following data available to you:
* Your current funds deposited on BTC-e for all currencies.
* Your open orders.
* Checking *All* will fix the *Amount* and *Value* fields to your current possible maximum.

Finally, an API key with *Trade* permission enables the following:
* Place buy and sell orders.
* Cancel open orders.

*Warning: Again, anyone knowing your API key/secret pair has the same permissions as you and can request personal information and place orders in your name without even knowing your user name or password.*

Contact Information
-------------------
If you have any suggestions or want to thank or insult me, please do so on https://github.com/Oppium/BTCeGUI.
I would also be very thankful to any kind-hearted humans that may wish to donate:
LTC: LbTCeK1EPwdYGs5drKW38LxmV35ou9k8kR
BTC: 1BTCeYSbLegRz8WNEqcTiF2irryKBBa3LF