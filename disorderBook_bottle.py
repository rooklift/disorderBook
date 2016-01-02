# This is a better version of the frontend using the bottle library
# Made by Medecau and Fohristiwhirl

import json, optparse
from bottle import route, request, run
import disorderBook_book as book

all_venues = dict()			# dict: venue string ---> dict: stock string ---> OrderBook objects
current_book_count = 0

BOOK_ERROR = {"ok": False, "error": "Book limit exceeded! (See command line options)"}

# ----------------------------------------------------------------------------------------

class TooManyBooks (Exception):
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
		ret = all_venues[venue][symbol].get_status(id)
		assert(ret)
		return ret
	except Exception as e:
		ret = response_from_exception(e)
		return ret


@route("/ob/api/venues/<venue>/accounts/<account>/orders", "GET")
def status_all_orders(venue, account):

	orders = []

	if venue in all_venues:
		for bk in all_venues[venue].values():
			orders += bk.get_all_orders(account)["orders"]

	ret = dict()
	ret["ok"] = True
	ret["venue"] = venue
	ret["orders"] = orders
	return ret


@route("/ob/api/venues/<venue>/accounts/<account>/stocks/<symbol>/orders", "GET")
def status_all_orders_one_stock(venue, account, symbol):

	try:
		create_book_if_needed(venue, symbol)
	except TooManyBooks:
		return BOOK_ERROR

	try:
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
		ret = all_venues[venue][symbol].cancel_order(id)
		assert(ret)
		return ret
	except Exception as e:
		ret = response_from_exception(e)
		return ret


@route("/ob/api/venues/<venue>/stocks/<symbol>/orders", "POST")
def make_order(venue, symbol):

	try:
		data = str(request.body.read(), encoding="utf-8")
		data = json.loads(data)
	except:
		return {"ok": False, "error": "Incoming data was not valid JSON"}

	try:
		# Thanks to cite-reader for this:
		# Match behavior of real Stockfighter: recognize both these forms

		symbol = None
		if "stock" in data:
			symbol = data["stock"]
		elif "symbol" in data:
			symbol = data["symbol"]
		assert(symbol is not None)

		venue = data["venue"]

		try:
			create_book_if_needed(venue, symbol)
		except TooManyBooks:
			return BOOK_ERROR

		ret = all_venues[venue][symbol].parse_order(data)
		assert(ret)
		return ret
	except Exception as e:
		ret = response_from_exception(e)
		return ret


@route("/ob/api/venues/<venue>/stocks/<symbol>/orders/<id>/cancel", "POST")		# Alternate cancel method, for people without DELETE
def cancel_via_post(venue, symbol, id):
	
	try:
		create_book_if_needed(venue, symbol)
	except TooManyBooks:
		return BOOK_ERROR
	
	try:
		ret = all_venues[venue][symbol].cancel_order(id)
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
	</pre>
	"""

# ----------------------------------------------------------------------------------------

def main():
	global opts; global args
	
	opt_parser = optparse.OptionParser()
	
	opt_parser.add_option("-b", "--maxbooks", dest="maxbooks", type="int", help="Maximum number of books (exchange/ticker combos) [default: %default]")
	opt_parser.set_defaults(maxbooks = 10)
	opt_parser.add_option("-v", "--venue", dest="default_venue", type="str", help="Default venue; always exists [default: %default]")
	opt_parser.set_defaults(default_venue = "TESTEX")
	opt_parser.add_option("-s", "--symbol", dest="default_symbol", type="str", help="Default symbol; always exists on default venue [default: %default]")
	opt_parser.set_defaults(default_symbol = "FOOBAR")
	
	opts, args = opt_parser.parse_args()
	
	create_book_if_needed(opts.default_venue, opts.default_symbol)
	
	run(host="127.0.0.1", port=8000)
	

if __name__ == "__main__":
	main()
