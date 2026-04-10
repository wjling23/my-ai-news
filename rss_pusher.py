import feedparser
import requests
import time
import os
import re

print(">>> 量子位 AI 机器人列表版启动...")

# --- 配置区 ---
RSS_URL = "https://www.qbitai.com/feed"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def push_to_dingtalk(entries):
    """将多条资讯汇总成一个列表发送"""
    if not entries:
        return

    # 构建 Markdown 列表
    # 标题必须包含机器人关键词，假设你的关键词还是 "AI"
    content = ["### 🤖 量子位 AI 每日精选\n"]
    
    for i, entry in enumerate(entries, 1):
        # 清洗标题，去掉可能存在的 HTML 标签
        clean_title = re.sub('<[^<]+?>', '', entry.title)
        line = f"{i}. **{clean_title}** \n   [点击阅读全文]({entry.link})\n"
        content.append(line)

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AI 每日精选",
            "text": "\n".join(content)
        }
    }
    
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        print(f"DEBUG: 钉钉响应: {res.text}")
    except Exception as e:
        print(f"ERROR: 推送出错: {e}")

def main():
    if not WEBHOOK_URL:
        print("ERROR: DINGTALK_WEBHOOK 缺失!")
        return

    try:
        response = requests.get(RSS_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        print(f"DEBUG: 抓取成功，共有 {len(feed.entries)} 条资讯")
        
        if not feed.entries:
            return

        # 读取上次记录
        last_link = ""
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                last_link = f.read().strip()

        new_entries = []
        for entry in feed.entries:
            if entry.link == last_link:
                break
            new_entries.append(entry)

        if new_entries:
            print(f"DEBUG: 检测到 {len(new_entries)} 条新内容")
            
            # 限制最多展示 10 条
            display_entries = new_entries[:10]
            
            # 一次性汇总推送
            push_to_dingtalk(display_entries)
            
            # 更新最后一条记录（记录 RSS 中最顶端的那一条）
            with open(STATUS_FILE, "w") as f:
                f.write(feed.entries[0].link)
            print("✅ 推送完成，状态已保存")
        else:
            print("☕ 暂无新资讯。")

    except Exception as e:
        print(f"❌ 运行异常: {e}")

if __name__ == "__main__":
    main()
