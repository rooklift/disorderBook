# disorderBook
A probably-too-slow implementation of Stockfighter in Python

disorderBook is a Stockfighter implementation.

Usage:

* Run disorderBook_main.py
* Connect your trading bots to http://localhost:8000/ob/api/
* They can use whatever accounts, venues, and symbols they like

Issues:

* No websockets
* No authentication, anyone can cancel or see any order

Chances of these issues being fixed:

* Unknown, making this hurt my brain

Notes:

* There are 2 parts, the orderbook, and the request handler. The orderbook, if I say so myself, is relatively sane in its design. The request handler is a mess. Aside from that, a noise-bot is included for your amusement.