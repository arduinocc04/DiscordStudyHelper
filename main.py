import api
import os
import time
import logging
with open('testguild.txt', 'r') as f:
    GUILD = f.readline().rstrip()
sendProblemBuffer = []

logger = logging.getLogger('MAIN LOGGER')
logger.setLevel(logging.DEBUG)
logger.addHandler(api.streamHandler)
logger.addHandler(api.fileHandler)

def onMessage(data):
    httpAPI = api.HttpAPI(GUILD)
    if data['t'] == "INTERACTION_CREATE":
        if(data['d']['author']['id'] != api.CLIENT_ID) httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'GOT IT!')
        userInBuffer = False
        for user, _, _, _ in sendProblemBuffer:
            if data['d']['member']['user']['id'] == user:
                userInBuffer = True
        logger.info(f'{sendProblemBuffer=}')
        if userInBuffer: 
            for i in range(len(sendProblemBuffer)):
                if sendProblemBuffer[i][0] == data['d']['member']['user']['id']:
                    del sendProblemBuffer[i]
                    break

        if(data['d']['member']['user']['id'] != api.CLIENT_ID) sendProblemBuffer.append((data['d']['member']['user']['id'], data['d']['token'], data['d']['id'], time.time()))
        logger.info(f'{sendProblemBuffer=}')
        
    elif data['t'] == 'MESSAGE_CREATE':
        #if 'embeds' in data['d'] and len(data['d']['embeds']) and api.CLIENT_ID == data['d']['author']['id']:
        #    httpAPI.createReaction(data['d']['channel_id'], data['d']['id'], '%E2%AD%95%0A')

        while len(sendProblemBuffer):
            if time.time() - sendProblemBuffer[0][3] > 60 * 15:
                del sendProblemBuffer[0]
            else:
                break

        if len(sendProblemBuffer):
            if 'attachments' in data['d']:
                userInBuffer = False
                for user, token, iid, _ in sendProblemBuffer:
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
                    for pic in problemPicUrls:
                        httpAPI.sendPicToChannel(pic, data['d']['channel_id'])
                    for i in range(len(sendProblemBuffer)):
                        if sendProblemBuffer[i][0] == userId:
                            del sendProblemBuffer[i]
                            break
                    httpAPI.delMessage(data['d']['channel_id'], data['d']['id'])

if __name__ == '__main__':
    app = api.WebSocketAPI(onMessage=onMessage)