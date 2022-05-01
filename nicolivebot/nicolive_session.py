import asyncio
from datetime import datetime
import json
import requests

import websockets
from bs4 import BeautifulSoup
from nicolivebot.config import Config


# https://qiita.com/nouyakko/items/e4b24484c5f7eae0a3d1
class NicoLiveCommentSession:
    initial_data_system: str = {
        "type": "startWatching",
        "data": {
            "stream": {
                "quality": "abr",
                "protocol": "hls",
                "latency": "low",
                "chasePlay": False,
            },
            "room": {"protocol": "webSocket", "commentable": True},
            "reconnect": False,
        },
    }

    initial_data_comment = [
        {"ping": {"content": "rs:0"}},
        {"ping": {"content": "ps:0"}},
        {
            "thread": {
                "thread": None,
                "version": "20061206",
                "user_id": "guest",
                "res_from": -150,
                "with_global": 1,
                "scores": 1,
                "nicoru": 0,
            }
        },
        {"ping": {"content": "pf:0"}},
        {"ping": {"content": "rf:0"}},
    ]

    data_post_comment = {"type": "postComment", "data": {"text": None, "vpos": None, "isAnonymous": True}}
    login_uri = "https://account.nicovideo.jp/login/redirector"

    def __init__(self, live_id, on_chat_posted) -> None:

        # ニコニコにログインする
        session = requests.session()
        data = {"mail_tel": Config().niconico_mail, "password": Config().niconico_password}
        session.post(self.login_uri, data=data)

        # htmlを取ってきてWebSocket接続のための情報を取得
        # ここでログインしてないとコメントが投稿できないWebSocketのURIが帰ってくる
        response = session.get(f"https://live2.nicovideo.jp/watch/{live_id}")
        soup = BeautifulSoup(response.text, "html.parser")
        embedded_data = json.loads(soup.find("script", id="embedded-data")["data-props"])

        # ログインできていればこのURIに自分のIDが含まれている(できていなければ`anonymous-user`が含まれている)
        self.ws_system_uri = embedded_data["site"]["relive"]["webSocketUrl"]
        self.ws_comment_uri = None
        self.ws_system = None
        self.ws_comment = None
        self.on_chat_posted = on_chat_posted
        self.vpos_basetime = None
        self.chats = asyncio.Queue()

    # 3つの関数を並列で実行するための関数
    async def gather(self):
        await asyncio.gather(self.connect_ws_system(), self.connect_ws_comment(), self.comment_loop())

    # 視聴セッションとのWebSocket接続関数
    async def connect_ws_system(self):
        # 視聴セッションとのWebSocket接続を開始
        async with websockets.connect(self.ws_system_uri) as ws:
            self.ws_system = ws

            # 最初のメッセージを送信
            await ws.send(json.dumps(self.initial_data_system))

            # 視聴セッションとのWebSocket接続中ずっと実行
            while True:
                msg = json.loads(await ws.recv())

                # コメントセッションへ接続するために必要な情報が送られてきたら抽出してグローバル変数へ代入
                if msg["type"] == "room":
                    self.ws_comment_uri = msg["data"]["messageServer"]["uri"]
                    self.initial_data_comment[2]["thread"]["thread"] = msg["data"]["threadId"]
                    self.vpos_basetime = datetime.fromisoformat(msg["data"]["vposBaseTime"][:-6])

                # pingが送られてきたらpongとkeepseatを送り、視聴権を獲得し続ける
                if msg["type"] == "ping":
                    pong = json.dumps({"type": "pong"})
                    keepSeat = json.dumps({"type": "keepSeat"})
                    await ws.send(pong)
                    await ws.send(keepSeat)

    # コメントセッションとのWebSocket接続関数
    async def connect_ws_comment(self):

        while not self.ws_comment_uri:
            # 視聴セッションがグローバル変数に代入されていなければ0.01秒待つ
            await asyncio.sleep(0.01)

        # コメントセッションとのWebSocket接続を開始
        async with websockets.connect(self.ws_comment_uri) as ws:
            self.ws_comment = ws

            # 最初のメッセージを送信
            await ws.send(json.dumps(self.initial_data_comment))

            # コメントセッションとのWebSocket接続中ずっと実行
            while True:
                msg = json.loads(await ws.recv())

                # "chat"を持つオブジェクトが来たらQueueに格納
                if "chat" in msg:
                    await self.chats.put(msg)

    # 新しいコメントに反応する関数
    async def comment_loop(self):
        while True:
            chat = await self.chats.get()
            self.on_chat_posted(self, chat)

    # コメントを投稿する
    async def post_chat(self, chat: str):
        if not self.ws_system or not self.vpos_basetime:
            raise ValueError()
        vpos = int(datetime.now().timestamp() - self.vpos_basetime.timestamp() + 1) * 100
        self.data_post_comment["data"]["text"] = chat
        self.data_post_comment["data"]["vpos"] = vpos
        await self.ws_system.send(json.dumps(self.data_post_comment))
