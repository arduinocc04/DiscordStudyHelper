import api
import time
import logging
import json
import os
import urllib.request

sendProblemBuffer = []
with open('solveState.json', 'r') as f:
    solveState = json.loads(f.readline())
with open('urI.txt', 'r') as f:
    MY_IP = f.readline()

logger = logging.getLogger('MAIN LOGGER')
logger.setLevel(logging.DEBUG)
logger.addHandler(api.streamHandler)
logger.addHandler(api.fileHandler)

def onMessage(data):
    httpAPI = api.HttpAPI(api.GUILD)
    if data['t'] == "INTERACTION_CREATE":
        if data['d']['type'] == 2: #APPLICATION_COMMAND
            if data['d']['data']['name'] == 'problem': #/problem interaction
                if (not 'message' in data['d']) or  data['d']['message']['author']['id'] != api.CLIENT_ID: 
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'GOT IT!')
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

                    sendProblemBuffer.append((data['d']['member']['user']['id'], data['d']['token'], data['d']['id'], time.time(), data['d']['data']['options'][0]['value']))
                    logger.info(f'{sendProblemBuffer=}')

        elif data['d']['type'] == 3: #MESSAGE_COMPONENT
            if data['d']['data']['component_type'] == 2: #solve, unsolve, bookmark Interaction
                if data['d']['data']['custom_id'] == 'solve_button':
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'solve')
                    solveState[data['d']['message']['id']][data['d']['member']['user']['id']] = True
                    with open('solveState.json', 'w') as f:
                        f.write(json.dumps(solveState))
                elif data['d']['data']['custom_id'] == 'unsolve_button':
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'unsolve')
                    solveState[data['d']['message']['id']][data['d']['member']['user']['id']] = False
                    with open('solveState.json', 'w') as f:
                        f.write(json.dumps(solveState))
                elif data['d']['data']['custom_id'] == 'bookmark_button':
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'bookmark')
                else:
                    pass
                logger.info(f'{solveState=}')
        
        
    elif data['t'] == 'MESSAGE_CREATE':
        if data['d']['author']['id'] == api.CLIENT_ID and data['d']['type'] == 0: #if Bot reuploaded problem
            members = httpAPI.getGuildMembers(data['d']['guild_id'])
            users = []
            for mem in members:
                if 'bot' in mem['user'] and mem['user']['bot']:
                    pass
                else:
                    users.append(mem['user']['id'])
            logger.info(f'{users=}')
            solveState[data['d']['id']] = {}
            for uid in users:
                solveState[data['d']['id']][uid] = False
            with open('solveState.json', 'w') as f:
                f.write(json.dumps(solveState))
        else:
            while len(sendProblemBuffer):
                if time.time() - sendProblemBuffer[0][3] > 60 * 1: #User should send problem picture in 1 minute
                    del sendProblemBuffer[0]
                else:
                    break

            if len(sendProblemBuffer):
                if 'attachments' in data['d']: #when user uploaded problem
                    userInBuffer = False
                    for user, token, _, _, s in sendProblemBuffer:
                        if data['d']['author']['id'] == user:
                            userInBuffer = True
                            userId = user
                            interactionToken = token
                            subject = s
                            break
                    if userInBuffer:
                        problemPicUrls = []
                        for attachment in data['d']['attachments']:
                            if 'image' in attachment['content_type']: problemPicUrls.append(attachment['url'])
                        httpAPI.deleteOriginalInteraction(interactionToken)
                        imgI = 0
                        for pic in problemPicUrls:
                            urllib.request.urlretrieve(pic, "problems/" + data['d']['id'] + "_" + str(imgI) + ".jpg")
                            #os.system("curl " + pic + " > problems/" + data['d']['id'] + "_" + str(imgI) + ".jpg")
                            url = MY_IP + "/problems/"+ data['d']['id'] + "_" + str(imgI) + ".jpg"
                            httpAPI.sendPicToChannelWithMentionAndContent(url, data['d']['channel_id'], data['d']['author']['id'], subject)
                            imgI += 1
                        for i in range(len(sendProblemBuffer)):
                            if sendProblemBuffer[i][0] == userId:
                                del sendProblemBuffer[i]
                                break
                        httpAPI.delMessage(data['d']['channel_id'], data['d']['id'])

if __name__ == '__main__':
    app = api.WebSocketAPI(onMessage=onMessage)
