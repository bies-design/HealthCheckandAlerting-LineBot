#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh
# This module is used to schedule the polling action, and push the job to queue for JobsManager to do the job.
########################

# System Modules
import logging
import os
import json

from datetime import datetime, timezone, timedelta
import sys
import time
import threading

import yaml
import re

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

class PollingScheduler(object):
    def __init__(self, is_stop_event, timezone, logger_level, refresh_seconds) -> None:
        super().__init__()

        self.__queue_request = None
        self.__chatpool = []  # To distinguish between response actions, private channels and broadcast channels

        self.__logger = self.__create_logger(logger_level, timezone)
        self.__is_stop_event = is_stop_event
        self.__refresh_seconds = int(refresh_seconds)

    def __create_logger(self, logger_level=logging.INFO, timezone='UTC'):
        """創建專屬於此類的 logger"""
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        logger.setLevel(logger_level)
        logger.propagate = False  # 禁用 propagate，防止消息傳遞給父 logger
        
        # 只有在沒有處理器時才添加（避免重複）
        if not logger.handlers:
            # 創建 StreamHandler
            handler = logging.StreamHandler(sys.stdout)
            
            # 設定時區格式器
            formatter = TimezoneFormatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                timezone=timezone  # 或從環境變數獲取
            )
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
        
        return logger

    def __information(self):

        self.__logger.info("Hello, this is polling action scheduler. Ready to serve ...")

    def run(self, jobs_queue, is_sys_stop):
        # stop_signals=[SIGINT, SIGTERM, SIGABRT]
        thread_id = threading.current_thread().ident
        thread_name = threading.current_thread().name
        print(f"[DEBUG] run() called in thread: {thread_name} (ID: {thread_id})")
        
        self.__isRunning = True
        self.__queue_request = jobs_queue
        self.__information()
        self.__tasksList = None
        self.__josList = []

        while self.__isRunning:
            try:
                if self.__is_stop_event.is_set() is True:
                    self.__isRunning = False

                elif is_sys_stop() is True:
                    self.__isRunning = False
                    self.__logger.info("Sys. already enter stop steps. PollingActionScheduler will stop itself... ")
                    self.__release()
                else:
                    # TODO:
                    ## 1. create some task which is obied by config/tasklist.yml
                    self.__tasksList = self.__load_task_from_config()

                    ## 2. package task to queue, and let JobsManager to do the job.
                    self.__josList = self.__task_mapping_table(self.__tasksList)

                    ## 3. make the task change log when first time create and modify.
                    self.__push_job_to_queue(self.__josList)

                    time.sleep(self.__refresh_seconds)
            except Exception as msg:
                self.__logger.warning("some thing wrong when run polling scheduler. \n".format(__name__)
                                   + "\t\t {}".format(msg))
                time.sleep(self.__refresh_seconds)
                # self.stop()

    def __delay_stop(self, delay=0):
        l_start = int(round(time.time()))
        l_end = round(l_start + delay)
        l_run = True
        while l_run is True and delay > 0:
            l_current = int(round(time.time()))
            if l_current > l_end:
                l_run = False
            else:
                time.sleep(0.5)
        if self.__is_stop_event.is_set() is False:
            self.__is_stop_event.set()  # set stop event to true, and let main thread know to stop the system.
            # signal.alarm(signal.SIGINT)

    def __release(self):
        self.__logger.info("{} stoping...".format(__name__))
        try:
            self.__delay_stop(delay=0)
            self.__chatpool = []
        except RuntimeError:
            self.__logger.warning("already close object from {}".format(__name__))
        except Exception as msg:
            self.__logger.warning("some thing wrong when stop close object from {}. \n".format(__name__)
                               + "\t\t {}".format(msg))

    def stop(self):
        self.__release()

    def __del__(self):
        self.__release()

    def __load_task_from_config(self):
        # Initial all option from configuration file (*.yaml)
        tasks_setting_folder = os.path.dirname(os.path.abspath(__file__))
        yaml_data = None
        with open("{}/../config/tasklist.yaml".format(tasks_setting_folder), "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        return self.__parse_task_from_config(yaml_data)

    def __task_mapping_table(self, tasksList):
        rstDict = {}
        for task in tasksList:
            if task.get("type") == "syscheck":
                rstDict["syscheck"] = task.get("content")
            elif task.get("type") == "appcheck":
                rstDict["appcheck"] = task.get("content")
        return rstDict

    def __push_job_to_queue(self, jobs) -> None:
        self.__pushToQueueReq(jobs, important=False)

    def __parse_task_from_config(self, config) -> list:
        tasks = []
        for task_name, task_params in config.items():
            if re.search(task_name, "syscheck", re.IGNORECASE):
                content_list = task_params.split(",")
                tasks.append({
                    "type": "syscheck",
                    "content": content_list
                })
            elif re.search(task_name, "appcheck", re.IGNORECASE):
                content_list = task_params.split(",")
                tasks.append({
                    "type": "appcheck",
                    "content": content_list
                })
        return tasks
    
    def __pushToQueueReq(self, item: dict, important=False):
        '''
        __pushToQueueReq (item: dict, important: boolean)
        PARAMETER: 
            'item' is dict data
            'important' mean task permission
        OUTPUT:
            NONE
        '''
        # TODO self.__queue_request
        l_res = False
        l_msg = "None"
        # It can be used to parse a Python Dictionary string and convert it into a valid JSON.
        l_dict_2_json = json.dumps(item)
        self.__logger.info("push job to queue: {}".format(l_dict_2_json))

        try:
            l_res, l_msg = self.__queue_request.push(l_dict_2_json, important)
            if l_res is False:
                self.__logger.warning("add request into queue some thing wrong. {}".format(l_msg))
        except Exception as msg:
            self.__logger.error("add request into queue fail. {}".format(msg))