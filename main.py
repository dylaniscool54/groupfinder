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

def run(hook, lock, bl, key, auth, start, end, freehook, cookie, rbxhook, blacklistarray, urls_chunk, threadnum, possiblehook):
    global running, groupscans
    
    for idx, robloxapiurl in enumerate(urls_chunk):
        while True:
            response = requests.get(f"https://groups.{currentapi}.com/v2/groups?groupIds={robloxapiurl}")
            
            if response.status_code == 429:
                swapapi()
                continue
            
            responsedata = response.json()['data']
            print(f"{threadnum}, v2: {idx} / {len(urls_chunk)}")
            
            for idx2, robloxgroupinfo in enumerate(responsedata):
                robloxID = robloxgroupinfo['id']
                groupscans += 1

                if not robloxgroupinfo.get('owner'):
                    while True:
                        if requests.head(f"https://cdn.glitch.global/{key}/{robloxID}").status_code == 403:
                            v1request = requests.get(f"https://groups.{currentapi}.com/v1/groups/{robloxID}")
                            
                            if v1request.status_code == 429:
                                swapapi()
                                continue
                            
                            v1requestdata = v1request.json()
                            print(f"{threadnum}, v1: {idx2} / {len(responsedata)}")
                            
                            if (not v1requestdata.get('owner') and v1requestdata['publicEntryAllowed'] and not v1requestdata.get('isLocked')):
                                data = {}
                                groupname = robloxgroupinfo['name']
                                clouds = "Unknown"
                                poss = False
                                
                                extra = ""

                                try:
                                    onsale = requests.get("https://catalog.roblox.com/v1/search/items?category=All&creatorTargetId="+str(robloxID)+"&creatorType=Group&cursor=&limit=50&sortOrder=Desc&sortType=Updated").json()["data"]
                                    
                                    if len(onsale) > 0:
                                        poss = True
                                        extra += "\n Has " + str(len(onsale)) + " items on sale"
                                    
                                    games = requests.get("https://games.roblox.com/v2/groups/"+str(robloxID)+"/games?accessFilter=Public&cursor=&limit=50&sortOrder=Desc").json()["data"]
                                    if len(games) > 0:
                                        poss = True
                                        extra += "\n Has " + str(len(onsale)) + " games"

                                    rs = requests.get(f"https://economy.roblox.com/v1/groups/{robloxID}/currency", cookies={".ROBLOSECURITY": cookie})
                                    clouds = rs.json()['robux']
                                    
                                except:
                                    pass

                                touse = freehook

                                if clouds == "Unknown":
                                    if poss:
                                        touse = possiblehook
                                    else:
                                        touse = hook
                                elif clouds > 0:
                                    touse = rbxhook
                                    
                                if clouds == 0:
                                    if poss:
                                        touse = possiblehook
                                
                                data["embeds"] = [{
                                    "description": f"Robux: {clouds}\nMembers: {v1requestdata['memberCount']}{extra} \n https://www.roblox.com/groups/{robloxID}",
                                    "title": f"{groupname} is unclaimed"
                                }]

                                data["content"] = "<@&1242748573632954459>"

                                requests.post("https://discord.com/api/webhooks/" + touse, json=data)
                            else:
                                if v1requestdata.get('owner') is None:
                                    response = requests.get(f"https://api.glitch.com/v1/projects/{key}/policy?contentType=lol", headers={"Authorization": auth, "Origin": "https://glitch.com"})
                                    authed = response.json()

                                    data = {
                                            'key': f"{key}/{robloxID}",
                                            'Content-Type': "lol",
                                            'Cache-Control': 'max-age=31536000',
                                            'AWSAccessKeyId': authed['accessKeyId'],
                                            'acl': 'public-read',
                                            'policy': authed['policy'],
                                            'signature': authed['signature'],
                                    }

                                    files = {
                                            'file': (str(robloxID), "locked".encode('utf-8')),
                                    }

                                    s3response = requests.post("https://s3.amazonaws.com/production-assetsbucket-8ljvyr1xczmb", data=data, files=files)

                                    data = {}
                                    groupname = robloxgroupinfo['name']

                                    data["embeds"] = [{
                                        "description": f"Members: {v1requestdata['memberCount']}\nhttps://www.roblox.com/groups/{robloxID}",
                                        "title": f"{groupname} is unclaimed but locked!"
                                    }]

                                    requests.post("https://discord.com/api/webhooks/" + lock, json=data)
                        break
            time.sleep(1)  # prevent rate limits
            break
    print(f"{threadnum}, is done!")
            
def main(hook, lock, bl, key, auth, start, end, freehook, cookie, rbxhook, possiblehook):
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
    
    num_threads = 10
    chunk_size = len(allrequesturls) // num_threads
    threads = []
    for i in range(num_threads):
        start_index = i * chunk_size
        end_index = start_index + chunk_size if i < num_threads - 1 else len(allrequesturls)
        urls_chunk = allrequesturls[start_index:end_index]
        thread = threading.Thread(target=run, args=(hook, lock, bl, key, auth, start, end, freehook, cookie, rbxhook, blacklistArray, urls_chunk, i, possiblehook))
        threads.append(thread)
        thread.start()
        
        
    for thread in threads:
      thread.join()
      
      
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
    freehook = request.args.get('free')
    cookie = request.args.get('cookie')
    rbx = request.args.get('rbx')
    possiblehook = request.args.get('p')
    print(freehook)
    print(cookie)
    print(rbx)
    
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

    threading.Thread(target=main, args=(hook, lock, bl, key, auth, start, end,freehook,cookie,rbx,possiblehook)).start()
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
