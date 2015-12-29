# disorderBook
A probably-too-slow implementation of **[Stockfighter](http://stockfighter.io)** in Python 3

**Usage:**

* Run *disorderBook_main.py* &nbsp; (also requires *disorderBook_book.py* to be present)
* Connect your trading bots to &nbsp; **http://127.0.0.1:8000/ob/api/** &nbsp; instead of the normal URL
* Don't use https

**Features:**

* Your bots can use whatever accounts, venues, and symbols they like
* New exchanges/stocks are created as needed when someone tries to do something on them
* One noise-bot (i.e. randomish trades) is included - you must start it (or many copies) manually

**Issues:**

* No websockets
* No authentication, anyone can cancel or see any order
* Everything persists forever; we will eventually run out of memory

**Chances of these issues being fixed:**

* Unknown, making this hurt my brain

**Notes:**

* There are 2 parts, the orderbook, and the request handler
* The orderbook, if I say so myself, is relatively sane in its design
* The request handler is stupidly done, but easy to read
