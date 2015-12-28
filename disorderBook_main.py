import http.server, json
import disorderBook_book as book

GENERIC_ERROR = '{"ok": false, "error": "Could not determine handler for request"}'

all_venues_and_symbols = dict()

def create_book_if_needed(venue, symbol):
	pair = (venue, symbol)
	if pair not in all_venues_and_symbols:
		all_venues_and_symbols[pair] = book.OrderBook(venue, symbol)

class StockFighterHandler(http.server.BaseHTTPRequestHandler):
	
	def send_string(self, s):
		if type(s) == dict or type(s) == book.Order:
			s = json.dumps(s)
		self.send_response(200)
		self.end_headers()
		self.wfile.write(s.encode(encoding="ascii"))
		
	def send_bad(self, s):
		if type(s) == dict or type(s) == book.Order:
			s = json.dumps(s)
		self.send_response(400)
		self.end_headers()
		self.wfile.write(s.encode(encoding="ascii"))
	
	def send_exception(self, e):
		self.send_response(400)
		self.end_headers()
		msg = '"ok": "false", "error" : "{}"'.format(e)
		self.wfile.write(e.encode(encoding="ascii"))
	
	def do_GET(self):
		path = self.path
		
		try:
			decomp = path.split("/")
		except:
			send_bad(GENERIC_ERROR)
			return
		
		# What follows is an incredibly crude way of guessing what type of request
		# was intended. There must be a cleaner way but it's late and I'm tired.

		# ----------- HEARTBEAT ------------------------------------------------------
		
		try:
			if decomp[-1] == "heartbeat" and "/venues/" not in path:
				self.send_string({"ok": True, "error": ""})
				return
		except Exception as e:
			send_exception(e)
			return
			
		# ----------- VENUE HEARTBEAT ------------------------------------------------
		
		try:
			if decomp[-1] == "heartbeat" and decomp[-3] == "venues":
				self.send_string({"ok": True, "venue": decomp[-2]})
				return
		except Exception as e:
			send_exception(e)
			return
		
		# ----------- STOCK LIST -----------------------------------------------------
		
		try:
			if decomp[-1] == "stocks" and decomp[-3] == "venues":
				ret = {"ok" : True, "symbols" : [{"symbol" : symbol, "name" : symbol + " Inc"} for (venue, symbol) in all_venues_and_symbols.keys() if venue == decomp[-2]]}
				self.send_string(ret)
				return
		except Exception as e:
			send_exception(e)
			return
		
		# ----------- ORDERBOOK ------------------------------------------------------
		
		try:
			if decomp[-2] == "stocks" and decomp[-4] == "venues":
				symbol = decomp[-1]
				venue = decomp[-3]
				create_book_if_needed(venue, symbol)
				ret = all_venues_and_symbols[(venue, symbol)].get_book()
				assert(ret)
				self.send_string(ret)
				return
		except Exception as e:
			send_exception(e)
			return
		
		# ----------- QUOTE ----------------------------------------------------------
		
		try:
			if path.endswith("quote") and decomp[-3] == "stocks" and decomp[-5] == "venues":
				symbol = decomp[-2]
				venue = decomp[-4]
				create_book_if_needed(venue, symbol)
				ret = all_venues_and_symbols[(venue, symbol)].get_quote()
				assert(ret)
				self.send_string(ret)
				return
		except Exception as e:
			send_exception(e)
			return
		
		# ----------- STATUS ---------------------------------------------------------
		
		try:
			if decomp[-2] == "orders" and decomp[-4] == "stocks" and decomp[-6] == "venues":
				id = int(decomp[-1])
				symbol = decomp[-3]
				venue = decomp[-5]
				create_book_if_needed(venue, symbol)
				ret = all_venues_and_symbols[(venue, symbol)].get_status(id)
				assert(ret)
				self.send_string(ret)
				return
		except Exception as e:
			send_exception(e)
			return
		
		# ----------- STATUS ALL ORDERS ----------------------------------------------
		
		try:
			if decomp[-1] == "orders" and decomp[-3] == "accounts" and decomp[-5] == "venues":
				self.send_string('{"ok": false, "error": "not implemented"}')
				return
		except Exception as e:
			send_exception(e)
			return
		
		# ----------- STATUS ALL ORDERS IN STOCK -------------------------------------
		
		try:
			if decomp[-1] == "orders" and decomp[-3] == "stocks" and decomp[-5] == "accounts" and decomp[-7] == "venues":
				venue = decomp[-6]
				account = decomp[-4]
				symbol = decomp[-2]
				create_book_if_needed(venue, symbol)
				ret = all_venues_and_symbols[(venue, symbol)].get_all_orders(account)
				assert(ret)
				self.send_string(ret)
				return
		except Exception as e:
			send_exception(e)
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
			send_exception(e)
			return
		
		# ----------- MAKE AN ORDER -------------------------------------
		
		try:
			if not path.endswith("cancel"):
				data = str(data, encoding="ascii")
				data = json.loads(data)

				venue = data["venue"]
				symbol = data["symbol"]
			
				create_book_if_needed(venue, symbol)
			
				ret = all_venues_and_symbols[(venue, symbol)].parse_order(data)
				assert(ret)
				self.send_string(ret)
				return
		except Exception as e:
			send_exception(e)
			return
		
		# ----------- CANCEL AN ORDER -----------------------------------
		
		try:
			if decomp[-1] == "cancel" and decomp[-3] == "orders" and decomp[-5] == "stocks" and decomp[-7] == "venues":
				
				venue = decomp[-6]
				symbol = decomp[-4]
				id = decomp[-2]
				
				create_book_if_needed(venue, symbol)
				ret = all_venues_and_symbols[(venue, symbol)].cancel_order(id)
				assert(ret)
				self.send_string(ret)
				return
		except Exception as e:
			send_exception(e)
			return
		
		self.send_bad(GENERIC_ERROR)
		return
	
	# ---------------------------------------------------------------------------------------------------------------
	
	def do_DELETE(self):
		path = self.path
		
		try:
			decomp = path.split("/")
		except Exception as e:
			send_exception(e)
			return
		
		try:
			if decomp[-2] == "orders" and decomp[-4] == "stocks" and decomp[-6] == "venues":
				venue = decomp[-5]
				symbol = decomp[-3]
				id = decomp[-1]
				
				create_book_if_needed(venue, symbol)
				ret = all_venues_and_symbols[(venue, symbol)].cancel_order(id)
				assert(ret)
				self.send_string(ret)
				return
		except Exception as e:
			send_exception(e)
			return
		
		self.send_bad(GENERIC_ERROR)
		return


PORT = 8000
server_address = ("localhost", PORT)
httpd = http.server.HTTPServer(server_address, StockFighterHandler)
print("disorderBook running on port {}...".format(PORT))
httpd.serve_forever()
