import json, random, time
import stockfighter_minimal as sf

account = "BLSHBOTS"
venue, symbol = "TESTEX", "FOOBAR"

sf.set_web_url("http://127.0.0.1:8000/ob/api/")
sf.change_api_key("blshkey")

def main():
    global account
    global venue
    global symbol
    
    orderType = "limit"
    last_id = None
    last_price = None
    active_ids = []
    myshares, mycents = 0, 0
    
    print("Waiting to see some prices before placing orders...")
    
    # The strategy of this stupid bot is:
    #
    # If we have positive shares, try to sell above current price
    # If we have negative shares, try to buy below current price
    
    while 1:
        try:
            last_price = sf.quote(venue, symbol)["last"]
        except:
            time.sleep(5)
            continue
        
        if len(active_ids) > 10:
            r = sf.cancel(venue, symbol, active_ids[0], verbose = True)
            if r:
                deltas = sf.parse_fills_from_response(r)
                myshares += deltas["shares"]
                mycents += deltas["cents"]
            print("\nShares: {}, Cents: {}, NAV: {} (current price: {})\n".format(myshares, mycents, myshares * last_price + mycents, last_price))
            active_ids.pop(0)
        
        qty = 100
        qty += random.randint(-25, 0)
        
        if myshares < 0:
            direction = "buy"
        elif myshares > 0:
            direction = "sell"
        else:
            direction = random.choice(["buy", "sell"])
        
        if direction == "buy":
            price = last_price - 50
        else:
            price = last_price + 50
        
        print("Placing order...")
        r = sf.execute_d(
                {
                    "price" : price,
                    "qty" : qty,
                    "direction" : direction,
                    "orderType" : orderType,
                    "account" : account,
                    "venue" : venue,
                    "stock" : symbol
                },
                verbose = False)
        
        try:
            active_ids.append(r["id"])
        except:
            print("Trouble getting ID.")
        
        time.sleep(0.5)
        


if __name__ == "__main__":
    main()
