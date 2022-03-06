import requests
import asyncio
import websockets
import nest_asyncio
import json


API_VERSION = 8
API_ENDPOINT = f'https://discord.com/api/v{API_VERSION}'
GATEWAY_ENDPOINT = f"wss://gateway.discord.gg/?v={API_VERSION}&encoding=json"
with open('clientId.txt', 'r') as f:
    CLIENT_ID = f.readline().rstrip()
with open('clientSecret.txt', 'r') as f:
    CLIENT_SECRET = f.readline().rstrip()
with open('token.txt', 'r') as f:
    TOKEN = f.readline().rstrip()
with open('urI.txt', 'r') as f:
    REDIRECT_URI = f.readline().rstrip()

nest_asyncio.apply()

headers = {
    "User-Agent": f"DiscordBot ({REDIRECT_URI}, {API_VERSION})",
    "Authorization": f"Bot {TOKEN}"
}

class WebSocket:
    def __init__(self) -> None:
        self.seq = "null"
        self.heartbeatAckReceived = True
        pass

    async def init(self):
        await self.connect(),
        await self.sendIdentifyPayload()
        self.main()

    async def revive(self):
        await self.disconnect(),
        await self.connect(),
        await self.sendResume()
        self.main()

    async def connect(self):
        self.ws = await websockets.connect(GATEWAY_ENDPOINT)
        data = await self.ws.recv()
        data = json.loads(data)
        if data['op'] == 10:
            self.heartbeatInterval = data['d']['heartbeat_interval']
            print(self.heartbeatInterval)
        else:
            print("Connection Failed.")
            await self.revive()

    async def disconnect(self):
        self.loop.close()
        await self.ws.close()
        pass
    
    async def sendPayload(self, op:int, d:dict):
        toSend = {
            "op": op,
            "d":d
        }
        j = json.dumps(toSend)
        await self.ws.send(j)

    async def sendHeartbeat(self):
        if not self.heartbeatAckReceived:
            await self.revive()
        await self.sendPayload(1, self.seq)
        self.heartbeatAckReceived = False
        print('heartbeat send!')

    async def heartbeat(self):
        while True:
            await self.sendHeartbeat()
            await asyncio.sleep(self.heartbeatInterval/1000)
    
    async def recv(self):
        while True:
            data = await self.ws.recv()
            data = json.loads(data)
            print(data)
            print(f"{data['op']=}")
            if data['s'] != None:
                self.seq = data['s']
            if data['op'] == 0:
                if data['t'] == 'READY':
                    print('ready!')
            elif data['op'] == 1:
                self.sendHeartbeat()
            elif data['op'] == 9:
                print('INVALID SESSION!')
                self.revive()
            elif data['op'] == 11:
                self.heartbeatAckReceived = True

    def main(self):
        self.loop = asyncio.get_event_loop()
        heartbeatTask = self.loop.create_task(self.heartbeat())
        recvTask = self.loop.create_task(self.recv())
        self.loop.run_forever()

    
    async def sendIdentifyPayload(self):
        await self.sendPayload(
            2, 
            {
                "token": f"{TOKEN}",
                "intents": 15915,
                "properties": {
                    "$os": "linux",
                    "$browser": "disco",
                    "$device": "disco"
                }
            }
        )
        print('identifypayload sended!')
    
    async def sendResume(self):
        await self.sendPayload(
            6,
            {
                "token": f"{TOKEN}",
                "seq": f"{self.seq}",
                "session_id":f"{self.sessionId}"
            }
        )
if __name__ == "__main__":
    a = WebSocket()
    asyncio.run(a.init())
    #asyncio.run(a.sendIdentifyPayload())
