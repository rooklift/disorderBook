# disorderBook
An implementation of a **[Stockfighter](http://stockfighter.io)** server in Python 3<br>
Written by Stockfighter user Amtiskaw (a.k.a. Fohristiwhirl on GitHub)

With the help of Medecau, a version of this now uses the [Bottle](http://bottlepy.org/) library for request handling. It can likely be installed using "pip install bottle".

**disorderBook Usage:**

* Run either *disorderBook_simple.py* or *disorderBook_bottle.py*
* Connect your trading bots to &nbsp; **http://127.0.0.1:8000/ob/api/** &nbsp; instead of the normal URL
* Don't use https

**Features:**

* Your bots can use whatever accounts, venues, and symbols they like
* New exchanges/stocks are created as needed when someone tries to do something on them
* Two stupid bots are included - you must start them (or many copies) manually

**Issues:**

* No websockets
* No authentication, anyone can cancel or see any order
* Everything persists forever; we will eventually run out of RAM or the CPU will get bogged down

**Other important differences:**

* Currently, order IDs are unique per venue+stock, not per venue (e.g. on venue SELLEX, the stock CATS can have an order with an ID of 42 at the same time as stock DOGS also has an order with ID of 42)

**Chances of these issues being fixed:**

* Unknown, making this hurt my brain

**Notes:**

* There are 2 parts, the orderbook, and the request handler
* The orderbook, if I say so myself, is relatively sane in its design
* The request handler is stupidly done, but fairly simple
