import feedparser
import requests
import time
import os
import re

print(">>> 脚本启动成功，正在初始化环境...")

# --- 配置区 ---
RSS_URL = "http://www.jiqizhixin.com/rss"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

# 更加逼真的浏览器伪装
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'application/xml,application/rss+xml,text/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def send_dingtalk(entry):
    print(f"DEBUG: 正在准备推送: {entry.title}")
    # 提取摘要并去标签
    summary_text = entry.get('summary', '点击链接查看详情')
    summary_text = re.sub('<[^<]+?>', '', summary_text) 

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AI 资讯更新",
            "text": f"## AI 资讯: {entry.title}\n\n"
                    f"{summary_text[:200]}...\n\n"
                    f"[点击阅读全文]({entry.link})"
        }
    }
    
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        print(f"DEBUG: 钉钉返回: {res.text}")
    except Exception as e:
        print(f"ERROR: 推送出错: {e}")

def main():
    if not WEBHOOK_URL:
        print("ERROR: DINGTALK_WEBHOOK 缺失!")
        return

    print(f"DEBUG: 正在使用 requests 抓取: {RSS_URL}")
    try:
        # 1. 先用 requests 强行下载 XML 内容
        response = requests.get(RSS_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # 2. 将下载的内容交给 feedparser 解析
        feed = feedparser.parse(response.content)
        print(f"DEBUG: 抓取成功，文章条数: {len(feed.entries)}")
        
    except Exception as e:
        print(f"ERROR: 抓取过程崩溃: {e}")
        return

    if not feed.entries:
        print("WARNING: 依然没有抓取到文章，请检查 RSS 地址或网站状态。")
        return

    # 3. 读取排重记录
    last_id = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            last_id = f.read().strip()
        print(f"DEBUG: 上次推送记录 ID: {last_id}")

    new_entries = []
    for entry in feed.entries:
        if entry.id == last_id:
            break
        new_entries.append(entry)

    if new_entries:
        print(f"DEBUG: 发现 {len(new_entries)} 条新内容")
        # 首次运行仅推送最新的3条
        if not last_id:
            new_entries = new_entries[:3]
        
        for entry in reversed(new_entries):
            send_dingtalk(entry)
            time.sleep(1.5)
            
        # 更新 ID
        with open(STATUS_FILE, "w") as f:
            f.write(new_entries[0].id)
    else:
        print("DEBUG: 所有的文章都已经推送过了。")

if __name__ == "__main__":
    main()
