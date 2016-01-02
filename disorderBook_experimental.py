from bottle import route, request, run
import disorderBook_book as book
import json


all_venues = dict()        # dict: venue string ---> dict: stock string ---> OrderBook objects


def response_from_exception(e):
    di = dict()
    di["ok"] = False
    di["error"] = str(e)
    return di


def create_book_if_needed(venue, symbol):
    if venue not in all_venues:
        all_venues[venue] = dict()
        
    if symbol not in all_venues[venue]:
        all_venues[venue][symbol] = book.OrderBook(venue, symbol)

# ------------------------------------------------------------------------------

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
route("/ob/api/venues/<venue>", "GET", stocklist)


@route("/ob/api/venues/<venue>/stocks/<symbol>", "GET")
def orderbook(venue, symbol):
    
    create_book_if_needed(venue, symbol)

    try:
        ret = all_venues[venue][symbol].get_book()
        assert(ret)
        return ret
    except Exception as e:
        ret = response_from_exception(e)
        return ret


@route("/ob/api/venues/<venue>/stocks/<symbol>/quote", "GET")
def quote(venue, symbol):
    
    create_book_if_needed(venue, symbol)
        
    try:
        ret = all_venues[venue][symbol].get_quote()
        assert(ret)
        return ret
    except Exception as e:
        ret = response_from_exception(e)
        return ret
    
    
@route("/ob/api/venues/<venue>/stocks/<symbol>/orders/<id>", "GET")
def status(venue, symbol, id):
    
    create_book_if_needed(venue, symbol)
    
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

    create_book_if_needed(venue, symbol)
    
    try:
        ret = all_venues[venue][symbol].get_all_orders(account)
        assert(ret)
        return ret
    except Exception as e:
        ret = response_from_exception(e)
        return ret


@route("/ob/api/venues/<venue>/stocks/<symbol>/orders/<id>", "DELETE")
def cancel(venue, symbol, id):
    
    create_book_if_needed(venue, symbol)
    
    try:
        ret = all_venues[venue][symbol].cancel_order(id)
        assert(ret)
        return ret
    except Exception as e:
        ret = response_from_exception(e)
        return ret
    

@route("/ob/api/venues/<venue>/stocks/<symbol>/orders", "POST")
def make_order(venue, symbol):
    request.form.get('var')  # http://bottlepy.org/docs/dev/tutorial.html#request-data
    
    try:
        data = str(request.body, encoding="ascii")
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
        
        create_book_if_needed(venue, symbol)
        
        ret = all_venues[venue][symbol].parse_order(data)
        assert(ret)
        return ret
    except Exception as e:
        ret = response_from_exception(e)
        return ret




@route("/ob/api/venues/:venue/stocks/:stock/orders/:id/cancel", "POST")        # Alternate cancel method, for people without DELETE
def cancel_via_post(venue, symbol, id):
    
    create_book_if_needed(venue, symbol)
    
    try:
        ret = all_venues[venue][symbol].cancel_order(id)
        assert(ret)
        return ret
    except Exception as e:
        ret = response_from_exception(e)
        return ret


    


@route("/")
def home():
    return"""
    <pre>
    Oh, hay!
    
    Ask questions on slack, Amtiskaw "promised" to answer everything.
    </pre>
    """

run(host="0.0.0.0", port=8000)
