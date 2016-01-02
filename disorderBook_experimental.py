import http.server, json, threading
import disorderBook_book as book


SERVER_THREADS = 20


GENERIC_ERROR = {"ok": False, "error": "Could not determine handler for request"}
TOO_MANY_BOOKS = {"ok": False, "error": "Server already has maximum number of books"}

all_venues = dict()		# dict: venue string ---> dict: stock string ---> OrderBook objects

currentbooks = 0



class Options ():
	def __init__(self, **kwargs):
		self.maxbooks = None


def parse_options ():
	pass


def create_book_if_needed(venue, symbol):

	if venue not in all_venues:
		if options.maxbooks and currentbooks > options.maxbooks:
			raise ValueError
		all_venues[venue] = dict()
		
	if symbol not in all_venues[venue]:
		if options.maxbooks and currentbooks > options.maxbooks:
			raise ValueError
		all_venues[venue][symbol] = book.OrderBook(venue, symbol)


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
		di = {"ok": False, "error": str(e)}
		self.send_whatever(di, 400)
	
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
				self.send_whatever({"ok": True, "error": ""})
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
				venue = decomp[-2]
				if venue in all_venues:
					self.send_whatever({"ok": True, "venue": venue})
				else:
					self.send_whatever({"ok": False, "error": "Venue {} does not exist (create it by using it)".format(venue)})
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		# ----------- STOCK LIST (2 different URLs) ----------------------------------
		
		try:
			if decomp[-1] == "stocks" and decomp[-3] == "venues":
				venue = decomp[-2]
			elif decomp[-2] == "venues":
				venue = decomp[-1]
			else:
				venue = None

			if venue is not None:			# We currently do accept empty string
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
				
				try:
					create_book_if_needed(venue, symbol)
				except:
					self.send_bad(TOO_MANY_BOOKS)
					return

				ret = all_venues[venue][symbol].get_book()
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
				
				try:
					create_book_if_needed(venue, symbol)
				except:
					self.send_bad(TOO_MANY_BOOKS)
					return

				ret = all_venues[venue][symbol].get_quote()
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
				
				try:
					create_book_if_needed(venue, symbol)
				except:
					self.send_bad(TOO_MANY_BOOKS)
					return

				ret = all_venues[venue][symbol].get_status(id)
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
				venue = decomp[-4]
				
				orders = []
				
				if venue in all_venues:
					for bk in all_venues[venue].values():
						orders += bk.get_all_orders(account)["orders"]
				
				ret = dict()
				ret["ok"] = True
				ret["venue"] = venue
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
				
				try:
					create_book_if_needed(venue, symbol)
				except:
					self.send_bad(TOO_MANY_BOOKS)
					return
				
				ret = all_venues[venue][symbol].get_all_orders(account)
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
			
				try:
					create_book_if_needed(venue, symbol)
				except:
					self.send_bad(TOO_MANY_BOOKS)
					return
				
				ret = all_venues[venue][symbol].parse_order(data)
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
				
				try:
					create_book_if_needed(venue, symbol)
				except:
					self.send_bad(TOO_MANY_BOOKS)
					return
				
				ret = all_venues[venue][symbol].cancel_order(id)
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
				
				try:
					create_book_if_needed(venue, symbol)
				except:
					self.send_bad(TOO_MANY_BOOKS)
					return
				
				ret = all_venues[venue][symbol].cancel_order(id)
				assert(ret)
				self.send_whatever(ret)
				return
		except Exception as e:
			self.send_exception(e)
			return
		
		self.send_bad(GENERIC_ERROR)
		return

def run_server(s):
	s.serve_forever()
	

if __name__ == "__main__":
	
	options = Options()		# FIXME: actually parse options
	
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
	server_address = ("0.0.0.0", PORT)
	for n in range(SERVER_THREADS):
		httpd = http.server.HTTPServer(server_address, StockFighterHandler)
		print("disorderBook running on port {}...".format(PORT))
		
		newthread = threading.Thread(target = run_server, args = (httpd, ))
		newthread.start()
		