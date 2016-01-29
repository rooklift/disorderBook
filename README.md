# disorderBook
An implementation of a **[Stockfighter](http://stockfighter.io)** server in Python 3<br>
Written by Stockfighter user Amtiskaw (a.k.a. Fohristiwhirl on GitHub)

## Usage

* Run `python3 disorderBook_main.py`
* Connect your trading bots to &nbsp; **http://127.0.0.1:8000/ob/api/** &nbsp; instead of the normal URL
* Don't use https

## WebSockets

Thanks to the [SimpleWebSocketServer](https://github.com/dpallot/simple-websocket-server) library (included in the repo), we now have WebSockets. They cause a bit of a performance hit and are disabled by default; enable with the `--websockets` command line option. Connect in via &nbsp; **ws://127.0.0.1:8001/ob/api/ws/** &nbsp; and note we use ws, not wss.

## Authentication

There is no authentication by default. If you want authentication, edit `accounts.json` to contain a list of valid users and their API keys and use the command line option `-a accounts.json` (then authentication will work in [the same way](https://starfighter.readme.io/docs/api-authentication-authorization) as on the official servers, via "X-Starfighter-Authorization" headers).

## Other features

* Your bots can use whatever accounts, venues, and symbols they like
* New exchanges/stocks are created as needed when someone tries to do something on them
* Two stupid bots are included - you must start them (or many copies) manually
* Scores can be accessed at &nbsp; **/ob/api/venues/&lt;venue&gt;/stocks/&lt;symbol&gt;/scores** &nbsp; (accessing this with your bots is cheating though)

## Issues

* Everything persists forever; we will *eventually* run out of RAM

## Non-features

* disorderBook does not serve traffic directly, except to clients on the same host
* disorderBook does not speak TLS

If you want either of these features, put it behind a reverse proxy like NGINX.

## Thanks

* patio11
* cite-reader
* Medecau
* DanielVF
* eu90h
* rjsamson
* rami

## C+Go version

A version made with C and Go [now exists](https://github.com/fohristiwhirl/disorderCook), it's faster.
