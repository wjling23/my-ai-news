import feedparser
import requests
import time
import os
import re

print(">>> 脚本启动成功，正在初始化环境...")

# --- 配置区 ---
RSS_URL = "https://36kr.com/feed"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/xml,application/rss+xml,text/xml;q=0.9,*/*;q=0.8'
}

def send_dingtalk(entry):
    """发送 36氪 资讯到钉钉"""
    print(f"DEBUG: 正在准备推送: {entry.title}")
    
    # 清洗摘要
    summary_text = entry.get('summary', '点击链接查看详情')
    summary_text = re.sub('<[^<]+?>', '', summary_text) 
    
    if len(summary_text) > 200:
        summary_text = f"{summary_text[:200]}..."

    # 这里的标题前缀包含关键词 "AI"，确保钉钉放行
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AI 资讯更新 (36氪)",
            "text": f"### AI 提醒: {entry.title}\n\n"
                    f"> 发布时间: {entry.get('published', '刚刚')}\n\n"
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
        print("ERROR: DINGTALK_WEBHOOK 未配置!")
        return

    print(f"DEBUG: 开始抓取: {RSS_URL}")
    try:
        response = requests.get(RSS_URL, headers=HEADERS, timeout=25)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        print(f"DEBUG: 抓取成功，共有 {len(feed.entries)} 条文章")
        
        if not feed.entries:
            return

        # 36氪通常不带 id 属性，我们改用 link 属性作为唯一标识
        last_link = ""
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                last_link = f.read().strip()
            print(f"DEBUG: 上次记录的最后一条 Link: {last_link}")

        new_entries = []
        for entry in feed.entries:
            # 兼容性检查：如果没 id 就用 link
            current_id = getattr(entry, 'id', entry.link)
            if current_id == last_link:
                break
            new_entries.append(entry)

        if new_entries:
            print(f"DEBUG: 发现 {len(new_entries)} 条新内容")
            
            # 首次推送限流：只发最新的 3 条
            if not last_link:
                print("DEBUG: 首次运行，推送最新 3 条")
                new_entries = new_entries[:3]
            
            # 倒序推送
            for entry in reversed(new_entries):
                send_dingtalk(entry)
                time.sleep(1.5)
            
            # 记录最新的一条链接
            with open(STATUS_FILE, "w") as f:
                f.write(getattr(new_entries[0], 'id', new_entries[0].link))
            print("✅ 状态已保存，任务完成。")
        else:
            print("☕ 暂无新资讯。")

    except Exception as e:
        # 这里会打印更详细的报错信息方便我们定位
        import traceback
        print(f"❌ 程序崩溃: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
