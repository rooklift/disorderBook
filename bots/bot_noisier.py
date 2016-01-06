import json, random, threading, time
import stockfighter_minimal as sf

account = "NOISEBOTS"
venue, symbol = "TESTEX", "FOOBAR"

sf.set_web_url("http://127.0.0.1:8000/ob/api/")
sf.change_api_key("noisekey")

def make_bots():
    for n in range(6):
        newthread = threading.Thread(target = noise, args=(account, venue, symbol))
        newthread.start()

def noise(account, venue, symbol):
    
    orderType = "limit"
    all_orders = []

    while 1:
        try:
            price = sf.quote(venue, symbol)["last"]
            if price == 0:
                price = 5000
        except:
            price = 5000
        price += random.randint(-100, 100)
        qty = 100
        qty += random.randint(-50, 50)
        direction = random.choice(["buy", "sell"])
        
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
                verbose = True)
        try:
            id = r["id"]
            all_orders.append(id)
        except:
            print("Trouble getting ID.")

        time.sleep(random.uniform(0.3, 0.7))
        if len(all_orders) > 10:
            id = all_orders.pop(0)
            sf.cancel(venue, symbol, id, verbose = True)
        
if __name__ == "__main__":
    make_bots()
