import feedparser
import requests
import time
import hmac
import hashlib
import base64
import os

# 配置区
RSS_URL = "https://www.jiqizhixin.com/rss"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
SECRET = os.getenv("DINGTALK_SECRET")
STATUS_FILE = "last_id.txt"

def get_sign():
    timestamp = str(round(time.time() * 1000))
    secret_enc = SECRET.encode('utf-8')
    string_to_sign = f'{timestamp}\n{SECRET}'.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign, digestmod=hashlib.sha256).digest()
    return timestamp, base64.b64encode(hmac_code).decode('utf-8')

def send_dingtalk(entry):
    timestamp, sign = get_sign()
    url = f"{WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"
    
    # 构建消息：机器之心通常会有精美的头图，可以加入 Markdown
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AI咨询（RSS-机器之心）更新",
            "text": f"## {entry.title}\n\n"
                    f"> 发布时间: {entry.published}\n\n"
                    f"{entry.summary[:200]}...\n\n"
                    f"[点击阅读全文]({entry.link})"
        }
    }
    requests.post(url, json=payload)

def main():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return

    # 读取上一次推送成功的 ID
    last_id = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            last_id = f.read().strip()

    new_entries = []
    for entry in feed.entries:
        if entry.id == last_id:
            break
        new_entries.append(entry)

    # 倒序推送（保证时间线正确），并更新状态
    if new_entries:
        for entry in reversed(new_entries):
            send_dingtalk(entry)
            print(f"推送成功: {entry.title}")
            time.sleep(1) # 避开频率限制
            
        with open(STATUS_FILE, "w") as f:
            f.write(new_entries[0].id) # 将最新的 ID 写入文件

if __name__ == "__main__":
    main()
