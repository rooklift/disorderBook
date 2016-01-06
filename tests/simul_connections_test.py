import threading, time, queue, random
import stockfighter_minimal as sf

sf.set_web_url("http://127.0.0.1:8000/ob/api/")
sf.change_api_key("exb123456")

ACCOUNT = "EXB123456"
VENUE = "TESTEX"
SYMBOL = "FOOBAR"


PRINT_LOCK = threading.Lock()


def execute_from_queue(task_queue, result_queue, verbose = False):
	order = task_queue.get()
	result = sf.execute(order, verbose = verbose)
	result_queue.put(result)
	task_queue.task_done()
	return


def stress_test():

	INFO = sf.Order()
	
	INFO.account = ACCOUNT
	INFO.venue = VENUE
	INFO.symbol = SYMBOL
	INFO.orderType = "limit"
	INFO.qty = 100
	
	task_queue = queue.Queue()
	result_queue = queue.Queue()
	
	while 1:
	
		for n in range(20):
		
			INFO.price = random.randint(4000, 6000)
			INFO.direction = random.choice(["buy", "sell"])
			
			task_queue.put(INFO.copy())
		
			newthread = threading.Thread(target = execute_from_queue, daemon = True, kwargs={
						"task_queue" : task_queue,
						"result_queue" : result_queue,
						"verbose" : True}
			)
			newthread.start()

		task_queue.join()
		with PRINT_LOCK:
			print("Sleeping for 5....")
		time.sleep(5)


if __name__ == "__main__":
	stress_test()

