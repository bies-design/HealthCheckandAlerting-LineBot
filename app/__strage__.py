#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh

import os
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    UnfollowEvent,
)

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# 初始化設定
configuration = Configuration(
    access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))


# ────────────────────────────────────────
# Webhook 進入點
# ────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK", 200


# ────────────────────────────────────────
# 處理文字訊息（Echo Bot 範例）
# ────────────────────────────────────────
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text
    reply_text = f"你說：{user_text}"  # 可改成你的業務邏輯

    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(type="text", text=reply_text)
                ],
            )
        )


# ────────────────────────────────────────
# 處理加入好友事件
# ────────────────────────────────────────
@handler.add(FollowEvent)
def handle_follow(event):
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(type="text", text="感謝加入！歡迎使用本服務 🎉")
                ],
            )
        )


# ────────────────────────────────────────
# 處理封鎖事件（無法回覆，只記錄）
# ────────────────────────────────────────
@handler.add(UnfollowEvent)
def handle_unfollow(event):
    print(f"使用者封鎖了 Bot：{event.source.user_id}")


# ────────────────────────────────────────
# 啟動伺服器
# ────────────────────────────────────────
if __name__ == "__main__":
    # 仅在直接运行时用，否则用 gunicorn
    app.run(host="0.0.0.0", port=168, debug=True)