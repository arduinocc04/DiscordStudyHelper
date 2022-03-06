from email import header
import requests
import asyncio
import websockets
import nest_asyncio
import json
import typing
import time
import os

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
with open('testguild.txt', 'r') as f:
    GUILD = f.readline().rstrip()

nest_asyncio.apply()

headers = {
    "User-Agent": f"DiscordBot ({REDIRECT_URI}, {API_VERSION})",
    "Authorization": f"Bot {TOKEN}"
}

class WebSocketAPI:
    def __init__(self, onMessage):#, onMessage) -> None:
        self.seq = None
        self.heartbeatAckReceived = True
        self.onMessageCallBack = onMessage
        self.sendProblemBuffer = []
        self.loop = None
        asyncio.run(self.init())

    async def init(self) -> None:
        await self.connect(),
        await self.sendIdentifyPayload()
        self.main()

    async def revive(self) -> None:
        """
        await self.connect()
        await self.sendResume()
        self.main()
        """
        await self.init()
    async def connect(self) -> None:
        self.ws = await websockets.connect(GATEWAY_ENDPOINT)
        data = await self.ws.recv()
        data = json.loads(data)
        if data['op'] == 10:
            self.heartbeatInterval = data['d']['heartbeat_interval']
            print(self.heartbeatInterval)
        else:
            print("Connection Failed.")
            await self.revive()

    async def sendPayload(self, op:int, d:dict) -> None:
        toSend = {
            "op": op,
            "d":d
        }
        j = json.dumps(toSend)
        await self.ws.send(j)

    async def sendHeartbeat(self) -> None:
        if not self.heartbeatAckReceived:
            await self.revive()
        await self.sendPayload(1, self.seq)
        self.heartbeatAckReceived = False
        print('heartbeat send!')

    async def heartbeat(self) -> None:
        while True:
            await self.sendHeartbeat()
            await asyncio.sleep(self.heartbeatInterval/1000)
    
    async def recv(self) -> None:
        while True:
            data = await self.ws.recv()
            data = json.loads(data)
            print(data)
            if data['s'] != None:
                self.seq = data['s']
            if data['op'] == 0:
                if data['t'] == 'READY':
                    print('ready!')
                    self.sessionId = data['d']['session_id']
                elif data['t'] == 'RESUMED':
                    print('resumed!')
                else:
                    self.onMessageCallBack(data)
            elif data['op'] == 1:
                print('SEND HEARTBEAT NOW')
                self.sendHeartbeat()
            elif data['op'] == 7:
                await self.revive()
            elif data['op'] == 9:
                print('INVALID SESSION!')
                await self.init()
            elif data['op'] == 11:
                self.heartbeatAckReceived = True

    def main(self) -> None:
        self.loop = asyncio.get_event_loop()
        heartbeatTask = self.loop.create_task(self.heartbeat())
        recvTask = self.loop.create_task(self.recv())
        self.loop.run_forever()
    
    async def sendIdentifyPayload(self) -> None:
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
    
    async def sendResume(self) -> None:
        await self.sendPayload(
            6,
            {
                "token": f"{TOKEN}",
                "seq": self.seq,
                "session_id":f"{self.sessionId}"
            }
        )

class HttpAPI:
    def __init__(self, guild=None):
        pass
    
    def sendInteractionMessage(self, interactionId:int, interactionToken:str, message:str):
        interactionUrl = API_ENDPOINT + f'/interactions/{interactionId}/{interactionToken}/callback'
        data = {
            'type':4,
            'data': {
                'content': f"{message}"
            }
        }
        requests.post(interactionUrl, json=data, headers=headers)

    def deleteOriginalInteraction(self, interactionToken:str):
        interactionUrl = API_ENDPOINT + f'/webhooks/{CLIENT_ID}/{interactionToken}/messages/@original'
        requests.delete(interactionUrl, headers=headers)

    def sendPicToChannel(self, url:str, channelId:int):
        interactionUrl = API_ENDPOINT + f'/channels/{channelId}/messages'
        data = {
          "embeds": [{
            "type": 'image',
            "image": {
                "url": url,
                'content_type': "image/jpeg"
            }
          }]
        }
        res = requests.post(interactionUrl, json=data, headers=headers)
        print(f'{res.text=}')
    
    def delMessage(self, channelId:int, messageId:int):
        interactionUrl = API_ENDPOINT + f'/channels/{channelId}/messages/{messageId}'
        requests.delete(interactionUrl, headers=headers)
    
    def createReaction(self, channelId:int, messageId:int, emoji:str):
        interactionUrl = API_ENDPOINT + f'/channels/{channelId}/messages/{messageId}/reactions/{emoji}/@me'
        res = requests.put(interactionUrl, headers=headers)
        print(f'crreaction {res.status_code=}')
    
    #def makeChatInputTypeCommand(self, name:str, description:str, )
def f(m):
    pass
if __name__ == "__main__":
    a = WebSocketAPI(f)
