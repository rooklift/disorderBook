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
	last_time = time.clock()
	recent_prices = []
	
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
		
		if time.clock() - last_time < 5:
			time.sleep(1)
			continue
		
		# At this point we know we have 20 recent prices stored,
		# and our last order was placed 5 seconds ago.
		
		if last_id:
			r = sf.cancel(venue, symbol, last_id, verbose = True)
			deltas = sf.parse_fills_from_response(r)
			myshares += deltas["shares"]
			mycents += deltas["cents"]
			print("\nShares: {}, Cents: {}, NAV: {} (current price: {})\n".format(myshares, mycents, myshares * last_price + mycents, last_price))
			last_id = None
		
		average = sum(recent_prices) // len(recent_prices)
		
		qty = 200
		qty += random.randint(-50, 50)
		
		if last_price < average:
			direction = "buy"
			price = last_price - 50
		else:
			direction = "sell"
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
		
		last_time = time.clock()
		
		try:
			last_id = r["id"]
		except:
			print("Trouble getting ID.")
		


if __name__ == "__main__":
	main()
