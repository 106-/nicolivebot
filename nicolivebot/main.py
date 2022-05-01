from nicolivebot.nicolive_session import NicoLiveCommentSession

import logging
import asyncio

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 新しいコメントが投稿されるとこの関数が毎回呼ばれる
    def on_chat_posted(nlcs: NicoLiveCommentSession, chat: str):
        print(chat)

    nlcs = NicoLiveCommentSession("lv336761497", on_chat_posted)
    asyncio.run(nlcs.gather())
