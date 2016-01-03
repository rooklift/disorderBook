# This is a better version of the frontend using the bottle library
# Made by Medecau and Fohristiwhirl

import json, optparse
from bottle import route, request, run
import disorderBook_book as book

all_venues = dict()			# dict: venue string ---> dict: stock string ---> OrderBook objects
current_book_count = 0

auth = dict()

BOOK_ERROR = {"ok": False, "error": "Book limit exceeded! (See command line options)"}
NO_AUTH_ERROR = {"ok": False, "error": "Server is in +authentication mode but no API key was received"}
AUTH_FAILURE = {"ok": False, "error": "Unknown account or wrong API key"}
AUTH_WEIRDFAIL = {"ok": False, "error": "Account of stored data had no associated API key (this is impossible)"}
NO_SUCH_ORDER = {"ok": False, "error": "No such order for that Exchange + Symbol combo"}

# ----------------------------------------------------------------------------------------

class TooManyBooks (Exception):
	pass


class NoApiKey (Exception):
	pass


def response_from_exception(e):
	di = dict()
	di["ok"] = False
	di["error"] = str(e)
	return di


def create_book_if_needed(venue, symbol):
	global current_book_count
	
	if venue not in all_venues:
		if opts.maxbooks > 0:
			if current_book_count + 1 > opts.maxbooks:
				raise TooManyBooks
		all_venues[venue] = dict()

	if symbol not in all_venues[venue]:
		if opts.maxbooks > 0:
			if current_book_count + 1 > opts.maxbooks:
				raise TooManyBooks
		all_venues[venue][symbol] = book.OrderBook(venue, symbol)
		current_book_count += 1


def api_key_from_headers(headers):
	try:
		return headers.get('X-Starfighter-Authorization')
	except:
		try:
			return headers.get('X-Stockfighter-Authorization')
		except:
			raise NoApiKey

	
# ----------------------------------------------------------------------------------------

@route("/ob/api/heartbeat", "GET")
def heartbeat():
	return {"ok": True, "error": ""}


@route("/ob/api/venues", "GET")
def venue_list():
	ret = dict()
	ret["ok"] = True
	ret["venues"] = [{"name": v + " Exchange", "venue": v, "state" : "open"} for v in all_venues]
	return ret


@route("/ob/api/venues/<venue>/heartbeat", "GET")
def venue_heartbeat(venue):
	if venue in all_venues:
		return {"ok": True, "venue": venue}
	else:
		return {"ok": False, "error": "Venue {} does not exist (create it by using it)".format(venue)}


@route("/ob/api/venues/<venue>/stocks", "GET")
def stocklist(venue):
	if venue in all_venues:
		ret = {
				"ok" : True,
				"symbols" : [{"symbol" : symbol, "name" : symbol + " Inc"} for symbol in all_venues[venue]]
			}
	else:
		ret = {
				"ok" : False,
				"error": "Venue {} does not exist (create it by using it)".format(venue)
			}
	return ret

route("/ob/api/venues/<venue>", "GET", stocklist)				# Alternate URL


@route("/ob/api/venues/<venue>/stocks/<symbol>", "GET")
def orderbook(venue, symbol):

	try:
		create_book_if_needed(venue, symbol)
	except TooManyBooks:
		return 

	try:
		ret = all_venues[venue][symbol].get_book()
		assert(ret)
		return ret
	except Exception as e:
		ret = response_from_exception(e)
		return ret


@route("/ob/api/venues/<venue>/stocks/<symbol>/quote", "GET")
def quote(venue, symbol):
	
	try:
		create_book_if_needed(venue, symbol)
	except TooManyBooks:
		return BOOK_ERROR

	try:
		ret = all_venues[venue][symbol].get_quote()
		assert(ret)
		return ret
	except Exception as e:
		ret = response_from_exception(e)
		return ret


@route("/ob/api/venues/<venue>/stocks/<symbol>/orders/<id>", "GET")
def status(venue, symbol, id):
	
	try:
		create_book_if_needed(venue, symbol)
	except TooManyBooks:
		return BOOK_ERROR
	
	try:
		if auth:
			try:
				apikey = api_key_from_headers(request.headers)
			except NoApiKey:
				return NO_AUTH_ERROR
	
		ret = all_venues[venue][symbol].get_status(int(id))
		assert(ret)		# Fails if ID invalid
		
		if auth:
			account = ret["account"]
			if account not in auth:
				return AUTH_WEIRDFAIL
			elif auth[account] != apikey:
				return AUTH_FAILURE
			else:
				return ret

	except Exception as e:
		ret = response_from_exception(e)
		return ret


@route("/ob/api/venues/<venue>/accounts/<account>/orders", "GET")
def status_all_orders(venue, account):
	
	try:
	
		if auth:
			try:
				apikey = api_key_from_headers(request.headers)
			except NoApiKey:
				return NO_AUTH_ERROR

			if account not in auth:
				return AUTH_WEIRDFAIL
			elif auth[account] != apikey:
				return AUTH_FAILURE
		
		orders = []

		if venue in all_venues:
			for bk in all_venues[venue].values():
				orders += bk.get_all_orders(account)["orders"]

		ret = dict()
		ret["ok"] = True
		ret["venue"] = venue
		ret["orders"] = orders
		return ret
	
	except Exception as e:
		ret = response_from_exception(e)
		return ret



