# This program fires off multiple randomly generated orders at 2 different servers, and compares
# the quotes that result. One of these servers could be the official test server, though other
# people might place orders on it at the same time.


import copy, inspect, json, requests, time, random


API_URL_1 = "http://127.0.0.1:8000/ob/api/"
API_KEY_1 = "unused"

API_URL_2 = "https://api.stockfighter.io/ob/api/"
API_KEY_2 = "fixme"				# Needs a legit key for official

ACCOUNT_1 = "DISORDERTEST"
VENUE_1 = "SELLEX"
SYMBOL_1 = "CATS"

ACCOUNT_2 = "EXB123456"
VENUE_2 = "TESTEX"
SYMBOL_2 = "FOOBAR"

TEST_SIZE = 200
SEED = 155178

# ------------------------------------------------------------------------------------

_API_URL = API_URL_1		# This is what's actually used by get_json_from_url()

_api_cookie_text = "api_key={}".format(API_KEY_1)
_extra_headers = {"X-Starfighter-Authorization" : API_KEY_1, "Cookie" : _api_cookie_text}

def change_api_key(k):
	global _api_cookie_text
	global _extra_headers
	
	_api_cookie_text = "api_key={}".format(k)
	_extra_headers = {"X-Starfighter-Authorization" : k, "Cookie" : _api_cookie_text}
	
def change_url(u):
	global _API_URL
	_API_URL = u



random.seed(SEED)



# --------------- necessary stuff that could be in its own file ------------------------------------------

class Order():

	attributes_and_types = {			# These are all the attributes that can ever be set
		"account" : str,
		"venue" : str,
		"stock" : str,
		"price" : int,
		"qty" : int,
		"direction" : str,
		"orderType" : str
	}
	
	synonyms = {
		"symbol" : "stock"
	}
	
	attributes = attributes_and_types.keys()

	def __init__(self, att_dict=None):
		for attribute in self.attributes:
			setattr(self, attribute, None)

		# Simplest just to do the above even when the caller has tried to provide values.
		# So if the following fails in anyway we will still have None.
		
		if type(att_dict) is dict:
			for key in att_dict.keys():
				try:
					setattr(self, key, att_dict[key])
				except:
					print("Couldn't set attribute {} to {}".format(key, att_dict[key]))
		elif att_dict is None:
			pass
		else:
			print("Ignoring non-dictionary argument.")
	
	# Our own __setattr__ forbids the addition of any other attributes,
	# as well as ensuring the attribute has the correct type or None
	
	def __setattr__(self, name, val):
		if name in self.synonyms:
			name = self.synonyms[name]
		if name not in self.attributes:
			print("Not a valid attribute: '{}'.".format(name))
			return
		if val is not None:						# None values do get saved unaltered
			correct_type = self.attributes_and_types[name]
			try:
				val = correct_type(val)
			except:
				print("Unable to convert {} to type {}".format(val, correct_type))
				return
		super().__setattr__(name, val)
	
	def __getattr__(self, name):
		if name in self.synonyms:
			name = self.synonyms[name]
		return super().__getattribute__(name)
	
	def as_json(self):
		resultdict = dict()
		for attribute in self.attributes:
			val = getattr(self, attribute)
			resultdict[attribute] = val
		return json.dumps(resultdict)
	
	def dump(self):
		for attribute in self.attributes:
			val = getattr(self, attribute)
			print("{} = {}".format(attribute, val if val is not None else ""))
	
	def set_to_buy(self):
		self.direction = "buy"
	
	def set_to_sell(self):
		self.direction = "sell"
	
	def set_to_limit(self):
		self.orderType = "limit"
	
	def set_to_ioc(self):
		self.orderType = "immediate-or-cancel"
	
	def set_to_fok(self):
		self.orderType = "fill-or-kill"
	
	def set_to_market(self):
		self.orderType = "market"
	
	def copy(self):
		return copy.copy(self)



def get_json_from_url(url, postdata = None, deletemethod = False, verbose = False, superverbose = False, require_ok = True):		# Note: POST overrides DELETE

	caller = inspect.stack()[1][3]

	try:
		if postdata is not None:				# Might be "" which should be allowed, so test for not None
			raw = requests.post(url, data = postdata, headers = _extra_headers)
		elif deletemethod:
			raw = requests.delete(url, headers = _extra_headers)
		else:
			raw = requests.get(url, headers = _extra_headers)
	except TimeoutError:
		print("get_json_from_url() called from {}() - TimeoutError".format(caller))
		return None
	except requests.exceptions.ConnectionError:
		print("get_json_from_url() called from {}() - requests.exceptions.ConnectionError".format(caller))
		return None
	
	# We got some sort of reply...
	
	try:
		result = raw.json()
	except ValueError:
		print(raw.text)
		print("RESULT WAS NOT VALID JSON.")
		return None
	
	# The reply was valid JSON...
	
	if require_ok:
		if "ok" not in result:
			print(raw.text)
			print("THE 'ok' FIELD WAS NOT PRESENT.")
			return None
		if result["ok"] != True:
			print(raw.text)
			print("THE 'ok' FIELD WAS NOT TRUE.")
			return None
	
	# All tests have passed. Nothing has been printed (since we only print errors).
	
	if superverbose:
		print(raw.headers)
	if verbose:
		print(raw.text)
	
	return result


