# This is a minimal version of my rather larger suite of Stockfighter
# utility functions implementing only what some very minimal bots need.

import copy, json, requests


_API_URL = "https://api.stockfighter.io/ob/api/"
_api_key = "noapikey"

_api_cookie_text = "api_key={}".format(_api_key)		# Mockfighter likes cookies
_extra_headers = {"X-Starfighter-Authorization" : _api_key, "Cookie" : _api_cookie_text}


def change_api_key(k):
	global _api_key;			_api_key = str(k)
	global _api_cookie_text;	_api_cookie_text = "api_key={}".format(_api_key)
	global _extra_headers;		_extra_headers = {"X-Starfighter-Authorization" : _api_key, "Cookie" : _api_cookie_text}

def set_web_url(web):
    global _API_URL;        _API_URL = web

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------

class Order():

    attributes_and_types = {            # These are all the attributes that can ever be set
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
        if val is not None:                        # None values do get saved unaltered
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


def get_json_from_url(url, postdata = None, deletemethod = False, verbose = False, superverbose = False, require_ok = True):        # Note: POST overrides DELETE

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
    
    if not isinstance(result, dict):
        if superverbose:
            print(raw.status_code)
            print(raw.headers)
        # print(raw.text)
        # print("RESULT WAS JSON BUT NOT A DICT.")
        return None
    
    # The reply was a valid JSON dictionary...
    
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

def execute_d(di, verbose = False):
    return get_json_from_url(_API_URL + "venues/{}/stocks/{}/orders".format(di["venue"], di["stock"]), postdata = json.dumps(di), verbose = verbose)

def cancel(venue, symbol, id, verbose=False, require_ok=True):
    return get_json_from_url(_API_URL + "venues/{}/stocks/{}/orders/{}".format(venue, symbol, id), deletemethod = True, verbose = verbose, require_ok = require_ok)

def quote(venue, symbol, verbose=False):
    return get_json_from_url(_API_URL + "venues/{}/stocks/{}/quote".format(venue, symbol), verbose = verbose)

def orderbook(venue, symbol, verbose = False):
	return get_json_from_url(_API_URL + "venues/{}/stocks/{}".format(venue, symbol), verbose = verbose)


def parse_fills_from_response(response, verbose = False):

    # Parse (many) fills from a single cancel (or status) request and return the net change in my shares and my cents...

    return_dict = {"shares" : 0, "cents" : 0, "fills" : 0}        # These are deltas, which the calling function must add to its tally
    
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