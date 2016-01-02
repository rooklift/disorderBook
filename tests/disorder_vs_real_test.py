# Usage: Execute against both the real test server and the local server. Compare results.
# Check that nobody else used the real test server for the duration (via order IDs)


import copy, inspect, json, requests, time, random


_API_URL = "http://127.0.0.1:8000/ob/api/"
# _API_URL = "https://api.stockfighter.io/ob/api/"

_API_KEY = "exb123456"		# Needs a legit key if running on the official server

_extra_headers = {"X-Starfighter-Authorization" : _API_KEY}


TEST_SIZE = 200
SEED = 155176

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


# ---------------------------------------------------------------------------------


INFO = Order()

INFO.account = "EXB123456"
INFO.venue = "TESTEX"
INFO.symbol = "FOOBAR"

# Clear the book...

INFO.qty = 999999
INFO.orderType = "market"
INFO.direction = "buy"
INFO.price = 0

execute(INFO)

INFO.direction = "sell"
execute(INFO)


for n in range(TEST_SIZE):
	INFO.price = random.randint(1, 5000)
	INFO.qty = random.randint(1, 100)
	INFO.direction = random.choice(["buy", "sell"])
	INFO.orderType = random.choice(["limit", "limit", "limit", "limit", "market", "immediate-or-cancel", "fill-or-kill"])
	res = execute(INFO)
	if n == 0:
		first_id = res["id"]
	elif n == TEST_SIZE - 1:
		last_id = res["id"]
	print(n)

print("TEST_SIZE =", TEST_SIZE)
print("SEED =", SEED)

quote = quote(INFO.venue, INFO.symbol, verbose = True)

print("last - first == {} (expected {})".format(last_id - first_id, TEST_SIZE - 1))
input()


''' Results from official: (on my machine, but due to seeding issues, may differ across machines)

TEST_SIZE = 200
SEED = 155176
{
  "ok": true,
  "symbol": "FOOBAR",
  "venue": "TESTEX",
  "bid": 1742,
  "ask": 2448,
  "bidSize": 17,
  "askSize": 21,
  "bidDepth": 192,
  "askDepth": 520,
  "last": 1676,
  "lastSize": 26,
  "lastTrade": "2015-12-30T15:13:38.485833096Z",
  "quoteTime": "2015-12-30T15:13:47.203555038Z"
}
last - first == 199 (expected 199)


'''

