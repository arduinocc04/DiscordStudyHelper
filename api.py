import logging
import requests
import asyncio
import websockets
import nest_asyncio
import json

API_VERSION = 8
OS_NAME = 'linux'
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
streamHandler.setLevel(logging.DEBUG)
streamHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

nest_asyncio.apply()

headers = {
    "User-Agent": f"DiscordBot ({REDIRECT_URI}, {API_VERSION})",
    "Authorization": f"Bot {TOKEN}"
}

class WebSocketAPI:
    def __init__(self, onMessage) -> None:
        logger.debug('WebSocketAPI __init__')
        self.seq = None
        self.heartbeatAckReceived = True
        self.onMessageCallBack = onMessage
        asyncio.run(self.init())
        self.main()

    async def init(self) -> None:
        logger.debug('WebsocketAPI init')
        await self.connect()
        await self.sendIdentifyPayload()

    async def revive(self) -> None:
        logger.debug('WebsocketAPI revive')
        await self.connect()
        await self.sendResume()

    async def connect(self) -> None:
        logger.debug('WebsocketAPI connect')
        try:
            self.ws = await websockets.connect(GATEWAY_ENDPOINT, ping_timeout=None, ping_interval=None)
        except websockets.exceptions.ConnectionClosedError:
            self.revive()
        data = await self.ws.recv()
        data = json.loads(data)
        if data['op'] == 10:
            self.heartbeatInterval = data['d']['heartbeat_interval']
            logger.debug(f'heartbeatInterval: {self.heartbeatInterval}')
        else:
            logger.info('WebsocketAPI Connection Failed')
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
            logger.debug(f'WebsocketAPI data received\n{data}')
            if data['s'] != None:
                self.seq = data['s']

            if data['op'] == 0:
                if data['t'] == 'READY':
                    logger.info('WebsocketAPI Ready')
                    self.sessionId = data['d']['session_id']
                elif data['t'] == 'RESUMED':
                    logger.info('WebsocketAPI Resumed')
                else:
                    t = data['t']
                    logger.info(f'WebsocketAPI {t}')
                    self.onMessageCallBack(data)
            elif data['op'] == 1:
                logger.info('WebsocketAPI sendHeartbeatnow(op:1)')
                self.sendHeartbeat()
            elif data['op'] == 7:
                logger.info('WebsocketAPI reconnect(op:7)')
                await self.revive()
            elif data['op'] == 9:
                logger.info('WebsocketAPI Invalid session')
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
                    "$os": OS_NAME,
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
        self.GUILD = guild

    def getGuildMembers(self, guildId:int) -> dict:
        logger.debug(f'HttpAPI getGuildMembers guildId:{guildId}')
        interactionUrl = API_ENDPOINT + f'/guilds/{guildId}/members?limit=1000'
        res = requests.get(interactionUrl, headers=headers)
        logger.debug(f'HttpAPI getGuildMembers res {res.status_code=} {res.text=}')
        return res.json()
    
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

    def sendMessageToChannel(self, message:str, channelId:int):
        logger.debug(f'HttpAPI sendMessageToChannel message:{message} channelId:{channelId}')
        interactionUrl = API_ENDPOINT + f'/channels/{channelId}/messages'
        data = {
          "content": message
        }
        res = requests.post(interactionUrl, json=data, headers=headers)
        logger.info(f'HttpAPI sendMessageToChannel res {res.status_code=} {res.text=}')

    def replyMessage(self, channelId:int, messageId:int):
        logger.debug(f'HttpAPI replyMessage messageId: {messageId}')
        interactionUrl = API_ENDPOINT + f'/channels/{channelId}/messages'
        data = {
          "content": "",
          "message_reference": {
              "message_id": messageId
          }
        }
        res = requests.post(interactionUrl, json=data, headers=headers)
        logger.info(f'HttpAPI replyMessage res {res.status_code=} {res.text=}')

    def sendPicToChannel(self, url:str, channelId:int):
        logger.debug(f'HttpAPI sendPicToChannel url:{url} channelId:{channelId}')
        interactionUrl = API_ENDPOINT + f'/channels/{channelId}/messages'
        data = {
          "embeds": [{
            "type": 'image',
            "image": {
                "url": url,
                'content_type': "image/jpeg"
            },
          }],
          "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "label": "Solved",
                            "style": 1,
                            "custom_id": 'solve_button'
                        },
                        {
                            "type": 2,
                            "label": "Unsolved",
                            "style": 1,
                            "custom_id": 'unsolve_button'
                        },
                        {
                            "type": 2,
                            "label": "Bookmark",
                            "style": 1,
                            "custom_id": 'bookmark_button'
                        }
                    ]
                }
            ]
        }
        res = requests.post(interactionUrl, json=data, headers=headers)
        logger.info(f'HttpAPI sendPicToChannel res {res.status_code=} {res.text=}')
    
    def sendPicToChannelWithMentionAndContent(self, url:str, channelId:int, mention:str, message:str):
        logger.debug(f'HttpAPI sendPicToChannelWithMentionAndContent url:{url} channelId:{channelId}')
        interactionUrl = API_ENDPOINT + f'/channels/{channelId}/messages'
        data = {
          "content": f'<@{mention}> {message}',
          "allowed_mentions": {
              "parse": ["users"]
          },
          "embeds": [{
            "type": 'image',
            "image": {
                "url": url,
                'content_type': "image/jpeg",
            },
          }],
        }
        res = requests.post(interactionUrl, json=data, headers=headers)
        logger.info(f'HttpAPI sendPicToChannelWithMentionAndContent res {res.status_code=} {res.text=}')
    
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

def f(m):
    pass
if __name__ == "__main__":
    a = WebSocketAPI(f)
