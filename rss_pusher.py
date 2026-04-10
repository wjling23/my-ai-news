import feedparser
import requests
import time
import os
import re

print(">>> 脚本启动成功，正在初始化...")

# --- 配置区 ---
# 使用 RSSHub 提供的机器之心镜像，这个源在 GitHub Actions 里非常稳定且全是 AI 内容
RSS_URL = "https://rsshub.app/jiqizhixin/index"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def send_dingtalk(entry):
    """发送纯净的 AI 资讯"""
    print(f"DEBUG: 正在准备推送 AI 文章: {entry.title}")
    
    summary_text = entry.get('summary', '点击链接查看详情')
    summary_text = re.sub('<[^<]+?>', '', summary_text) 
    
    if len(summary_text) > 200:
        summary_text = f"{summary_text[:200]}..."

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AI 每日早报",
            "text": f"## AI 资讯: {entry.title}\n\n"
                    f"{summary_text}\n\n"
                    f"[点击阅读全文]({entry.link})"
        }
    }
    
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        print(f"DEBUG: 钉钉响应: {res.text}")
    except Exception as e:
        print(f"ERROR: 推送失败: {e}")

def main():
    if not WEBHOOK_URL:
        print("ERROR: 环境变量缺失!")
        return

    print(f"DEBUG: 正在抓取 AI 垂直源: {RSS_URL}")
    try:
        # RSSHub 有时会慢，我们给 40 秒超时
        response = requests.get(RSS_URL, headers=HEADERS, timeout=40)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        print(f"DEBUG: 抓取成功，共有 {len(feed.entries)} 条 AI 文章")
        
        if not feed.entries:
            return

        last_id = ""
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                last_id = f.read().strip()

        new_entries = []
        for entry in feed.entries:
            # RSSHub 的源通常有稳定的 id 或 link
            current_id = getattr(entry, 'id', entry.link)
            if current_id == last_id:
                break
            new_entries.append(entry)

        if new_entries:
            print(f"DEBUG: 发现 {len(new_entries)} 条新内容")
            
            # 如果是第一次推送（或者你刚换了源），为了不打扰，只发最新 1 条
            if not last_id:
                new_entries = new_entries[:1]
            
            for entry in reversed(new_entries):
                send_dingtalk(entry)
                time.sleep(1.5)
            
            with open(STATUS_FILE, "w") as f:
                f.write(getattr(new_entries[0], 'id', new_entries[0].link))
        else:
            print("☕ 暂无 AI 领域更新。")

    except Exception as e:
        print(f"❌ 运行异常: {e}")

if __name__ == "__main__":
    main()
