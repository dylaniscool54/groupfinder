const axios = require("axios");
const express = require("express");
const FormData = require("form-data");
const fs = require("fs");
const app = express();
const port = 3000;

function dreamtime(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

let dreaming = false;

let currentapi = "roblox"

async function ratelimit() {
  console.log("rate limit! waiting 30 seconds");
  if (currentapi == "roblox") {
    currentapi = 'roproxy'
  } else {
    currentapi = 'roblox'
    await dreamtime(1000);
  }
  
}

let groupscans = 0

app.get("/dreams", async (req, res) => {
  const fallingasleep = req.query.fallingasleep;
  const fallingasleeplocked = req.query.fallingasleeplocked;
  const bl = req.query.bl;
  const key = req.query.key;
  const auth = req.query.auth;

  const blacklistArray = bl.split(",").map((item) => item.trim());

  if (dreaming) {
    res.json(["busy", groupscans]);
    groupscans = 0
    return
  }
  const start = req.query.a;
  const end = req.query.b;
  dreaming = true;

  console.log("start: " + start);
  console.log("end: " + end);

  res.json(["ready", groupscans]);
  groupscans = 0

  let allrequesturls = [];

  let amountin = 0;
  let a = "";
  
  for (let i = start; i <= end; i++) {
    if (blacklistArray.includes(i.toString().trim())) {
      console.log("SKIPPED!: " + i);
      continue;
    }

    if (amountin >= 100) {
      allrequesturls.push(a);
      a = "";
      amountin = 0;
    }

    a += "," + i;
    amountin += 1;
  }
  if (amountin > 0) {
    allrequesturls.push(a);
  }

  for (const idx in allrequesturls) {
    const robloxapiurl = allrequesturls[idx];
    while (true) {
      try {
        const response = await axios.get(
          "https://groups."+currentapi+".com/v2/groups?groupIds=" + robloxapiurl
        );
        const responsedata = response.data.data;
        console.log("v2: " + idx + " / " + allrequesturls.length);

        for (const idx2 in responsedata) {
          const robloxgroupinfo = responsedata[idx2];
          let robloxID = robloxgroupinfo.id;
          
          groupscans += 1

          if (robloxgroupinfo.owner == null) {
            while (true) {
              try {
                try {
                  await axios.head(
                    "https://cdn.glitch.global/" +
                      key +
                      "/" +
                      robloxID
                  );
                  console.log("Group is locked!")
                } catch (err) {
                  //not marked as locked
                  const v1request = await axios.get(
                    "https://groups."+currentapi+".com/v1/groups/" + robloxID
                  );
                  console.log("v1: " + idx2 + " / " + responsedata.length);
                  const v1requestdata = v1request.data;

                  if (
                    v1requestdata.owner == null &&
                    v1requestdata.publicEntryAllowed == true &&
                    !v1requestdata.isLocked
                  ) {
                    let sleepingdata = {};
                    const groupname = robloxgroupinfo.name;

                    let clouds = "Unknown";

                    try {
                      const rs = await axios.get(
                        "https://economy."+currentapi+".com/v1/groups/" +
                          robloxID +
                          "/currency"
                      );
                      clouds = rs.data.robux;
                    } catch (err) {}

                    sleepingdata["embeds"] = [
                      {
                        description:
                          "Robux: " +
                          clouds +
                          "\nMembers: " +
                          v1requestdata.memberCount +
                          "\n" +
                          "https://www.roblox.com/groups/" +
                          robloxID,
                        title: groupname + " is unclaimed",
                      },
                    ];

                    sleepingdata["content"] = "<@&1230452555595644969>";

                    await axios.post(fallingasleep, sleepingdata);
                  } else {
                    if (v1requestdata.owner == null) {
                      let response = await axios.get(
                        "https://api.glitch.com/v1/projects/" +
                          key +
                          "/policy?contentType=lol",
                        {
                          headers: {
                            Authorization: auth,
                            Origin: "https://glitch.com",
                          },
                        }
                      );

                      const authed = response.data;

                      const formData = new FormData();

                      const filename = robloxID;
                      
                      formData.append("key", key + "/" + filename);
                      formData.append("Content-Type", "lol");
                      formData.append("Cache-Control", "max-age=31536000");
                      formData.append("AWSAccessKeyId", authed.accessKeyId);
                      formData.append("acl", "public-read");
                      formData.append("policy", authed.policy);
                      formData.append("signature", authed.signature);

                      const readStream = fs.createReadStream("place.txt");

                      formData.append("file", readStream, filename);

                      const s3response = await axios.post(
                        "https://s3.amazonaws.com/production-assetsbucket-8ljvyr1xczmb",
                        formData
                      );

                      let sleepingdata = {};
                      const groupname = robloxgroupinfo.name;

                      let clouds = "Unknown";

                      try {
                        const rs = await axios.get(
                          "https://economy.roblox.com/v1/groups/" +
                            robloxID +
                            "/currency"
                        );
                        clouds = rs.data.robux;
                      } catch (err) {}

                      sleepingdata["embeds"] = [
                        {
                          description:
                            "Robux: " +
                            clouds +
                            "\nMembers: " +
                            v1requestdata.memberCount +
                            "\n" +
                            "https://www.roblox.com/groups/" +
                            robloxID,
                          title: groupname + " is unclaimed but locked!",
                        },
                      ];

                      await axios.post(fallingasleeplocked, sleepingdata);
                    }
                  }
                }

                break;
              } catch (err) {
                console.log(err.message);
                
                if (err.response && err.response.status == 429) {
                  await ratelimit();
                } else {
                  break;
                }
              }
            }
          }
        }

        console.log("Success");
        await dreamtime(1000); //prevent rate limits
        break;
      } catch (err) {
        console.log(err.message);
        
        if (err.response && err.response.status == 429) {
          await ratelimit();
        } else {
          break;
        }
      }
    }
  }

  console.log("Dreamed");
  dreaming = false;
});

app.get("/", async (req, res) => {
  const e = await axios.get("http://ip-api.com/json");
  res.send(e.data.query);
});

app.listen(port, () => {
  console.log(`BLM app listening on port ${port}`);
});
