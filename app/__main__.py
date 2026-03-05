#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh

########
# System Modules
########
import os, sys
from flask import Flask, request, abort
from dotenv import load_dotenv
import logging
import signal
from datetime import datetime

########
# Multi-Threading Modules
########
from threading import Thread, Event

########
# Third-Party Modules
########
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

########
# Custom Modules
########
from app.module.jobsmanager import JobsManager
from app.module.pollingScheduler import PollingActionScheduler
from app.common.myqueue import MyQueue

# 載入環境變數
load_dotenv()

# 啟用loging 模組
logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    # Send to file and ttyS0...
                    handlers=[
                        # logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
                        logging.StreamHandler(sys.stdout)
                    ]
        )
logger = logging.getLogger(__name__)

# 全局變數
StopSys = False
TaskQueue = MyQueue(logger, 100, 0.25)  # 任務佇列


# 可控資源釋出操作
def stop_self():
    os.kill(os.getpid(), signal.SIGINT)

def isStopSys():
    return StopSys

def signal_handler(signum, frame):
    logger.warning('signal_handler: caught signal ' + str(signum))
    global StopSys
    if signum == signal.SIGINT.value:
        print('... SIGINT')
        StopSys = True
    elif signum == signal.SIGTERM.value:
        print('... SIGTERM')
        StopSys = True
    elif signum == signal.SIGABRT.value:
        print('... SIGABRT')
        StopSys = True
    elif signum == signal.SIGALRM.value:
        print('... SIGALRM')
        StopSys = False
    else:
        print('???')

    if StopSys:
        logging.info("Signal : '{}' Received. Handler Executed @ {}".format(signal.strsignal(signum), datetime.now()))
    else:
        print('just alarm for test')


# =======================================
# Thread 1: Jobs Manager
# =======================================

JobsManagerStopEvent = Event()
JobsManagerThread = Thread(
    target=JobsManager.run, 
    args=(JobsManagerStopEvent, TaskQueue, isStopSys), 
    name="[JobsManager]... Thread")
JobsManagerThread.start()

# =======================================
# Thread 2: Polling Actions Scheduler
# =======================================
def cb_is_stop():
    if not isStopSys():
        return False
    elif not JobsManagerStopEvent.is_set():
        logger.info("JobsManager not stop yet. ...")
        return False
    else:
        return True

PollingActionSchedulerStopEvent = Event()
PollingActionSchedulerThread = Thread(
    target=PollingActionScheduler.run, 
    args=(PollingActionSchedulerStopEvent, TaskQueue, cb_is_stop), 
    name="[PollingActionScheduler]... Thread")
PollingActionSchedulerThread.start()

# =======================================
# Thread 3: Listener Http Rx
# =======================================

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
# if __name__ == "__main__":
#     # 仅在直接运行时用，否则用 gunicorn
#     app.run(host="0.0.0.0", port=os.getenv("SERVER_PORT"), debug=True)

# system signal reader
signal.signal(signal.SIGALRM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGABRT, signal_handler)
signal.alarm(signal.SIGALRM)