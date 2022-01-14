import asyncio
import json
import random

import requests
from websockets.legacy.client import connect

WS_URI = "wss://www.drfrostmaths.com/ws/script2"

pin = input("Enter the game ID: ")
nick = input("Enter a nickname: ")
pid = random.randint(int(1e5), int(1e6))


r = requests.post(
    "https://www.drfrostmaths.com/live-processjoin-new.php",
    data={"pin": pin},
)

gid = r.url.split("?gid=")[1]

async def heartbeat(ws):
    while not ws.closed:
        payload = {"status": "pulse", "gid": gid}
        await ws.send(json.dumps(payload))
        print("sent pulse")

        await asyncio.sleep(30000//1000)


async def main():
    ws = await connect(WS_URI)
    print("connection established to", WS_URI)
    identify = {"status": "join", "gid": gid, "nickname": nick, "pid": pid}
    await ws.send(json.dumps(identify))
    
    while not ws.closed:
        raw = await ws.recv()
        data = json.loads(raw)

        if data["status"] == "question":
            if data["question"]["answer"]["type"] == "numeric":
                answer = [data["question"]["answer"]["correctAnswer"][0]["exact"]]
            else:
                answer = data["question"]["answer"]["correctAnswer"]

            payload = {"status": "submitAnswer", "pid": pid, "data": answer, "qid": data["question"]["id"]}
            await ws.send(json.dumps(payload))
            print("received question...")
        
        elif data["status"] == "answerResponse":
            print("correctly answered question in", round(data["time"], 4), "seconds I have", data["totalPoints"], "points")
        
        elif data["status"] == "evicted":
            print("evicted from the game")
            await ws.close(code=1000)
        
        elif data["status"] == "joined":
            print("successfully joined the game")
        
        elif data["status"] == "completed":
            print("completed the game with rank", data["rank"], "and got", data["score"], "points")
            await ws.close(code=1000)
        

asyncio.run(main())
