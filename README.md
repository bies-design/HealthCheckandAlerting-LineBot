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
SERVER_PORT=168         # 只限於 dev階段預設，prod 看docker-compose 設定
LINE_CHANNEL_SECRET= 申請 LINE Official Message API Channel 時可得
LINE_CHANNEL_ACCESS_TOKEN= 需要 LINE Developers 針對 Message API 生成
```

* startup [prod]
> 已經記錄在 docker-compose.yml ，直接執行或是接續到整合方案中 (eg. k8s, coolify...)
```
~> docker build                # 如果抓不到開放的環境印象檔案
~> docker compose run -d
```

* develop [dev -> Staging]
> 利用準備好的環境進行測試
```
~> docker build   
~> docker run -v ./app:/usr/local/app  -it markhsieh4good/python:3.13-slim-devenv /bin/bash
```
> 進入模擬的container 中...
```
~:/usr/local# # python3 app/__strage__.py

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

## Version

20260302-01