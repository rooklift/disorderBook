# The strategy of this stupid bot is:
#
# If current price is below recent average, try to buy at even lower price
# If current price is above recent average, try to sell at even higher price
# But try to not go too far outside the position range -500 to 500

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

	account = "LH" + str(random.randint(0,999999999))

	orderType = "limit"

	last_id = None
	recent_prices = []
	
	active_ids = []
	
	myshares, mycents = 0, 0
	
	print("Waiting to see some prices before starting...\n")
	
	while 1:
		try:
			last_price = sf.quote(venue, symbol)["last"]
			recent_prices.append(last_price)
		except:
			time.sleep(5)
		
		if len(recent_prices) > 20:
			recent_prices = recent_prices[-20:]
		else:
			time.sleep(1)
			continue
		
		# So the following only happens when enough prices have been seen...
		
		if len(active_ids) > 10:
			r = sf.cancel(venue, symbol, active_ids[0], verbose = True)
			if r:
				deltas = sf.parse_fills_from_response(r)
				myshares += deltas["shares"]
				mycents += deltas["cents"]
			print("\nShares: {}, Cents: {}, NAV: {} (current price: {})\n".format(myshares, mycents, myshares * last_price + mycents, last_price))
			active_ids.pop(0)
		
		average = sum(recent_prices) // len(recent_prices)
		
		qty = 200
		qty += random.randint(-50, 50)
		
		if last_price < average:
			if myshares < 500:
				direction = "buy"
			else:
				direction = "sell"
		else:
			if myshares > -500:
				direction = "sell"
			else:
				direction = "buy"

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
