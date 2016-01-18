# TODO: now that websockets are working, we really must adjust the
# quote on the fly rather than generating it every time it's needed.


import bisect
import datetime
import json

import disorderBook_ws


EXECUTION_TEMPLATE = '''
{{
  "ok": true,
  "account": "{}",
  "venue": "{}",
  "symbol": "{}",
  "order": {},
  "standingId": {},
  "incomingId": {},
  "price": {},
  "filled": {},
  "filledAt": "{}",
  "standingComplete": {},
  "incomingComplete": {}
}}
'''


def current_timestamp():
    ts = str(datetime.datetime.utcnow().isoformat())        # Thanks to medecau for this
    return ts


class Position():
    def __init__(self):
        self.cents = 0
        
        self._shares = 0
        self._min = 0
        self._max = 0
    
    @property
    def shares(self):
        return self._shares
    
    @shares.setter
    def shares(self, shares):
        self._shares = shares
        if shares < self._min:
            self._min = shares
        if shares > self._max:
            self._max = shares
    
    @property
    def minimum(self):
        return self._min
    
    @property
    def maximum(self):
        return self._max


class Order (dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    # All the comparisons are just for bisection insorting. Order should compare lower if it has higher
    # priority, which is confusing but whatever. It means high priority orders are sorted first.
    
    def __eq__(self, other):
        if self["price"] == other["price"] and self["ts"] == other["ts"]:
            return True
        else:
            return False
    
    def __lt__(self, other):
        if self["direction"] == "buy":
            if self["price"] > other["price"]:      # We beat the other price, so we are "less" (low is better)
                return True
            elif self["price"] < other["price"]:    # Other price beats us, so we are "more" (high is worse)
                return False
            elif self["ts"] < other["ts"]:          # Our order was first, so we are "less" (low is better)
                return True
            else:
                return False
        else:
            if self["price"] < other["price"]:      # We beat the other price, so we are "less" (low is better)
                return True
            elif self["price"] > other["price"]:    # Other price beats us, so we are "more" (high is worse)
                return False
            elif self["ts"] < other["ts"]:          # Our order was first, so we are "less" (low is better)
                return True
            else:
                return False
    
    def __le__(self, other):
        if self < other or self == other:
            return True
        else:
            return False
    
    def __gt__(self, other):
        if self <= other:
            return False
        else:
            return True
    
    def __ge__(self, other):
        if self > other or self == other:
            return True
        else:
            return False
    
    def __ne__(self, other):
        if not self == other:
            return True
        else:
            return False


# For the orderbook itself, the general plan is to keep a list of bids and a list of asks,
# always *kept* sorted (never sorted as a whole), with the top priority order first in line.
# Incoming orders can then just iterate through the list until they're finished crossing.

class OrderBook ():
    def __init__(self, venue, symbol, websockets_flag):
        self.venue = str(venue)
        self.symbol = str(symbol)
        self.websockets_flag = websockets_flag
        self.starttime = current_timestamp()
        self.bids = []
        self.asks = []
        self.id_lookup_table = dict()            # order id ---> order object
        self.account_order_lists = dict()        # account name ---> list of order objects
        self.next_id = 0
        self.quote = dict()
        self.positions = dict()
        
        self.init_quote()


    def account_from_order_id(self, id):
        try:
            return self.id_lookup_table[id]["account"]
        except KeyError:
            return None


    def cleanup_closed_bids(self):
        self.bids = [bid for bid in self.bids if bid["open"]]
        
    def cleanup_closed_asks(self):
        self.asks = [ask for ask in self.asks if ask["open"]]
        
    def cleanup_closed_orders(self):
        self.cleanup_closed_bids()
        self.cleanup_closed_asks()


    def get_book(self):
        ret = dict()
        ret["ok"] = True
        ret["venue"] = self.venue
        ret["symbol"] = self.symbol
        ret["bids"] = [{"price": order["price"], "qty": order["qty"], "isBuy": True} for order in self.bids]
        ret["asks"] = [{"price": order["price"], "qty": order["qty"], "isBuy": False} for order in self.asks]
        ret["ts"] = current_timestamp()
        return ret
    
    
    def get_status(self, id):
        return self.id_lookup_table[id]
    
    
    def get_all_orders(self, account):
        if account in self.account_order_lists:
            return {"ok": True, "venue": self.venue, "orders": self.account_order_lists[account]}
        else:
            return {"ok": True, "venue": self.venue, "orders": []}
    

    def get_quote(self):    # Used by the frontend for historical reasons
        return self.quote
    

    def init_quote(self):
        self.quote["ok"] = True
        self.quote["venue"] = self.venue
        self.quote["symbol"] = self.symbol
        
        self.quote["bidDepth"] = 0
        self.quote["bidSize"] = 0
        
        self.quote["askDepth"] = 0
        self.quote["askSize"] = 0
        
        self.quote["quoteTime"] = current_timestamp()

        
    def bid_size(self):
        if len(self.bids) == 0:
            return 0
        ret = 0
        bestprice = self.bids[0]["price"]
        for order in self.bids:
            if order["price"] == bestprice:
                ret += order["qty"]
            else:
                break
        return ret

        
    def ask_size(self):
        if len(self.asks) == 0:
            return 0
        ret = 0
        bestprice = self.asks[0]["price"]
        for order in self.asks:
            if order["price"] == bestprice:
                ret += order["qty"]
            else:
                break
        return ret


    def fok_can_buy(self, price, qty):
        avail = 0
        for standing in self.asks:
            if standing["price"] <= price:
                avail += standing["qty"]
                if avail >= qty:
                    break
            else:
                break                # Taking advantage of list sortedness

        if avail >= qty:
            return True
        else:
            return False


    def fok_can_sell(self, price, qty):
        avail = 0
        for standing in self.bids:
            if standing["price"] >= price:
                avail += standing["qty"]
                if avail >= qty:
                    break
            else:
                break                # Taking advantage of list sortedness

        if avail >= qty:
            return True
        else:
            return False
    
    
    def cancel_order(self, id):
        order = self.id_lookup_table[id]
        
        if order["open"]:
        
            qty_outstanding = order["qty"]
        
            order["qty"] = 0
            order["open"] = False
            self.cleanup_closed_orders()
            
            # Fix the quote...
            
            self.quote["quoteTime"] = current_timestamp()
            
            if order["direction"] == "buy":
                if self.bids:
                    self.quote["bidDepth"] -= qty_outstanding
                    
                    bestprice = self.bids[0]["price"]
                    
                    if order["price"] == bestprice:
                        self.quote["bidSize"] -= qty_outstanding
                    elif order["price"] > bestprice:                # Best order was cancelled
                        self.quote["bidSize"] = self.bid_size()
                        self.quote["bid"] = self.bids[0]["price"]
                else:
                    self.quote["bidDepth"] = 0
                    self.quote["bidSize"] = 0
                    if "bid" in self.quote:
                        self.quote.pop("bid")
            else:
                if self.asks:
                    self.quote["askDepth"] -= qty_outstanding
                    
                    bestprice = self.asks[0]["price"]
                    
                    if order["price"] == bestprice:
                        self.quote["askSize"] -= qty_outstanding
                    elif order["price"] < bestprice:                # Best order was cancelled
                        self.quote["askSize"] = self.ask_size()
                        self.quote["ask"] = self.asks[0]["price"]
                else:
                    self.quote["askDepth"] = 0
                    self.quote["askSize"] = 0
                    if "ask" in self.quote:
                        self.quote.pop("ask")
            
        if self.websockets_flag:
            self.create_ticker_message()

        return order
    
    
    def create_ticker_message(self):
        msg = '{"ok": true, "quote": ' + json.dumps(self.quote) + '}'
        ticker_msg_obj = disorderBook_ws.WebsocketMessage(account = "NONE", venue = self.venue, symbol = self.symbol, msg = msg)
        disorderBook_ws.ticker_messages.put(ticker_msg_obj)
    
    
    def parse_order(self, data):
        # We now assume symbol and venue are correct for this book. Caller's responsibility.
        # The caller should be prepared to handle KeyError, TypeError and ValueError
        
        # Official Stockfighter recognises lowercase ordertype:
        try:
            orderType = data["orderType"]
        except KeyError:
            orderType = data["ordertype"]    # Could re-raise KeyError

        # Official stockfighter accepts "fok" and "ioc" as legit orderType:
        if orderType == "fok":
            orderType = "fill-or-kill"
        elif orderType == "ioc":
            orderType = "immediate-or-cancel"
        
        # The following can raise KeyError:
        account = data["account"]
        price = data["price"]
        qty = data["qty"]
        direction = data["direction"]
        
        # Official SF sets price to 0 on market orders:
        if orderType == "market":
            price = 0

        price = int(price)    # Could raise TypeError
        qty = int(qty)        # Could raise TypeError
        
        if price < 0:
            raise ValueError
        if qty <= 0:
            raise ValueError
        if direction not in ("buy", "sell"):
            raise ValueError
        if orderType not in ("limit", "market", "fill-or-kill", "immediate-or-cancel"):
            raise ValueError

        id = self.next_id
        self.next_id += 1
        
        order = Order(
                         ok = True,
                      venue = self.venue,
                     symbol = self.symbol,
                  direction = direction,
                originalQty = qty,
                        qty = qty,
                      price = price,
                  orderType = orderType,
                         id = id,
                    account = account,
                         ts = current_timestamp(),
                      fills = list(),
                totalFilled = 0,
                       open = True
                            )
        
        self.id_lookup_table[id] = order            # So we can find it for status/cancel
        
        if account not in self.account_order_lists:
            self.account_order_lists[account] = list()
        self.account_order_lists[account].append(order)        # So we can list all an account's orders
            
        # Limit, Market, and IOC orders are easy...
        
        if orderType in ("limit", "immediate-or-cancel", "market"):
            self.run_order(order)
            
        # FOK orders are slightly tricky...
        
        elif orderType == "fill-or-kill":
            if direction == "buy":
                if self.fok_can_buy(price = price, qty = qty):
                    self.run_order(order)
            else:
                if self.fok_can_sell(price = price, qty = qty):
                    self.run_order(order)
        
        # Limit orders may have been placed on the book, the rest may need to be closed...
        
        if order["orderType"] != "limit":
            order["qty"] = 0
            order["open"] = False
        
        return order


    def run_order(self, incoming):
    
        incomingprice = incoming["price"]
        timestamp = current_timestamp()
        
        lastprice = 0
        lastqty = 0
    
        if incoming["direction"] == "sell":
            for standing in self.bids:
                if standing["price"] >= incomingprice or incoming["orderType"] == "market":
                    lastprice, lastqty = self.order_cross(standing = standing, incoming = incoming, timestamp = timestamp)
                    if incoming["qty"] == 0:
                        break
                else:
                    break               # Taking advantage of the sortedness of the book's lists
            self.cleanup_closed_bids()
        else:
            for standing in self.asks:
                if standing["price"] <= incomingprice or incoming["orderType"] == "market":
                    lastprice, lastqty = self.order_cross(standing = standing, incoming = incoming, timestamp = timestamp)
                    if incoming["qty"] == 0:
                        break
                else:
                    break               # Taking advantage of the sortedness of the book's lists
            self.cleanup_closed_asks()

        # Limit orders rest on the book (also must adjust quote for their half of the book)....
            
        if incoming["orderType"] == "limit":
            if incoming["open"]:
                if incoming["direction"] == "buy":
                
                    if self.bids:
                        old_bestprice = self.bids[0]["price"]
                    else:
                        old_bestprice = None
                
                    bisect.insort(self.bids, incoming)
                    
                    self.quote["bidDepth"] += incoming["qty"]
                    
                    if incoming["price"] == old_bestprice:
                        self.quote["bidSize"] += incoming["qty"]
                        
                    elif old_bestprice is None or incoming["price"] > old_bestprice:        # New order is best
                        self.quote["bidSize"] = incoming["qty"]
                        self.quote["bid"] = incoming["price"]
                        
                else:
                
                    if self.asks:
                        old_bestprice = self.asks[0]["price"]
                    else:
                        old_bestprice = None
                        
                    bisect.insort(self.asks, incoming)
                    
                    self.quote["askDepth"] += incoming["qty"]
                    
                    if incoming["price"] == old_bestprice:
                        self.quote["askSize"] += incoming["qty"]
                        
                    elif old_bestprice is None or incoming["price"] < old_bestprice:        # New order is best
                        self.quote["askSize"] = incoming["qty"]
                        self.quote["ask"] = incoming["price"]
        
        self.quote["quoteTime"] = timestamp         # Always do this
        
        # Check if there were any crosses; if so we need to do more quote setting...
        
        if incoming["totalFilled"]:
            if incoming["direction"] == "sell":
                if self.bids:
                    self.quote["bid"] = self.bids[0]["price"]
                    self.quote["bidSize"] = self.bid_size()
                    self.quote["bidDepth"] -= incoming["totalFilled"]
                else:
                    if "bid" in self.quote:
                        self.quote.pop("bid")
                    self.quote["bidSize"] = 0
                    self.quote["bidDepth"] = 0
            else:
                if self.asks:
                    self.quote["ask"] = self.asks[0]["price"]
                    self.quote["askSize"] = self.ask_size()
                    self.quote["askDepth"] -= incoming["totalFilled"]
                else:
                    if "ask" in self.quote:
                        self.quote.pop("ask")
                    self.quote["askSize"] = 0
                    self.quote["askDepth"] = 0
            
            self.quote["last"] = lastprice
            self.quote["lastSize"] = lastqty
            self.quote["lastTrade"] = timestamp

        # And fire off a websocket message...
            
        if self.websockets_flag:
            self.create_ticker_message()
        
        return incoming
    
    
    def order_cross(self, *, standing, incoming, timestamp):        # Force named args to not get it wrong
        quantity = min(standing["qty"], incoming["qty"])
        standing["qty"] -= quantity
        standing["totalFilled"] += quantity
        incoming["qty"] -= quantity
        incoming["totalFilled"] += quantity
        
        price = standing["price"]
        
        fill = dict(price = price, qty = quantity, ts = timestamp)
        
        for o in standing, incoming:
            o["fills"].append(fill)
            if o["qty"] == 0:
                o["open"] = False
        
        # All the following is just to track "score" for PvP (or PvE) purposes:
        
        s_account = standing["account"]
        i_account = incoming["account"]
        
        if s_account not in self.positions:
            self.positions[s_account] = Position()
        if i_account not in self.positions:
            self.positions[i_account] = Position()
        
        s_pos = self.positions[s_account]
        i_pos = self.positions[i_account]
        
        if standing["direction"] == "buy":
            s_pos.shares += quantity
            s_pos.cents -= quantity * price
            i_pos.shares -= quantity
            i_pos.cents += quantity * price
        else:
            s_pos.shares -= quantity
            s_pos.cents += quantity * price
            i_pos.shares += quantity
            i_pos.cents -= quantity * price
        
        # And the following is for the executions websocket:
        
        if self.websockets_flag:
        
            standing_execution_msg = EXECUTION_TEMPLATE.format(
                    standing["account"], self.venue, self.symbol, json.dumps(standing),
                    standing["id"], incoming["id"], price, quantity, timestamp,
                    "false" if standing["open"] else "true", "false" if incoming["open"] else "true")

            incoming_execution_msg = EXECUTION_TEMPLATE.format(
                    incoming["account"], self.venue, self.symbol, json.dumps(incoming),
                    standing["id"], incoming["id"], price, quantity, timestamp,
                    "false" if standing["open"] else "true", "false" if incoming["open"] else "true")

            standing_msg_obj = disorderBook_ws.WebsocketMessage(account = standing["account"], venue = self.venue, symbol = self.symbol, msg = standing_execution_msg)
            incoming_msg_obj = disorderBook_ws.WebsocketMessage(account = incoming["account"], venue = self.venue, symbol = self.symbol, msg = incoming_execution_msg)
            
            disorderBook_ws.execution_messages.put(standing_msg_obj)
            disorderBook_ws.execution_messages.put(incoming_msg_obj)
        
        return (price, quantity)
