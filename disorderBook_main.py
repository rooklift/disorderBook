import http.server, json
import disorderBook_book as book

GENERIC_ERROR = '{"ok": false, "error": "Could not determine handler for request"}'

venue_symbol_book_map = dict()			# tuple (venue, symbol) ---> OrderBook object
all_venues = set()

def create_book_if_needed(venue, symbol):
	pair = (venue, symbol)
	
	all_venues.add(venue)
	
	if pair not in venue_symbol_book_map:
		venue_symbol_book_map[pair] = book.OrderBook(venue, symbol)

class StockFighterHandler(http.server.BaseHTTPRequestHandler):
	
	# Most of the heavy lifting is done by the parent class, for more info see:
	# https://hg.python.org/cpython/file/3.4/Lib/http/server.py
	#
	# We only need to implement do_GET, do_POST, and do_DELETE and it will call those functions
	# as needed. But I also reimplement log_request just to disable printing to screen...
	
	def log_request(self, *args, **kwargs):
		pass
	
	# Nothing else in this new class is a reimplementation. Avoid naming something "send_error",
	# "send_header", "send_response", "handle", "parse_request", as these do exist in the parent.
	
	def send_whatever(self, s, code = 200):		# Accepts strings or dicts (converts to JSON in that case)
		if isinstance(s, dict):
			s = json.dumps(s, indent = 2)
		self.send_response(code)				# Sends http first line e.g. "HTTP/1.1 200 OK", plus Server and Date lines
		self.send_header("Content-Type", "application/json")
		self.end_headers()
		self.wfile.write(s.encode(encoding="ascii"))
		
	def send_bad(self, s):
		self.send_whatever(s, 400)
	
	def send_exception(self, e):
		msg = '{{"ok": false, "error": "{}"}}'.format(e)
		self.send_whatever(msg, 400)
	
	def do_GET(self):
		path = self.path
		
		try:
			decomp = path.split("/")
			decomp = [""] * 7 + decomp		# To ensure our checks don't cause IndexError
		except:
			self.send_bad(GENERIC_ERROR)
			return
		
		# What follows is an incredibly crude way of guessing what type of request
		# was intended. There must be a cleaner way but it's late and I'm tired.

		# ----------- HEARTBEAT ------------------------------------------------------
		
		try:
			if decomp[-1] == "heartbeat" and "venues" not in path:
				self.send_whatever('{"ok": true, "error": ""}')
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- VENUE LIST -----------------------------------------------------
		
		try:
			if decomp[-1] == "venues":
				ret = dict()
				ret["ok"] = True
				ret["venues"] = [{"name": v + " Exchange", "venue": v, "state" : "open"} for v in all_venues]
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- VENUE HEARTBEAT ------------------------------------------------
		
		try:
			if decomp[-1] == "heartbeat" and decomp[-3] == "venues":
				self.send_whatever('{{"ok": true, "venue": "{}"}}'.format(decomp[-2]))
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- STOCK LIST (2 different URLs) ----------------------------------
		
		try:
			if decomp[-1] == "stocks" and decomp[-3] == "venues":
				request_venue = decomp[-2]
			elif decomp[-2] == "venues":
				request_venue = decomp[-1]
			else:
				request_venue = None

			if request_venue is not None:
				symbol_list = [symbol for (venue, symbol) in venue_symbol_book_map if venue == request_venue]
				
				if symbol_list:
					ret = {
							"ok" : True,
							"symbols" : [{"symbol" : symbol, "name" : symbol + " Inc"} for symbol in symbol_list]
						}
				else:
					ret = {
							"ok" : True,
							"symbols" : [],
							"info" : "Use any venue and symbol to create an exchange"
						}
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- ORDERBOOK ------------------------------------------------------
		
		try:
			if decomp[-2] == "stocks" and decomp[-4] == "venues":
				symbol = decomp[-1]
				venue = decomp[-3]
				
				create_book_if_needed(venue, symbol)
				ret = venue_symbol_book_map[(venue, symbol)].get_book()
				assert(ret)
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- QUOTE ----------------------------------------------------------
		
		try:
			if decomp[-1] == "quote" and decomp[-3] == "stocks" and decomp[-5] == "venues":
				symbol = decomp[-2]
				venue = decomp[-4]
				
				create_book_if_needed(venue, symbol)
				ret = venue_symbol_book_map[(venue, symbol)].get_quote()
				assert(ret)
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- STATUS ---------------------------------------------------------
		
		try:
			if decomp[-2] == "orders" and decomp[-4] == "stocks" and decomp[-6] == "venues":
				id = int(decomp[-1])
				symbol = decomp[-3]
				venue = decomp[-5]
				
				create_book_if_needed(venue, symbol)
				ret = venue_symbol_book_map[(venue, symbol)].get_status(id)
				assert(ret)
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- STATUS ALL ORDERS ON A VENUE (ALL STOCKS) ----------------------
		
		try:
			if decomp[-1] == "orders" and decomp[-3] == "accounts" and decomp[-5] == "venues":
				account = decomp[-2]
				request_venue = decomp[-4]
				
				orders = []
				
				for (venue, symbol) in venue_symbol_book_map:	# Getting this tuple from the keys
					if venue == request_venue:
						book = venue_symbol_book_map[(venue, symbol)]
						orders += book.get_all_orders(account)["orders"]
				
				ret = dict()
				ret["ok"] = True
				ret["venue"] = request_venue
				ret["orders"] = orders
				
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- STATUS ALL ORDERS IN STOCK -------------------------------------
		
		try:
			if decomp[-1] == "orders" and decomp[-3] == "stocks" and decomp[-5] == "accounts" and decomp[-7] == "venues":
				venue = decomp[-6]
				account = decomp[-4]
				symbol = decomp[-2]
				
				create_book_if_needed(venue, symbol)
				book = venue_symbol_book_map[(venue, symbol)]
				ret = book.get_all_orders(account)
				assert(ret)
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		self.send_bad(GENERIC_ERROR)
		return

	# ---------------------------------------------------------------------------------------------------------------
	
	def do_POST(self):
		data = self.rfile.read(int(self.headers['Content-Length']))
		path = self.path
		
		try:
			decomp = path.split("/")
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- MAKE AN ORDER -------------------------------------
		
		try:								# Any POST that's not a cancel is accepted
			if "cancel" not in path:
				data = str(data, encoding="ascii")
				data = json.loads(data)

				venue = data["venue"]

				# Thanks to cite-reader for this:
				# Match behavior of real Stockfighter: recognize both these forms
				if "stock" in data:
					symbol = data["stock"]
				elif "symbol" in data:
					symbol = data["symbol"]
			
				create_book_if_needed(venue, symbol)
			
				ret = venue_symbol_book_map[(venue, symbol)].parse_order(data)
				assert(ret)
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- POST METHOD CANCEL AN ORDER -----------------------
		
		try:
			if decomp[-1] == "cancel" and decomp[-3] == "orders" and decomp[-5] == "stocks" and decomp[-7] == "venues":
				venue = decomp[-6]
				symbol = decomp[-4]
				id = decomp[-2]
				
				create_book_if_needed(venue, symbol)
				ret = venue_symbol_book_map[(venue, symbol)].cancel_order(id)
				assert(ret)
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		self.send_bad(GENERIC_ERROR)
		return
	
	# ---------------------------------------------------------------------------------------------------------------
	
	def do_DELETE(self):
		path = self.path
		
		try:
			decomp = path.split("/")
		except Exception as e:
			self.send_exception(e)
			return
		
		try:
			if decomp[-2] == "orders" and decomp[-4] == "stocks" and decomp[-6] == "venues":
				venue = decomp[-5]
				symbol = decomp[-3]
				id = decomp[-1]
				
				create_book_if_needed(venue, symbol)
				ret = venue_symbol_book_map[(venue, symbol)].cancel_order(id)
				assert(ret)
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		self.send_bad(GENERIC_ERROR)
		return


if __name__ == "__main__":

	# Create 1 exchange and stock so the venues list isn't empty.
	# Override the defaults with a text file DEFAULT_STOCK.txt:
	
	defaultvenue, defaultsymbol = "DORBEX", "CATS"
	try:
		with open("DEFAULT_STOCK.txt") as infile:
			defaultvenue, defaultsymbol = infile.readline().split()
	except:
		pass
	create_book_if_needed(defaultvenue, defaultsymbol)

	PORT = 8000
	server_address = ("localhost", PORT)
	httpd = http.server.HTTPServer(server_address, StockFighterHandler)
	print("disorderBook running on port {}...".format(PORT))
	httpd.serve_forever()
