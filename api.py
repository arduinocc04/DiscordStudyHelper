import logging
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

logger = logging.getLogger('API LOGGER')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(thread)d - %(message)s")
fileHandler = logging.FileHandler(filename="logs/information.log")
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)
streamHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

nest_asyncio.apply()

headers = {
    "User-Agent": f"DiscordBot ({REDIRECT_URI}, {API_VERSION})",
    "Authorization": f"Bot {TOKEN}"
}

class WebSocketAPI:
    def __init__(self, onMessage):#, onMessage) -> None:
        logger.debug('WebSocketAPI __init__')
        self.seq = None
        self.heartbeatAckReceived = True
        self.onMessageCallBack = onMessage
        self.sendProblemBuffer = []
        self.loop = None
        asyncio.run(self.init())

    async def init(self) -> None:
        logger.debug('WebsocketAPI init')
        await self.connect(),
        await self.sendIdentifyPayload()
        self.main()

    async def revive(self) -> None:
        logger.debug('WebsocketAPI revive')
        await self.connect()
        await self.sendResume()
        self.main()
        #await self.init()
    async def connect(self) -> None:
        logger.debug('WebsocketAPI connect')
        self.ws = await websockets.connect(GATEWAY_ENDPOINT)
        data = await self.ws.recv()
        data = json.loads(data)
        if data['op'] == 10:
            self.heartbeatInterval = data['d']['heartbeat_interval']
            logger.debug(f'heartbeatInterval: {self.heartbeatInterval}')
        else:
            logger.warning('WebsocketAPI Connection Failed')
            await self.revive()

    async def sendPayload(self, op:int, d:dict) -> None:
        logger.debug(f'WebsocketAPI sendPayload {op=} {d=}')
        toSend = {
            "op": op,
            "d":d
        }
        j = json.dumps(toSend)
        await self.ws.send(j)

    async def sendHeartbeat(self) -> None:
        logger.debug('WebsocketAPI sendHeartbeat')
        if not self.heartbeatAckReceived:
            await self.revive()
        await self.sendPayload(1, self.seq)
        self.heartbeatAckReceived = False

    async def heartbeat(self) -> None:
        while True:
            await self.sendHeartbeat()
            await asyncio.sleep(self.heartbeatInterval/1000)
    
    async def recv(self) -> None:
        while True:
            data = await self.ws.recv()
            data = json.loads(data)
            logger.info(f'WebsocketAPI data received\n{data}')
            if data['s'] != None:
                self.seq = data['s']
            if data['op'] == 0:
                if data['t'] == 'READY':
                    logger.debug('WebsocketAPI Ready')
                    self.sessionId = data['d']['session_id']
                elif data['t'] == 'RESUMED':
                    logger.info('WebsocketAPI Resumed')
                else:
                    self.onMessageCallBack(data)
            elif data['op'] == 1:
                logger.info('WebsocketAPI sendHeartbeatnow(op:1)')
                self.sendHeartbeat()
            elif data['op'] == 7:
                logger.info('WebsocketAPI reconnect(op:7)')
                await self.revive()
            elif data['op'] == 9:
                logger.warning('WebsocketAPI Invalid session')
                await self.init()
            elif data['op'] == 11:
                logger.debug('WebsocketAPI heartbeat ACK')
                self.heartbeatAckReceived = True

    def main(self) -> None:
        logger.debug('WebsocketAPI Main')
        self.loop = asyncio.get_event_loop()
        heartbeatTask = self.loop.create_task(self.heartbeat())
        recvTask = self.loop.create_task(self.recv())
        self.loop.run_forever()
    
    async def sendIdentifyPayload(self) -> None:
        logger.debug('WebsocketAPI SendIdentifyPayload')
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
    
    async def sendResume(self) -> None:
        logger.info('WebsocketAPI SendResume')
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
        logger.debug(f'HttpAPI sendInteractionMessage id:{interactionId} token:{interactionToken} message:{message}')
        interactionUrl = API_ENDPOINT + f'/interactions/{interactionId}/{interactionToken}/callback'
        data = {
            'type':4,
            'data': {
                'content': f"{message}"
            }
        }
        res = requests.post(interactionUrl, json=data, headers=headers)
        logger.debug(f'HttpAPI sendInteractionMessage res {res.status_code=} {res.text=}')

    def deleteOriginalInteraction(self, interactionToken:str):
        logger.debug(f'HttpAPI deleteOriginalInteraction token:{interactionToken}')
        interactionUrl = API_ENDPOINT + f'/webhooks/{CLIENT_ID}/{interactionToken}/messages/@original'
        res = requests.delete(interactionUrl, headers=headers)
        logger.debug(f'HttpAPI deleteOriginalInteraction res {res.status_code=} {res.text=}')

    def sendPicToChannel(self, url:str, channelId:int):
        logger.debug(f'HttpAPI sendPicToChannel url:{url} channelId:{channelId}')
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
        logger.debug(f'HttpAPI sendPicToChannel res {res.status_code=} {res.text=}')
    
    def delMessage(self, channelId:int, messageId:int):
        logger.debug(f'HttpAPI delMessage messageId:{messageId} channelId:{channelId}')
        interactionUrl = API_ENDPOINT + f'/channels/{channelId}/messages/{messageId}'
        res = requests.delete(interactionUrl, headers=headers)
        logger.debug(f'HttpAPI delMessage res {res.status_code=} {res.text=}')
    
    def createReaction(self, channelId:int, messageId:int, emoji:str):
        logger.debug(f'HttpAPI createReaction messageId:{messageId} channelId:{channelId} emoji:{emoji}')
        interactionUrl = API_ENDPOINT + f'/channels/{channelId}/messages/{messageId}/reactions/{emoji}/@me'
        res = requests.put(interactionUrl, headers=headers)
        logger.debug(f'HttpAPI createReaction res {res.status_code=} {res.text=}')
    
    #def makeChatInputTypeCommand(self, name:str, description:str, )
def f(m):
    pass
if __name__ == "__main__":
    a = WebSocketAPI(f)
