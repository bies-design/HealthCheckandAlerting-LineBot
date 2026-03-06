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
from datetime import datetime, timezone, timedelta

########
# Multi-Threading Modules
########
from threading import Thread, Event, Lock

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
# from module.jobsmanager import JobsManager
from module.pollingScheduler import PollingScheduler
from common.myqueue import MyQueue

# 載入環境變數
load_dotenv()

# 自定義時區格式器
class TimezoneFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, timezone='UTC'):
        super().__init__(fmt, datefmt)
        self.timezone = timezone
        # 設定時區偏移（簡單實現，支援 UTC 和固定偏移）
        if timezone == 'UTC':
            self.tz_offset = 0
        elif timezone == 'Asia/Taipei':
            self.tz_offset = 8  # UTC+8
        elif timezone == 'America/New_York':
            self.tz_offset = -5  # UTC-5 (標準時間)
        else:
            # 預設 UTC
            self.tz_offset = 0

    def formatTime(self, record, datefmt=None):
        # 取得記錄時間並轉換時區
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        dt = dt + timedelta(hours=self.tz_offset)
        
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            s = dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 添加毫秒
        if self.default_msec_format:
            s = self.default_msec_format % (s, record.msecs)
        return s

# 全局變數
StopSys = False
JobsManagerStopEvent = Event()
PollingActionSchedulerStopEvent = Event()
LoggerLevel = os.getenv("LOGGER_LEVEL", "INFO").upper()
Logger_Level_Numeric = getattr(logging, LoggerLevel, logging.INFO)
timezone_str = os.getenv("TIMEZONE", "UTC")
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "1"))
TaskQueue = MyQueue(Logger_Level_Numeric, timezone_str, 100, 0)  # 任務佇列:  order is base on request him self.
Scheduler_Initialized = False  # 防止重複初始化標誌
Scheduler_Lock = Lock()  # 線程鎖確保初始化線程安全
print(f"[DEBUG] Module __strage__ loaded at {datetime.now()}")

# 啟用loging 模組
logging.basicConfig(
                    level=Logger_Level_Numeric,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    # Send to file and ttyS0...
                    handlers=[
                        # logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
                        logging.StreamHandler(sys.stdout)
                    ]
        )

# 設定時區格式器（可從環境變數設定）
formatter = TimezoneFormatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    timezone=timezone_str
)

# 應用格式器到所有處理器
for handler in logging.getLogger().handlers:
    handler.setFormatter(formatter)

logger = logging.getLogger(__name__)


# # 可控資源釋出操作
# def stop_self():
#     os.kill(os.getpid(), signal.SIGINT)

def cb_is_sys_stop():
    return StopSys

def signal_handler(signum, frame):
    global logger
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
        os._exit(0)
    else:
        print('just alarm for test')

# system signal reader
signal.signal(signal.SIGALRM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGABRT, signal_handler)
# signal.alarm(signal.SIGALRM)  # for test, it will trigger signal_handler every 1 second.

# =======================================
# Thread 1: Jobs Manager
# =======================================
def cb_is_polling_stop():
    global logger
    if not cb_is_sys_stop():
        return False
    elif not PollingActionSchedulerStopEvent.is_set():
        logger.info("Polling-Action Scheduler not stop yet. ...")
        return False
    else:
        return True

# JobsManager = JobsManager(is_stop_event=JobsManagerStopEvent, 
#                           timezone=Logger_Level_Numeric,
#                           timezone=os.getenv("TIMEZONE", "UTC"),
#                           refresh_seconds=REFRESH_SECONDS) 
# # refresh_seconds need to be shot because loop already blocking by element length fo queue.
# JobsManagerThread = Thread(
#     target=JobsManager.run, 
#     args=(TaskQueue, cb_is_polling_stop), 
#     name="JobsManager01")

# =======================================
# Thread 2: Polling Actions Scheduler
# =======================================

PollingActionScheduler = None
PollingActionSchedulerThread = None

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
def webhook():   # auto mapping to /webhook by flask
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
def handle_text_message(event):   # overwrite the default handler for receive message event
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
def handle_follow(event):   # overwrite the default handler for receive follow event
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
def handle_unfollow(event):  # overwrite the default handler for receive unfollow event
    print(f"使用者封鎖了 Bot：{event.source.user_id}")


# ────────────────────────────────────────
# 啟動伺服器
# ────────────────────────────────────────
if __name__ == "__main__":
    # 仅在直接运行时用，否则用 gunicorn
    # 使用 Lock 確保初始化線程安全
    with Scheduler_Lock:
        if not Scheduler_Initialized:
            # 初始化 PollingActionScheduler
            PollingActionScheduler = PollingScheduler(is_stop_event=PollingActionSchedulerStopEvent, 
                                                            logger_level=Logger_Level_Numeric,
                                                            timezone=os.getenv("TIMEZONE", "UTC"),
                                                            refresh_seconds=REFRESH_SECONDS)
            logger.debug("create PollingActionScheduler")
            
            PollingActionSchedulerThread = Thread(
                target=PollingActionScheduler.run, 
                args=(TaskQueue, cb_is_sys_stop), 
                name="PollingActionScheduler01")
            logger.debug("set PollingActionSchedulerThread")
            
            # JobsManagerThread.start()
            PollingActionSchedulerThread.start()
            logger.debug("start PollingActionSchedulerThread")
            Scheduler_Initialized = True
            logger.info("PollingActionScheduler initialization complete")

    app.run(host="0.0.0.0", port=os.getenv("SERVER_PORT"), debug=False, use_reloader=False)