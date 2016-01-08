import random, threading, time
import stockfighter_minimal as sf

sf.set_web_url("http://127.0.0.1:8000/ob/api/")
sf.change_api_key("exb123456")

ACCOUNT = "EXB123456"
VENUE = "TESTEX"
SYMBOL = "FOOBAR"


def execute_randomly_forever(verbose = False):

    INFO = sf.Order()

    INFO.account = ACCOUNT
    INFO.venue = VENUE
    INFO.symbol = SYMBOL

    while 1:
        INFO.price = random.randint(4000, 6000)
        INFO.qty = random.randint(1, 100)
        INFO.orderType = random.choice(["limit", "limit", "limit", "limit", "market", "immediate-or-cancel", "fill-or-kill"])
        INFO.direction = random.choice(["buy", "sell"])
        
        result = sf.execute(INFO, verbose = verbose)



def stress_test():

    INFO = sf.Order()
    
    INFO.account = ACCOUNT
    INFO.venue = VENUE
    INFO.symbol = SYMBOL
    INFO.orderType = "limit"
    INFO.qty = 100
    
    for n in range(50):
        newthread = threading.Thread(target = execute_randomly_forever, daemon = False, kwargs={
                        "verbose" : True}
        )
        newthread.start()


if __name__ == "__main__":
    stress_test()

