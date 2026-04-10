import feedparser
import requests
import time
import os
import re

print(">>> 脚本启动成功，正在初始化...") # 这行如果没印出来，说明代码结构有问题

# --- 配置区 ---
RSS_URL = "https://www.jiqizhixin.com/rss"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def send_dingtalk(entry):
    print(f"正在准备推送: {entry.title}")
    summary_text = entry.get('summary', '点击链接查看详情')
    summary_text = re.sub('<[^<]+?>', '', summary_text) # 去除HTML

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
        print(f"钉钉返回结果: {res.text}")
    except Exception as e:
        print(f"推送出错: {e}")

def main():
    if not WEBHOOK_URL:
        print("错误: DINGTALK_WEBHOOK 环境变量缺失!")
        return

    print(f"开始抓取 RSS: {RSS_URL}")
    response = requests.get(RSS_URL, headers=HEADERS, timeout=20)
    feed = feedparser.parse(response.content)
    print(f"抓取完成，共有文章 {len(feed.entries)} 条")

    last_id = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            last_id = f.read().strip()
        print(f"上次推送 ID: {last_id}")

    new_entries = []
    for entry in feed.entries:
        if entry.id == last_id:
            break
        new_entries.append(entry)

    if new_entries:
        print(f"发现 {len(new_entries)} 条新文章")
        # 首次运行防止刷屏，只发最新的3条
        if not last_id:
            new_entries = new_entries[:3]
        
        for entry in reversed(new_entries):
            send_dingtalk(entry)
            time.sleep(1)
            
        with open(STATUS_FILE, "w") as f:
            f.write(new_entries[0].id)
    else:
        print("没有检测到新内容")

# ！！！重点检查：确保这两行没有缩进，且在文件最底部 ！！！
if __name__ == "__main__":
    main()