@route("/ob/api/venues/<venue>/accounts/<account>/stocks/<symbol>/orders", "GET")
def status_all_orders_one_stock(venue, account, symbol):

	try:
		create_book_if_needed(venue, symbol)
	except TooManyBooks:
		return BOOK_ERROR
	
	try:
	
		if auth:
			try:
				apikey = api_key_from_headers(request.headers)
			except NoApiKey:
				return NO_AUTH_ERROR

			if account not in auth:
				return AUTH_WEIRDFAIL

			if auth[account] != apikey:
				return AUTH_FAILURE

		ret = all_venues[venue][symbol].get_all_orders(account)
		assert(ret)
		return ret

	except Exception as e:
		ret = response_from_exception(e)
		return ret


@route("/ob/api/venues/<venue>/stocks/<symbol>/orders/<id>", "DELETE")
def cancel(venue, symbol, id):

	try:
		create_book_if_needed(venue, symbol)
	except TooManyBooks:
		return BOOK_ERROR
	
	try:
	
		if auth:
			try:
				apikey = api_key_from_headers(request.headers)
			except NoApiKey:
				return NO_AUTH_ERROR
		
			account = all_venues[venue][symbol].account_from_order_id(int(id))
			if not account:
				return NO_SUCH_ORDER
				
			if account not in auth:
				return AUTH_WEIRDFAIL

			if auth[account] != apikey:
				return AUTH_FAILURE

		ret = all_venues[venue][symbol].cancel_order(int(id))
		assert(ret)
		return ret
		
	except Exception as e:
		ret = response_from_exception(e)
		return ret

route("/ob/api/venues/<venue>/stocks/<symbol>/orders/<id>/cancel", "POST", cancel)		# Alternate method and URL


@route("/ob/api/venues/<venue>/stocks/<symbol>/orders", "POST")
def make_order(venue, symbol):

	try:
		data = str(request.body.read(), encoding="utf-8")
		data = json.loads(data)
	except:
		return {"ok": False, "error": "Incoming data was not valid JSON"}

	try:
	
		# Thanks to cite-reader for the following:
		# Match behavior of real Stockfighter: recognize both these forms
		symbol = None
		if "stock" in data:
			symbol = data["stock"]
		elif "symbol" in data:
			symbol = data["symbol"]
		assert(symbol is not None)

		venue = data["venue"]
		account = data["account"]

		try:
			create_book_if_needed(venue, symbol)
		except TooManyBooks:
			return BOOK_ERROR
		
		if auth:
			try:
				apikey = api_key_from_headers(request.headers)
			except NoApiKey:
				return NO_AUTH_ERROR
				
			if account not in auth:
				return AUTH_FAILURE

			if auth[account] != apikey:
				return AUTH_FAILURE

		ret = all_venues[venue][symbol].parse_order(data)
		assert(ret)
		return ret
		
	except Exception as e:
		ret = response_from_exception(e)
		return ret


@route("/")
def home():
	return """
	<pre>
	
	Unofficial Stockfighter server
	By Amtiskaw (Fohristiwhirl on GitHub) and Medecau
	With helpful help from DanielVF
	
	Mad props to patio11 for the fundamental design
	</pre>
	"""

# ----------------------------------------------------------------------------------------

def create_auth_records():
	global auth
	global opts
	
	with open(opts.accounts_file) as infile:
		auth = json.load(infile)

def main():
	global opts; global args
	
	opt_parser = optparse.OptionParser()
	
	opt_parser.add_option(
		"-b", "--maxbooks",
		dest = "maxbooks",
		type = "int",
		help = "Maximum number of books (exchange/ticker combos) [default: %default]")
	opt_parser.set_defaults(maxbooks = 10)
	
	opt_parser.add_option(
		"-v", "--venue",
		dest = "default_venue",
		type = "str",
		help = "Default venue; always exists [default: %default]")
	opt_parser.set_defaults(default_venue = "TESTEX")

	opt_parser.add_option(
		"-s", "--symbol", "--stock",
		dest = "default_symbol",
		type = "str",
		help = "Default symbol; always exists on default venue [default: %default]")
	opt_parser.set_defaults(default_symbol = "FOOBAR")
	
	opt_parser.add_option(
		"-a", "--accounts",
		dest = "accounts_file",
		type = "str",
		help = "File containing JSON dict of account names mapped to their API keys [default: none]")
	opt_parser.set_defaults(accounts_file = "")
	
	opts, args = opt_parser.parse_args()
	
	create_book_if_needed(opts.default_venue, opts.default_symbol)
	
	if opts.accounts_file:
		create_auth_records()
	
	if not auth:
		print("\n -----> Warning: running WITHOUT AUTHENTICATION! <-----\n")
	
	run(host = "127.0.0.1", port = 8000)
	

if __name__ == "__main__":
	main()
