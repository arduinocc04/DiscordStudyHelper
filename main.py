import api
import time
import logging
import json
import os

sendProblemBuffer = []
with open('solveState.json', 'r') as f:
    solveState = json.loads(f.readline())
with open('bookmarkState.json', 'r') as f:
    bookmarkState = json.loads(f.readline())
with open('urI.txt', 'r') as f:
    MY_IP = f.readline().rstrip()

logger = logging.getLogger('MAIN LOGGER')
logger.setLevel(logging.DEBUG)
logger.addHandler(api.streamHandler)
logger.addHandler(api.fileHandler)

def onMessage(data):
    httpAPI = api.HttpAPI(api.GUILD)
    if data['t'] == "MESSAGE_REACTION_ADD":
        if data['d']['user_id'] != api.CLIENT_ID:
            if data['d']['emoji']['name'] == '❌':
                solveState[data['d']['message_id']][data['d']['user_id']] = False
                httpAPI.sendMessageToChannel("unsolved!", data['d']['channel_id'])
                with open('solveState.json', 'w') as f:
                    f.write(json.dumps(solveState))
            elif data['d']['emoji']['name'] == '⭕':
                solveState[data['d']['message_id']][data['d']['user_id']] = True
                httpAPI.sendMessageToChannel("solved!", data['d']['channel_id'])
                with open('solveState.json', 'w') as f:
                    f.write(json.dumps(solveState))
            elif data['d']['emoji']['name'] == '⭐':
                bookmarkState[data['d']['message_id']][data['d']['user_id']] = True
                httpAPI.sendMessageToChannel("bookmarked!", data['d']['channel_id'])
                with open('bookmarkState.json', 'w') as f:
                    f.write(json.dumps(bookmarkState))

    elif data['t'] == "MESSAGE_REACTION_REMOVE":
        if data['d']['user_id'] != api.CLIENT_ID:
            if data['d']['emoji']['name'] == '⭐':
                bookmarkState[data['d']['message_id']][data['d']['user_id']] = False
                httpAPI.sendMessageToChannel("unbookmarked!", data['d']['channel_id'])
                with open('bookmarkState.json', 'w') as f:
                    f.write(json.dumps(bookmarkState))

    elif data['t'] == "INTERACTION_CREATE":
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
            elif data['d']['data']['name'] == 'solved':
                if (not 'message' in data['d']) or  data['d']['message']['author']['id'] != api.CLIENT_ID: 
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'GOT IT!')
                    for a in solveState.keys():
                        if solveState[a][data['d']['member']['user']['id']]:
                            httpAPI.replyMessage(data['d']['channel_id'], a)
            elif data['d']['data']['name'] == 'unsolved':
                if (not 'message' in data['d']) or  data['d']['message']['author']['id'] != api.CLIENT_ID: 
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'GOT IT!')
                    for a in solveState.keys():
                        if not solveState[a][data['d']['member']['user']['id']]:
                            httpAPI.replyMessage(data['d']['channel_id'], a)
            elif data['d']['data']['name'] == 'bookmarks':
                if (not 'message' in data['d']) or  data['d']['message']['author']['id'] != api.CLIENT_ID: 
                    if data['d']['data']['options'][0]['value'] == 'all':
                        httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'GOT IT!')
                        for a in bookmarkState.keys():
                            cnt = -1 #studyhelper must solved it
                            total = 0
                            for i in bookmarkState[a]:
                                if i: cnt += 1
                                total += 1
                            if cnt:
                                httpAPI.replyMessage(data['d']['channel_id'], a, f'{cnt}/{total}명이 북마크 함')
                    elif data['d']['data']['options'][0]['value'] == 'me':
                        httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'GOT IT!')
                        for a in bookmarkState.keys():
                            if bookmarkState[a][data['d']['member']['user']['id']]:
                                httpAPI.replyMessage(data['d']['channel_id'], a)
                    
        """
        elif data['d']['type'] == 3: #MESSAGE_COMPONENT
            if data['d']['data']['component_type'] == 2: #solve, unsolve, bookmark Interaction
                if data['d']['data']['custom_id'] == 'solve_button':
                    solveState[data['d']['message']['id']][data['d']['member']['user']['id']] = True
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'solve')
                    with open('solveState.json', 'w') as f:
                        f.write(json.dumps(solveState))
                elif data['d']['data']['custom_id'] == 'unsolve_button':
                    solveState[data['d']['message']['id']][data['d']['member']['user']['id']] = False
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'unsolve')
                    with open('solveState.json', 'w') as f:
                        f.write(json.dumps(solveState))
                elif data['d']['data']['custom_id'] == 'bookmark_button':
                    bookmarkState[data['d']['member']['user']['id']].app
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'bookmark')
                else:
                    pass
                logger.info(f'{solveState=}')
        """
        
        
    elif data['t'] == 'MESSAGE_CREATE':
        if data['d']['author']['id'] == api.CLIENT_ID and data['d']['type'] == 0: #if Bot send message
            if len(data['d']['embeds']) + len(data['d']['attachments']) > 0: #if Bot reuploaded problem
                httpAPI.createReaction(data['d']['channel_id'], data['d']['id'], "⭕")
                members = httpAPI.getGuildMembers(data['d']['guild_id'])
                users = []
                for mem in members:
                    if 'bot' in mem['user'] and mem['user']['bot']:
                        pass
                    else:
                        users.append(mem['user']['id'])
                logger.info(f'{users=}')
                httpAPI.createReaction(data['d']['channel_id'], data['d']['id'], "❌")
                solveState[data['d']['id']] = {}
                bookmarkState[data['d']['id']] = {}
                for uid in users:
                    solveState[data['d']['id']][uid] = False
                    bookmarkState[data['d']['id']][uid] = False
                with open('solveState.json', 'w') as f:
                    f.write(json.dumps(solveState))
                with open('bookmarkState.json', 'w') as f:
                    f.write(json.dumps(bookmarkState))

                httpAPI.createReaction(data['d']['channel_id'], data['d']['id'], "⭐")
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
                            #urllib.request.urlretrieve(pic, "problems/" + data['d']['id'] + "_" + str(imgI) + ".jpg")
                            os.system("curl " + pic + " > problems/" + data['d']['id'] + "_" + str(imgI) + ".jpg")
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
