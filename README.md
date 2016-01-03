# disorderBook
An implementation of a **[Stockfighter](http://stockfighter.io)** server in Python 3<br>
Written by Stockfighter user Amtiskaw (a.k.a. Fohristiwhirl on GitHub)

## Requirements

With the help of Medecau, we now use the [Bottle](http://bottlepy.org/) library for request handling; you could install it through `pip install bottle`, but a copy of the library is included in this repo (and will be used if Bottle is not otherwise installed).

You might want to [set up a virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) to do your work in.

## Usage

* Run `python3 disorderBook_main.py` &nbsp; (also requires `disorderBook_book.py` to be present)
* Connect your trading bots to &nbsp; **http://127.0.0.1:8000/ob/api/** &nbsp; instead of the normal URL
* Don't use https

## Authentication

There is no authentication by default. If you want authentication, edit `accounts.json` to contain a list of valid users and their API keys and run `python3 disorderBook_main.py -a accounts.json`.

## Features

* Your bots can use whatever accounts, venues, and symbols they like
* New exchanges/stocks are created as needed when someone tries to do something on them
* Two stupid bots are included - you must start them (or many copies) manually

## Missing features / issues

* No websockets yet, or maybe ever
* Everything persists forever; we will eventually run out of RAM or the CPU will get bogged down

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
