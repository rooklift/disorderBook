import stockfighter_minimal as sf

sf.set_web_url("http://127.0.0.1:8000/ob/api/")

for price in range(5000):
    for n in range(20):
        order = {"price": price, "qty": 1, "direction": "buy", "orderType": "limit", "account": "EXB123456", "venue": "TESTEX", "stock": "FOOBAR"}
        sf.execute_d(order)
    print(price * n)

sf.orderbook("TESTEX", "FOOBAR", verbose = True)

input()
