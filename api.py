import requests
import asyncio
import websockets
import nest_asyncio
import json
import typing
import time

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
    def __init__(self):#, onMessage) -> None:
        self.seq = "null"
        self.heartbeatAckReceived = True
        #self.onMessageCallBack = onMessage
        self.sendProblemBuffer = []
        asyncio.run(self.init())

    async def init(self) -> None:
        await self.connect(),
        await self.sendIdentifyPayload()
        self.main()

    async def revive(self) -> None:
        await self.disconnect(),
        await self.connect(),
        await self.sendResume()
        self.main()

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

    async def disconnect(self) -> None:
        self.loop.close()
        await self.ws.close()
    
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
            #print(f"{data['op']=}")
            if data['s'] != None:
                self.seq = data['s']
            if data['op'] == 0:
                if data['t'] == 'READY':
                    print('ready!')
                else:
                    httpAPI = HttpAPI(GUILD)
                    if data['t'] == "INTERACTION_CREATE":
                        httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'GOT IT!')
                        userInBuffer = False
                        for user, _, _, _ in self.sendProblemBuffer:
                            if data['d']['member']['user']['id'] == user:
                                userInBuffer = True
                        if userInBuffer: 
                            for i in range(len(self.sendProblemBuffer)):
                                if self.sendProblemBuffer[i][0] == data['d']['member']['user']['id']:
                                    del self.sendProblemBuffer[i]
                                    break
                        self.sendProblemBuffer.append((data['d']['member']['user']['id'], data['d']['token'], data['d']['id'], time.time()))
                        
                    elif data['t'] == 'MESSAGE_CREATE':
                        while len(self.sendProblemBuffer):
                            if time.time() - self.sendProblemBuffer[0][3] > 60 * 15:
                                del self.sendProblemBuffer[0]
                            else:
                                break

                        if len(self.sendProblemBuffer):
                            if 'attachments' in data['d']:
                                userInBuffer = False
                                for user, token, iid, _ in self.sendProblemBuffer:
                                    if data['d']['author']['id'] == user:
                                        userInBuffer = True
                                        userId = user
                                        interactionToken = token
                                        interactionId = iid
                                        break
                                if userInBuffer:
                                    problemPicUrls = []
                                    for attachment in data['d']['attachments']:
                                        if 'image' in attachment['content_type']: problemPicUrls.append(attachment['url'])
                                    httpAPI.deleteOriginalInteraction(interactionToken)
                                    print(f'{problemPicUrls=}')
                                    for pic in problemPicUrls:
                                        httpAPI.sendFollowupInteractionEmbedImageUrl(interactionToken, pic)
                                    for i in range(len(self.sendProblemBuffer)):
                                        if self.sendProblemBuffer[i][0] == userId:
                                            del self.sendProblemBuffer[i]
                                            break
                    #self.onMessageCallBack(data)
            elif data['op'] == 1:
                self.sendHeartbeat()
            elif data['op'] == 7:
                await self.revive()
            elif data['op'] == 9:
                print('INVALID SESSION!')
                self.revive()
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
                "seq": f"{self.seq}",
                "session_id":f"{self.sessionId}"
            }
        )

class HttpAPI:
    def __init__(self, guild=None):
        if guild != None:
            self.apiEndpoint = f"https://discord.com/api/v{API_VERSION}/applications/{CLIENT_ID}/guilds/{guild}/commands"
        else:
            self.apiEndpoint = f"https://discord.com/api/v{API_VERSION}/applications/{CLIENT_ID}/commands"
    
    def sendInteractionMessage(self, interactionId:int, interactionToken:str, message:str):
        interactionUrl = f'https://discord.com/api/v{API_VERSION}/interactions/{interactionId}/{interactionToken}/callback'
        data = {
            'type':4,
            'data': {
                'content': f"{message}"
            }
        }
        requests.post(interactionUrl, json=data, headers=headers)

    def deleteOriginalInteraction(self, interactionToken:str):
        interactionUrl = f'https://discord.com/api/v{API_VERSION}/webhooks/{CLIENT_ID}/{interactionToken}/messages/@original'
        requests.delete(interactionUrl)

    def sendFollowupInteractionEmbedImageUrl(self, interactionToken:str, url:str):
        interactionUrl = f'https://discord.com/api/v{API_VERSION}/webhooks/{CLIENT_ID}/{interactionToken}'
        data = {
            'type':4,
            'data': {
                'embeds': [{
                    'image':{
                        'url': url
                    }
                }]
            }
        }
        requests.post(interactionUrl, json=data, headers=headers)
    
    #def makeChatInputTypeCommand(self, name:str, description:str, )

if __name__ == "__main__":
    a = WebSocketAPI()
