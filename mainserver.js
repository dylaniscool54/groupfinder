const axios = require("axios");
console.log("we here");

let eachbatch = 10000;


const minnumber = 0;
const maxnumber = 34000000;
let currentidx = minnumber;

const discordwebhook = Buffer.from(process.env.foundhook, 'base64').toString('utf-8');
const debughook = Buffer.from(process.env.debughook, 'base64').toString('utf-8');
const lockedhook = Buffer.from(process.env.lockedhook, 'base64').toString('utf-8');
const glitchauth = Buffer.from(process.env.auth, 'base64').toString('utf-8');

const glitchkey = "0d702471-9ed0-497b-948c-145b524b2171"

//https://raw.githubusercontent.com/dylaniscool54/groupfinder/main/main.js
let nodes = [];

const blacklist = [ //roblox group id's
  1
]


nodes = nodes.reverse()
const blacklists = blacklist.join(',')

let unodes = []; //with unique IP's


const nodeslength = nodes.length;
console.log(nodeslength + " VM's");

let onnode = 0;

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function scangroups(start, end) {
  try {
    let currentnode = unodes[onnode];
    if (!currentnode) {
      onnode = 0;
      currentnode = unodes[onnode];
    }
    console.log(currentnode);

    const r = await axios.get(
      "https://" +
        currentnode +
        ".glitch.me/dreams?a=" +
        start +
        "&b=" +
        end +
        "&fallingasleep=" +
        discordwebhook + "&bl=" + blacklists + "&key=" + glitchkey + "&auth=" + glitchauth + "&fallingasleeplocked=" + lockedhook,
      { timeout: 10000 }
    );
    const response = r.data;
    onnode += 1;
    return response;
  } catch (err) {
    console.log(err.message);
    onnode += 1;
    return ["busy", 0];
  }
}

let basecounts = 0;

async function main() {
  try {
    let start = currentidx;
    currentidx += 10000
    const scans = await scangroups(start, currentidx);
    basecounts += parseInt(scans[1]);
    if (scans[0] != "ready") {
      currentidx -= 10000
    }
    
    if (currentidx > 17412877 && currentidx < 32000000) { //roblox skipped ids
      currentidx = 32000000
    }
    
    if (currentidx > maxnumber) {
      //reached end!
      currentidx = minnumber;
    }
    console.log(currentidx);
  } catch (err) {
    console.log(err);
  }
}

let a = 0;

function chunkArray(array, chunkSize) {
  const chunks = [];
  for (let i = 0; i < array.length; i += chunkSize) {
    chunks.push(array.slice(i, i + chunkSize));
  }
  return chunks;
}

let avgs = [];

let ipadds = [];

let laststart = currentidx;

async function awaken() {
  ipadds = [];
  unodes = [];
  const chunkedLinks = chunkArray(nodes, 50);

  let projectsProcessed = 0;

  let ips = [];

  for (const linksChunk of chunkedLinks) {
    const promises = linksChunk.map((link) => {
      let url = `https://${link}.glitch.me/getip`;

      return axios
        .get(url, { timeout: 60000 })
        .then((response) => {
          if (!ips.includes(response.data)) {
            ips.push(response.data);
            unodes.push(link);
            console.log([response.data, link]);
          }

          return response.data;
        })
        .catch((error) => {
          console.log(error.message);
          return null;
        });
    });

    const responses = await Promise.all(promises);

    projectsProcessed += linksChunk.length;
    const percentage = ((projectsProcessed / nodeslength) * 100).toFixed(2);
    console.log(
      `Progress: ${percentage}% (${projectsProcessed}/${nodeslength})`
    );
  }

  console.log("IP's: " + unodes.length);
}

async function loop() {
  while (true) {
    a += 1;

    await main();
    if (a >= unodes.length) {
      let data = {};

      avgs.push(basecounts);
      if (avgs.length > 100) {
        avgs.shift();
      }

      let sum = 0;
      for (let i = 0; i < avgs.length; i++) {
        sum += avgs[i];
      }
      
      const average = avgs.length > 0 ? sum / avgs.length : 0;
      const persec = Math.round(average / 60);
      const perhour = Math.round(average * 60);
      const perday = Math.round(perhour * 24);
      const perweek = Math.round(perday * 7);
      const permonth = Math.round(perweek * 4.34524);
      const peryear = Math.round(permonth * 12);

      const scannedthissec = Math.round(basecounts / 60);
      
      data["embeds"] = [
        {
          description:
            "We are now scanning id's: " +
            laststart.toLocaleString() +
            " to " +
            currentidx.toLocaleString() +
            "\n" +
            "IP's: " +
            unodes.length +
            "\n\n Avg's based off last 100 scans: \n Per Second: " +
            persec.toLocaleString() +
            "\n Per Minute: " +
            average.toLocaleString() +
            "\n Per hour: " +
            perhour.toLocaleString() +
            "\n Per Day: " +
            perday.toLocaleString() +
            "\n Per Week: " +
            perweek.toLocaleString() +
            "\n Per Month: " +
            permonth.toLocaleString() +
            "\n Per Year: " +
            peryear.toLocaleString(),
          title:
            "Scanned: " +
            basecounts.toLocaleString() +
            " Groups in 60 second's",
        },
      ];
      
      await axios.post(debughook, data);

      a = 0;
      console.log("waiting 1 minutes for next cycle!");

      for (let i = 60; i >= 1; i--) {
        await delay(1000);
        console.log("countdown: " + i);
      }

      basecounts = 0;
      laststart = currentidx;
    }
  }
}

loop();

awaken();
setInterval(awaken, 60 * 60 * 1000);
