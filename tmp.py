import requests

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
API_VERSION = 8
url = f"https://discord.com/api/v{API_VERSION}/applications/{CLIENT_ID}/guilds/{GUILD}/commands"
#url = f"https://discord.com/api/v{API_VERSION}/applications/{CLIENT_ID}/commands"

# This is an example CHAT_INPUT or Slash Command, with a type of 1
json = {
    "name": "problem",
    "type": 1,
    "description": "Send a problem",
    "options": [
        {
            "name": "subject",
            "description": "The type of subject",
            "type": 3,
            "required": True,
            "choices": [
                {
                    "name": "Reading",
                    "value": "subject_reading"
                },
                {
                    "name": "Literature",
                    "value": "subject_literature"
                },
                {
                    "name": "NarrAndWriting",
                    "value": "subject_narrandwriting"
                },
                {
                    "name": "KorGrammer",
                    "value": "subject_korgrammer"
                },
                {
                    "name": "MathOne",
                    "value": "subject_mathone"
                },
                {
                    "name": "MathTwo",
                    "value": "subject_mathtwo"
                },
                {
                    "name": "Calculus",
                    "value": "subject_calculus"
                },
                {
                    "name": "Probability",
                    "value": "subject_probability"
                },
                {
                    "name": "Geometry",
                    "value": "subject_geometry"
                },
                {
                    "name": "HighSchoolMath",
                    "value": "subject_highschoolmath"
                },
                {
                    "name": "PhysicsOne",
                    "value": "subject_physicsone"
                },
                {
                    "name": "ChemistryOne",
                    "value": "subject_chemistryone"
                },
                {
                    "name": "ChemistryTwo",
                    "value": "subject_chemistrytwo"
                },
                {
                    "name": "BiologyOne",
                    "value": "subject_biologyone"
                },
                {
                    "name": "English",
                    "value": "subject_english"
                },
                {
                    "name": "KorHistory",
                    "value": "subject_korhistory"
                },
            ]
        },
    ]
}

# For authorization, you can use either your bot token
headers = {
    "Authorization": f"Bot {TOKEN}"
}

r = requests.post(url, headers=headers, json=json)

json = {
    "name": "bookmarks",
    "type": 1,
    "description": "Show bookmarked problems",
    "options": [
        {
           "name": "range", 
           "description": "range",
           "type": 3,
           "required": True,
           "choices": [
               {
                   "name": "me",
                   "value": "me"
               },
               {
                   "name": "all",
                   "value": "all"
               }
           ]
        }
    ]
}

r = requests.post(url, headers=headers, json=json)

json = {
    "name": "unsolved",
    "type": 1,
    "description": "Show unsolved problems by me"
}
r = requests.post(url, headers=headers, json=json)
print(r.text)

json = {
    "name": "solved",
    "type": 1,
    "description": "Show solved problems by me"
}
r = requests.post(url, headers=headers, json=json)
print(r.text)
