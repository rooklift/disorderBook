import queue, re, threading, time
import SimpleWebSocketServer as swss

WS_Messages = queue.Queue()

TICKER = 1
EXECUTION = 2

ticker_clients = []
execution_clients = []

ticker_clients_lock = threading.Lock()
execution_clients_lock = threading.Lock()


class WebsocketMessage ():
    def __init__(self, account = None, venue = None, symbol = None, msgtype = None, msg = ""):
        self.account = account
        self.venue = venue
        self.symbol = symbol
        self.msgtype = msgtype
        self.msg = msg


class ConnectHandler(swss.WebSocket):

    def handleConnected(self):
        try:
            self.account, self.venue, self.symbol = re.search("/ws/(\S+)/venues/(\S+)/tickertape/stocks/(\S+)", str(self.headerbuffer, encoding = "utf-8")).group(1,2,3)
            assert(self.account and self.venue and self.symbol)
            self.websocket_type = TICKER
            with ticker_clients_lock:
                ticker_clients.append(self)
            return
        except:
            pass
            
        try:
            self.account, self.venue = re.search("/ws/(\S+)/venues/(\S+)/tickertape", str(self.headerbuffer, encoding = "utf-8")).group(1,2)
            assert(self.account and self.venue)
            self.symbol = None
            self.websocket_type = TICKER
            with ticker_clients_lock:
                ticker_clients.append(self)
            return
        except:
            pass
        
        try:
            self.account, self.venue, self.symbol = re.search("/ws/(\S+)/venues/(\S+)/executions/stocks/(\S+)", str(self.headerbuffer, encoding = "utf-8")).group(1,2,3)
            assert(self.account and self.venue and self.symbol)
            self.websocket_type = EXECUTION
            with execution_clients_lock:
                execution_clients.append(self)
            return
        except:
            pass
        
        try:
            self.account, self.venue = re.search("/ws/(\S+)/venues/(\S+)/executions", str(self.headerbuffer, encoding = "utf-8")).group(1,2)
            assert(self.account and self.venue)
            self.symbol = None
            self.websocket_type = EXECUTION
            with execution_clients_lock:
                execution_clients.append(self)
            return
        except:
            pass

        return      # Failed


    def handleClose(self):
        if self.websocket_type == TICKER:
            with ticker_clients_lock:
                ticker_clients.remove(self)
        elif self.websocket_type == EXECUTION:
            with execution_clients_lock:
                execution_clients.remove(self)
        else:
            pass


def start_websockets(ws_port):
    threading.Thread(target = message_sender_thread).start()
    
    server = swss.SimpleWebSocketServer('127.0.0.1', ws_port, ConnectHandler, selectInterval = 0.1)
    server.serveforever()


def message_sender_thread():

    while 1:
        msg_obj = WS_Messages.get()
        
        if msg_obj.msgtype == TICKER:
            with ticker_clients_lock:
                for c in ticker_clients:
                    if c.venue == msg_obj.venue and (c.symbol == msg_obj.symbol or c.symbol == None):
                        c.sendMessage(msg_obj.msg)
                        
        elif msg_obj.msgtype == EXECUTION:
            with execution_clients_lock:
                for c in execution_clients:
                    if c.account == msg_obj.account and c.venue == msg_obj.venue and (c.symbol == msg_obj.symbol or c.symbol == None):
                        c.sendMessage(msg_obj.msg)
                    
        WS_Messages.task_done()
