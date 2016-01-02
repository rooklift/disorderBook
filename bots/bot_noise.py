import json, random, time
import stockfighter_minimal as sf

# Override the default venue and symbol with DEFAULT_STOCK.txt
# containing a single line in format: "FOOEX DOGS" (no quotes)

def main():
	try:
		with open("DEFAULT_STOCK.txt") as infile:
			venue, symbol = infile.readline().split()
	except:
		venue, symbol = "BUYEX", "DOGS"

	account = "EXB123456"			# "NZ" + str(random.randint(0,999999999))

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

		time.sleep(0.5)
		if len(all_orders) > 10:
			id = all_orders.pop(0)
			sf.cancel(venue, symbol, id, verbose = True)


if __name__ == "__main__":
	main()
