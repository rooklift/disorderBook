import time, random
import stockfighter_minimal as sf


sf.set_web_url("http://127.0.0.1:8000/ob/api/")
sf.change_api_key("exb123456")

ACCOUNT = "EXB123456"
VENUE = "TESTEX"
SYMBOL = "FOOBAR"

SEED = 155176
TEST_TIME = 30

random.seed(SEED)




INFO = sf.Order()

INFO.account = ACCOUNT
INFO.venue = VENUE
INFO.symbol = SYMBOL

# Clear the book...

INFO.qty = 9999999
INFO.orderType = "market"
INFO.direction = "buy"
INFO.price = 0

sf.execute(INFO)

INFO.direction = "sell"
sf.execute(INFO)

starttime = time.time()
n = 0

print("Running for {} seconds...".format(TEST_TIME))

while 1:
	INFO.price = random.randint(1, 5000)
	INFO.qty = random.randint(1, 100)
	INFO.direction = random.choice(["buy", "sell"])
	INFO.orderType = random.choice(["limit", "limit", "limit", "limit", "market", "immediate-or-cancel", "fill-or-kill"])
	res = sf.execute(INFO)
	n += 1
	if time.time() - starttime > TEST_TIME:
		break

print("{} orders placed in {} seconds".format(n, TEST_TIME))
print("= {} per second".format(n // TEST_TIME))


input()


