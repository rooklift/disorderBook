# This is a minimal version of my rather larger suite of Stockfighter
# utility functions implementing only what some very minimal bots need.

import json, requests


_API_URL = "http://127.0.0.1:8000/ob/api/"

_api_key = "no_api_key_set"
_extra_headers = {"X-Starfighter-Authorization" : _api_key}


def change_api_key(k):
	global _api_key;			_api_key = str(k)
	global _extra_headers;		_extra_headers = {"X-Starfighter-Authorization" : _api_key}


def get_json_from_url(url, postdata = None, deletemethod = False, verbose = False, superverbose = False, require_ok = True):		# Note: POST overrides DELETE

	try:
		if postdata is not None:
			raw = requests.post(url, data = postdata, headers = _extra_headers)
		elif deletemethod:
			raw = requests.delete(url, headers = _extra_headers)
		else:
			raw = requests.get(url, headers = _extra_headers)
	except TimeoutError:
		print("ERROR -- TimeoutError")
		return None
	except requests.exceptions.ConnectionError:
		print("ERROR -- requests.exceptions.ConnectionError")
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


def execute_d(di, verbose = False):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}/orders".format(di["venue"], di["stock"]), postdata = json.dumps(di), verbose = verbose)

def cancel(venue, symbol, id, verbose=False, require_ok=True):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}/orders/{}".format(venue, symbol, id), deletemethod = True, verbose = verbose, require_ok = require_ok)

def quote(venue, symbol, verbose=False):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}/quote".format(venue, symbol), verbose = verbose)


def parse_fills_from_response(response, verbose = False):

	# Parse (many) fills from a single cancel (or status) request and return the net change in my shares and my cents...

	return_dict = {"shares" : 0, "cents" : 0, "fills" : 0}		# These are deltas, which the calling function must add to its tally
	
	if response is None:
		print("Couldn't parse fills... response is None.")
		return return_dict
	
	try:
		fills = response["fills"]
		direction = response["direction"]
	except:
		print("Couldn't find needed fields in response.")
		return return_dict
	
	for fill in fills:
		return_dict["fills"] += 1
		try:
			qty = fill["qty"]
			price = fill["price"]
			timestamp = fill["ts"]
			
			if direction == "buy":
				if verbose:
					print("Bought {} shares at ${}".format(qty, price / 100))
				return_dict["cents"] -= qty * price
				return_dict["shares"] += qty
			else:
				if verbose:
					print("Sold {} shares at ${}".format(qty, price / 100))
				return_dict["cents"] += qty * price
				return_dict["shares"] -= qty
			
		except:
			print("Unexpected error while parsing a fill.")
			continue
	
	return return_dict