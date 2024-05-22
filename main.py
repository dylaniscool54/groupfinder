import time
import requests
from flask import Flask, request, jsonify
import os
import threading

app = Flask(__name__)

def wait(ms):
    time.sleep(ms / 1000.0)

running = False
currentapi = "roblox"
groupscans = 0

def swapapi():
    global currentapi
    if currentapi == "roblox":
        currentapi = 'roproxy'
    else:
        currentapi = 'roblox'
    wait(1000)

def main(hook, lock, bl, key, auth, start, end):
    global running, groupscans
    blacklistArray = [item.strip() for item in bl.split(',')]

    allrequesturls = []
    amountin = 0
    a = ""

    for i in range(start, end + 1):
        if str(i).strip() in blacklistArray:
            print("SKIPPED!:", i)
            continue

        if amountin >= 100:
            allrequesturls.append(a)
            a = ""
            amountin = 0

        a += "," + str(i)
        amountin += 1

    if amountin > 0:
        allrequesturls.append(a)

    for idx, robloxapiurl in enumerate(allrequesturls):
        while True:
            try:
                response = requests.get(f"https://groups.{currentapi}.com/v2/groups?groupIds={robloxapiurl}")
                responsedata = response.json()['data']
                print(f"v2: {idx} / {len(allrequesturls)}")

                for idx2, robloxgroupinfo in enumerate(responsedata):
                    robloxID = robloxgroupinfo['id']
                    groupscans += 1

                    if not robloxgroupinfo.get('owner'):
                        while True:
                            try:
                                try:
                                    requests.head(f"https://cdn.glitch.global/{key}/{robloxID}")
                                    print("Group is locked!")
                                except requests.RequestException as err:
                                    v1request = requests.get(f"https://groups.{currentapi}.com/v1/groups/{robloxID}")
                                    v1requestdata = v1request.json()
                                    print(f"v1: {idx2} / {len(responsedata)}")

                                    if (not v1requestdata.get('owner') and v1requestdata['publicEntryAllowed'] and not v1requestdata.get('isLocked')):
                                        sleepingdata = {}
                                        groupname = robloxgroupinfo['name']
                                        clouds = "Unknown"

                                        try:
                                            rs = requests.get(f"https://economy.{currentapi}.com/v1/groups/{robloxID}/currency")
                                            clouds = rs.json()['robux']
                                        except requests.RequestException:
                                            pass

                                        sleepingdata["embeds"] = [{
                                            "description": f"Robux: {clouds}\nMembers: {v1requestdata['memberCount']}\nhttps://www.roblox.com/groups/{robloxID}",
                                            "title": f"{groupname} is unclaimed"
                                        }]

                                        data = {"content": "<@&1230452555595644969>", **sleepingdata}

                                        requests.post(hook, json=data)
                                    else:
                                        if v1requestdata.get('owner') is None:
                                            response = requests.get(f"https://api.glitch.com/v1/projects/{key}/policy?contentType=lol", headers={"Authorization": auth, "Origin": "https://glitch.com"})
                                            authed = response.json()

                                            with open('place.txt', 'rb') as readStream:
                                                files = {
                                                    'key': (None, f"{key}/{robloxID}"),
                                                    'Content-Type': (None, 'lol'),
                                                    'Cache-Control': (None, 'max-age=31536000'),
                                                    'AWSAccessKeyId': (None, authed['accessKeyId']),
                                                    'acl': (None, 'public-read'),
                                                    'policy': (None, authed['policy']),
                                                    'signature': (None, authed['signature']),
                                                    'file': (robloxID, readStream)
                                                }
                                                s3response = requests.post("https://s3.amazonaws.com/production-assetsbucket-8ljvyr1xczmb", files=files)

                                            sleepingdata = {}
                                            groupname = robloxgroupinfo['name']
                                            clouds = "Unknown"

                                            try:
                                                rs = requests.get(f"https://economy.roblox.com/v1/groups/{robloxID}/currency")
                                                clouds = rs.json()['robux']
                                            except requests.RequestException:
                                                pass

                                            data["embeds"] = [{
                                                "description": f"Robux: {clouds}\nMembers: {v1requestdata['memberCount']}\nhttps://www.roblox.com/groups/{robloxID}",
                                                "title": f"{groupname} is unclaimed but locked!"
                                            }]

                                            requests.post(lock, json=data)
                                break
                            except requests.RequestException as err:
                                print(err)
                                if err.response and err.response.status_code == 429:
                                    swapapi()
                                else:
                                    break
                print("LETS GO")
                wait(1000)  # prevent rate limits
                break
            except requests.RequestException as err:
                print(err)
                if err.response and err.response.status_code == 429:
                    swapapi()
                else:
                    break

    print("DONE")
    running = False

@app.route('/cycle', methods=['GET'])
def cycle():
    global running, groupscans

    hook = request.args.get('hook')
    lock = request.args.get('lock')
    bl = request.args.get('bl')
    key = request.args.get('key')
    auth = request.args.get('auth')

    if running:
        response = jsonify(["busy", groupscans])
        groupscans = 0
        return response

    start = int(request.args.get('a'))
    end = int(request.args.get('b'))
    running = True

    print("start:", start)
    print("end:", end)

    response = jsonify(["ready", groupscans])
    groupscans = 0

    threading.Thread(target=main, args=(hook, lock, bl, key, auth, start, end,)).start()
    return response

@app.route('/getip', methods=['GET'])
def getip():
    response = requests.get("http://ip-api.com/json")
    return response.json()['query']

@app.route('/')
def index():
    return ""

if __name__ == '__main__':
    app.run(port=3000)
