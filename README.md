# Line Bot
> 方便使用和擴充為主 <br/>
* 使用 docker container 管理，方便移動和設置
* 容易驗證測試和正式出版
* 使用 python3.0+

## Structure
```
/:.
│  .gitignore
│  docker-compose.yml
│  Dockerfile
│  README.md
│  requirements.txt
│  utility_get_git_latest_tag_name.sh
│  utility_loopback.sh
│  utility_namespace_dns.sh
│
└─app
    │  .env
    │  prod.py
    │  __init__.py
    │  __main__.py
    │
    ├─common
    │      loger.py
    │      myqueue.py
    │
    ├─module
           redis.py
           sysmonitor.py

```

## Tips
* configuration
> 需要建立 app/.env，建構內容請參考如下，其中數值如何取得請看其他文件
```
SERVER_PORT=168         # 服務監聽 Port
# CRITICAL=FATAL > ERROR > WARNING=WARN > INFO > DEBUG > NOTSET
# 50               40      30             20     10      0
LOGGER_LEVEL=DEBUG      # 紀錄層級，表示只顯示大於等於所選階層的訊息
TIMEZONE=Asia/Taipei    # 時間區域
REFRESH_SECONDS=2       # 每次檢查完的間隔時間
LINE_CHANNEL_SECRET= 申請 LINE Official Message API Channel 時可得
LINE_CHANNEL_ACCESS_TOKEN= 需要 LINE Developers 針對 Message API 生成
```
* 延伸功能 <br/>
a. module/redis.py 負責所有對redis 的讀寫動作，外部只能讀取，寫入動作是 timer 控制 <br/>
b. module/sysmonitor.py 對於所有需要監控的項目整合在此，只負責擷取資訊 <br/>
c. common/jobsmanager.py 由主thread 喚醒後，按照設置去輪巡(Timer) sysmonitor.py 的項目<br/>


* startup [prod]
> 已經記錄在 docker-compose.yml ，直接執行或是接續到整合方案中 (eg. k8s, coolify...)
```
~> docker compose build                # 如果抓不到開放的環境印象檔案
~> docker compose up -d
```

* develop [dev -> Staging]
> 利用準備好的環境進行測試
```
~> docker compose build   
~> docker run -v ./app:/usr/local/app  -it markhsieh4good/python:3.13-slim-devenv bash
```
> 進入模擬的container 中...
```
~:/usr/local# python3 app/__strage__.py

 * Serving Flask app '__strage__'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:168
 * Running on http://172.17.0.2:168
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 119-215-888
```
> 更新模組相依性紀錄 <br/>
> 請上網查詢對應需求功能的模組名稱。eg. r/w yaml file --> PyYAML
```
~:/usr/local# python3 -m pip install [Module Name]
~:/usr/local# python3 -m pip freeze 
~:/usr/local# exit
```
把輸出的版本資訊轉貼到 requirements.txt，此檔案要更新到 repo. <br/>
下次啟動服務前要先 docker compose build，把新增的模組合併到預設環境中 <br/>

## Version

20260302-0b
20260305-0a