from numpy import dtype
import api
import os
import time
import logging

sendProblemBuffer = []

logger = logging.getLogger('MAIN LOGGER')
logger.setLevel(logging.DEBUG)
logger.addHandler(api.streamHandler)
logger.addHandler(api.fileHandler)

def onMessage(data):
    httpAPI = api.HttpAPI(api.GUILD)
    if data['t'] == "INTERACTION_CREATE":
        if (not 'message' in data['d']) or  data['d']['message']['author']['id'] != api.CLIENT_ID: httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'GOT IT!')
        else:
            if data['d']['data']['component_type'] == 2 and data['d']['type'] == 3:
                if data['d']['data']['custom_id'] == 'solve_button':
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'solve')
                    #httpAPI.deleteOriginalInteraction(data['d']['token'])
                elif data['d']['data']['custom_id'] == 'unsolve_button':
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'unsolve')
                elif data['d']['data']['custom_id'] == 'bookmark_button':
                    httpAPI.sendInteractionMessage(data['d']['id'], data['d']['token'], 'bookmark')
                else:
                    pass
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

        if data['d']['member']['user']['id'] != api.CLIENT_ID: sendProblemBuffer.append((data['d']['member']['user']['id'], data['d']['token'], data['d']['id'], time.time(), data['d']['data']['options'][0]['value']))
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
                for user, token, iid, _, s in sendProblemBuffer:
                    if data['d']['author']['id'] == user:
                        userInBuffer = True
                        userId = user
                        interactionToken = token
                        interactionId = iid
                        subject = s
                        break
                if userInBuffer:
                    problemPicUrls = []
                    for attachment in data['d']['attachments']:
                        if 'image' in attachment['content_type']: problemPicUrls.append(attachment['url'])
                    httpAPI.deleteOriginalInteraction(interactionToken)
                    for pic in problemPicUrls:
                        httpAPI.sendPicToChannelWithMentionAndContent(pic, data['d']['channel_id'], data['d']['author']['id'], subject)
                    for i in range(len(sendProblemBuffer)):
                        if sendProblemBuffer[i][0] == userId:
                            del sendProblemBuffer[i]
                            break
                    httpAPI.delMessage(data['d']['channel_id'], data['d']['id'])

if __name__ == '__main__':
    app = api.WebSocketAPI(onMessage=onMessage)