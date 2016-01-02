# OK this is not exactly small but the problem
# won't be in the Order() class at least.


import copy, inspect, json, requests, threading, time, queue, random

_API_URL = "http://127.0.0.1:8000/ob/api/"

_API_KEY = "unused"

_extra_headers = {"X-Starfighter-Authorization" : _API_KEY}


PRINT_LOCK = threading.Lock()


class Order():

	attributes_and_types = {			# These are all the attributes that can ever be set
		"account" : str,
		"venue" : str,
		"symbol" : str,		# FIXME
		"price" : int,
		"qty" : int,
		"direction" : str,
		"orderType" : str
	}
	
	synonyms = {
		"stock" : "symbol"	# FIXME
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
		with PRINT_LOCK:
			print("get_json_from_url() called from {}() - TimeoutError".format(caller))
			return None
	except requests.exceptions.ConnectionError:
		with PRINT_LOCK:
			print("get_json_from_url() called from {}() - requests.exceptions.ConnectionError".format(caller))
			return None
	
	# We got some sort of reply...
	
	try:
		result = raw.json()
	except ValueError:
		with PRINT_LOCK:
			print(raw.text)
			print("RESULT WAS NOT VALID JSON.")
		return None
	
	# The reply was valid JSON...
	
	if require_ok:
		if "ok" not in result:
			with PRINT_LOCK:
				print(raw.text)
				print("THE 'ok' FIELD WAS NOT PRESENT.")
			return None
		if result["ok"] != True:
			with PRINT_LOCK:
				print(raw.text)
				print("THE 'ok' FIELD WAS NOT TRUE.")
			return None
	
	# All tests have passed. Nothing has been printed (since we only print errors).
	
	if superverbose:
		with PRINT_LOCK:
			print(raw.headers)
	if verbose:
		with PRINT_LOCK:
			print(raw.text)
	
	return result


def execute(order, verbose = False):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}/orders".format(order.venue, order.stock), postdata = order.as_json(), verbose = verbose)


def execute_from_queue(task_queue, result_queue, verbose = False):
	order = task_queue.get()
	result = execute(order, verbose = verbose)
	result_queue.put(result)
	task_queue.task_done()
	return


def market_maker():

	INFO = Order()
	
	INFO.account = "MARKETMAKER"
	INFO.venue = "FOOEX"
	INFO.symbol = "CATS"
	INFO.orderType = "limit"
	INFO.qty = 100
	
	task_queue = queue.Queue()
	result_queue = queue.Queue()
	
	while 1:
	
		for n in range(20):
		
			INFO.price = random.randint(4000, 6000)
			INFO.direction = random.choice(["buy", "sell"])
			
			task_queue.put(INFO.copy())
		
			newthread = threading.Thread(target = execute_from_queue, daemon = True, kwargs={
						"task_queue" : task_queue,
						"result_queue" : result_queue,
						"verbose" : True}
			)
			newthread.start()

		task_queue.join()
		with PRINT_LOCK:
			print("Sleeping for 5....")
		time.sleep(5)


if __name__ == "__main__":
	market_maker()

