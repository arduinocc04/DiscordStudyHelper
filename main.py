import api

def onMessage(data):
    print(data)

if __name__ == '__main__':
    app = api.WebSocketAPI(onMessage=onMessage)