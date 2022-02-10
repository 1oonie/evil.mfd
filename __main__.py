import asyncio
import random
import contextlib

import requests
import aiohttp

WS_URI = "ws://www.drfrostmaths.com/ws/script2"
builtin_print = print

nicknames = input("Nicknames (separated by space): ").split(" ")
pin = input("Enter the game ID: ")
pid = random.randint(int(1e5), int(1e6))

with contextlib.redirect_stdout(None):
    r = requests.post(
        "https://www.drfrostmaths.com/live-processjoin-new.php",
        data={"pin": pin}, verify=False
    )

    gid = r.url.split("?gid=")[1]


async def heartbeat(ws: aiohttp.ClientWebSocketResponse):
    while not ws.closed:
        payload = {"status": "pulse", "gid": gid}
        await ws.send_json(payload)

        await asyncio.sleep(30000 // 1000)

async def handle(nick, wait_time):
    def print(*args, **kwargs):
        builtin_print(f"[{nick}]", *args, **kwargs)

    session = aiohttp.ClientSession()
    ws = await session.ws_connect(WS_URI, ssl=False)

    pid = random.randint(int(1e5), int(1e6))

    identify = {"status": "join", "gid": gid, "nickname": nick, "pid": pid}
    await ws.send_json(identify)

    asyncio.create_task(heartbeat(ws))

    while not ws.closed:
        data = await ws.receive_json()

        if data["status"] == "question":
            if data["question"]["answer"]["type"] == "numeric":
                answer = [data["question"]["answer"]["correctAnswer"][0]["exact"]]
            elif data["question"]["answer"]["type"] == "textual":
                answer = [
                    data["question"]["answer"]["correctAnswer"][0].split(" OR ")[0]
                ]
            elif data["question"]["answer"]["type"] == "expression":
                answer = data["question"]["answer"]["correctAnswer"]["main"]
            else:
                answer = data["question"]["answer"]["correctAnswer"]

            await asyncio.sleep(wait_time)
            payload = {
                "status": "submitAnswer",
                "pid": pid,
                "data": answer,
                "qid": data["question"]["id"],
            }
            await ws.send_json(payload)

        elif data["status"] == "answerResponse":
            print(
                "answered question in",
                round(data["time"], 4),
                "seconds I have",
                data["totalPoints"],
                "points",
            )

        elif data["status"] == "evicted":
            print("evicted from the game")
            await ws.close(code=1000)

        elif data["status"] == "joined":
            print("successfully joined the game")

        elif data["status"] == "completed":
            print(
                "completed the game with rank",
                data["rank"],
                "and got",
                data["score"],
                "points",
            )
            await ws.close(code=1000)

    await session.close()

async def main():    
    coros = []
    for wait_time, nick in enumerate(nicknames, start=1):
        coros.append(handle(nick, wait_time))
    
    await asyncio.gather(*coros)


asyncio.run(main())