def execute(order, verbose = False):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}/orders".format(order.venue, order.stock), postdata = order.as_json(), verbose = verbose)

def quote(venue, symbol, verbose = False):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}/quote".format(venue, symbol), verbose = verbose)

def orderbook(venue, symbol, verbose = False):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}".format(venue, symbol), verbose = verbose)

def set_from_account_1(order):
	order.account = ACCOUNT_1
	order.venue = VENUE_1
	order.symbol = SYMBOL_1
	change_api_key(API_KEY_1)
	change_url(API_URL_1)

def set_from_account_2(order):
	order.account = ACCOUNT_2
	order.venue = VENUE_2
	order.symbol = SYMBOL_2
	change_api_key(API_KEY_2)
	change_url(API_URL_2)

# ---------------------------------------------------------------------------------


INFO = Order()


def clear_the_books():
	global INFO
	
	INFO.qty = 999999
	INFO.orderType = "market"
	INFO.direction = "buy"
	INFO.price = 1

	set_from_account_1(INFO)
	execute(INFO)
	set_from_account_2(INFO)
	execute(INFO)

	INFO.direction = "sell"

	set_from_account_1(INFO)
	execute(INFO)
	set_from_account_2(INFO)
	execute(INFO)

	# Set the last price and size...

	INFO.orderType = "limit"
	INFO.price = 5000
	INFO.qty = 50
	INFO.direction = "sell"

	set_from_account_1(INFO)
	execute(INFO)
	set_from_account_2(INFO)
	execute(INFO)

	INFO.direction = "buy"

	set_from_account_1(INFO)
	execute(INFO)
	set_from_account_2(INFO)
	execute(INFO)



clear_the_books()

for n in range(TEST_SIZE):
	INFO.price = random.randint(1, 5000)
	INFO.qty = random.randint(1, 100)
	INFO.direction = random.choice(["buy", "sell"])
	INFO.orderType = random.choice(["limit", "limit", "limit", "limit", "market", "immediate-or-cancel", "fill-or-kill"])
	
	set_from_account_1(INFO)
	res1 = execute(INFO)
	id1 = res1["id"]
	if n == 0:
		first_id_1 = id1
	if n == TEST_SIZE - 1:
		last_id_1 = id1
	q1 = quote(INFO.venue, INFO.symbol)
	o1 = orderbook(INFO.venue, INFO.symbol)
		
	set_from_account_2(INFO)
	res2 = execute(INFO)
	id2 = res2["id"]
	if n == 0:
		first_id_2 = id2
	if n == TEST_SIZE - 1:
		last_id_2 = id2
	q2 = quote(INFO.venue, INFO.symbol)
	o2 = orderbook(INFO.venue, INFO.symbol)
	
	print("IDs (adjusted, should match): {}, {} ----- {} {} @ {} ({})".format(id1 - first_id_1, id2 - first_id_2, INFO.direction, INFO.qty, INFO.price, INFO.orderType))
	
	bids_match = False
	asks_match = False
	if o1["bids"] == o2["bids"]:
		bids_match = True
	if o1["asks"] == o2["asks"]:
		asks_match = True
	if (not o1["bids"]) and (not o2["bids"]):
		bids_match = True
	if (not o1["asks"]) and (not o2["asks"]):
		asks_match = True
	
	if bids_match and asks_match:
		print("Books MATCH")
	else:
		print(o1["bids"], o1["asks"])
		print(o2["bids"], o2["asks"])
	
	results_match = True
	for field in ("direction", "originalQty", "price", "totalFilled", "qty", "open"):
		if field not in res1:
			print("{} missing from RESULT of order 1".format(field))
			print(res1)
		if field not in res2:
			print("{} missing from RESULT of order 2".format(field))
			print(res2)
		try:
			if res1[field] != res2[field]:
				results_match = False
				print("ORDER RESULT: {}: {} vs {}".format(field, res1[field], res2[field]))
		except KeyError:
			pass
	
	if results_match:
		print("Results MATCH")
	
	for field in ("ask", "bidDepth", "bidSize", "askSize", "last", "askDepth", "bid", "lastSize"):
		try:
			if q1[field] != q2[field]:
				print("QUOTE: {}: {} vs {}".format(field, q1[field], q2[field]))
		except KeyError:
			pass
	print()

print("TEST_SIZE =", TEST_SIZE)
print("SEED =", SEED)
print()

set_from_account_1(INFO)
quote(INFO.venue, INFO.symbol, verbose = True)
print("last - first == {} (expected {})".format(last_id_1 - first_id_1, TEST_SIZE - 1))
print()

set_from_account_2(INFO)
quote(INFO.venue, INFO.symbol, verbose = True)
print("last - first == {} (expected {})".format(last_id_2 - first_id_2, TEST_SIZE - 1))

input()

