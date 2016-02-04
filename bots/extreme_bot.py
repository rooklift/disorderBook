import json, random, time
import stockfighter_minimal as sf

account = "EXTREMEBOT"
venue, symbol = "TESTEX", "FOOBAR"

sf.set_web_url("http://127.0.0.1:8000/ob/api/")
sf.change_api_key("noisekey")

def main():
    global account
    global venue
    global symbol

    orderType = "limit"
    all_orders = []

    while 1:
        price = random.randint(0, 2 ** 31 - 1)
        qty = random.randint(1, 2 ** 31 - 1)
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
    main()
