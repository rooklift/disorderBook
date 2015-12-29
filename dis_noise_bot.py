import json, random, requests, time

_API_URL = "http://127.0.0.1:8000/ob/api/"

_api_key = "unused"
_api_cookie_text = "api_key={}".format(_api_key)
_extra_headers = {"X-Starfighter-Authorization" : _api_key, "Cookie" : _api_cookie_text}


def get_json_from_url(url, postdata = None, deletemethod = False, verbose = False, superverbose = False, require_ok = True):		# Note: POST overrides DELETE

	try:
		if postdata is not None:
			result = requests.post(url, data = postdata, headers = _extra_headers)
		elif deletemethod:
			result = requests.delete(url, headers = _extra_headers)
		else:
			result = requests.get(url, headers = _extra_headers)
	except TimeoutError:
		print("TIMED OUT WAITING FOR REPLY (REQUEST MAY STILL HAVE SUCCEEDED).")
		return None
	except requests.exceptions.ConnectionError:
		print("TIMED OUT WAITING FOR REPLY (REQUEST MAY STILL HAVE SUCCEEDED).")
		return None
	
	# We got some sort of reply...
	
	try:
		resultjson = result.json()
	except ValueError:
		print(result.text)
		print("RESULT WAS NOT VALID JSON.")
		return None
	
	# The reply was valid JSON...
	
	if require_ok:
		if "ok" not in resultjson:
			print(result.text)
			print("THE 'ok' FIELD WAS NOT PRESENT.")
			return None
		if resultjson["ok"] != True:
			print(result.text)
			print("THE 'ok' FIELD WAS NOT TRUE.")
			return None
	
	# All tests have passed. Nothing has been printed (since we only print errors).
	
	if superverbose:
		print(result.headers)
	if verbose:
		print(result.text)
	
	return resultjson


def execute(venue, symbol, postdata, verbose=False):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}/orders".format(venue, symbol), postdata = postdata, verbose = verbose)

def cancel(venue, symbol, id, verbose=False, require_ok=True):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}/orders/{}".format(venue, symbol, id), deletemethod = True, verbose = verbose, require_ok = require_ok)

def quote(venue, symbol, verbose=False):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}/quote".format(venue, symbol), verbose = verbose)


def main():
	with open("DEFAULT_STOCK.txt") as infile:
		venue, symbol = infile.readline().split()


	account = "NOISE" + str(random.randint(0,999999))

	orderType = "limit"

	all_orders = []

	while 1:
		try:
			price = quote(venue, symbol)["last"]
			if price == 0:
				price = 5000
		except:
			price = 5000
		price += random.randint(-100, 100)
		qty = 100
		qty += random.randint(-50, 50)
		direction = random.choice(["buy", "sell"])
		
		r = execute(venue, symbol,
				json.dumps({"price" : price, "qty" : qty, "direction" : direction, "orderType" : orderType, "account" : account, "venue" : venue, "symbol" : symbol}),
				verbose = True)
		try:
			id = r["id"]
			all_orders.append(id)
		except:
			print("Trouble getting ID.")

		time.sleep(0.5)
		if len(all_orders) > 10:
			id = all_orders.pop(0)
			cancel(venue, symbol, id)


if __name__ == "__main__":
	main()
