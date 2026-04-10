import feedparser
import requests
import time
import os
import re

print(">>> 量子位 AI 机器人启动：正在初始化...")

# --- 配置区 ---
# 切换为量子位官方 RSS 源
RSS_URL = "https://www.qbitai.com/feed"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def send_dingtalk(entry):
    """推送量子位 AI 资讯"""
    print(f"DEBUG: 正在准备推送: {entry.title}")
    
    # 提取摘要并清洗 HTML
    summary_text = entry.get('summary', '点击链接查看详情')
    summary_text = re.sub('<[^<]+?>', '', summary_text) 
    
    if len(summary_text) > 200:
        summary_text = f"{summary_text[:200]}..."

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "量子位 AI 早报",
            "text": f"### AI 资讯: {entry.title}\n\n"
                    f"{summary_text}\n\n"
                    f"[点击阅读全文]({entry.link})"
        }
    }
    
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        print(f"DEBUG: 钉钉响应: {res.text}")
    except Exception as e:
        print(f"ERROR: 推送出错: {e}")

def main():
    if not WEBHOOK_URL:
        print("ERROR: 环境变量 DINGTALK_WEBHOOK 缺失!")
        return

    print(f"DEBUG: 正在抓取量子位源: {RSS_URL}")
    try:
        # 增加超时时间，防止 GitHub 访问国内源波动
        response = requests.get(RSS_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        print(f"DEBUG: 抓取成功，当前共有 {len(feed.entries)} 条资讯")
        
        if not feed.entries:
            print("WARNING: 未发现文章内容")
            return

        # 读取上次记录
        last_link = ""
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                last_link = f.read().strip()

        new_entries = []
        for entry in feed.entries:
            # 记录 Link 作为唯一标识
            if entry.link == last_link:
                break
            new_entries.append(entry)

        if new_entries:
            print(f"DEBUG: 检测到 {len(new_entries)} 条新内容")
            
            # 首次运行限流：只推送最新的 1 条
            if not last_link:
                print("DEBUG: 首次运行，推送最新 1 条进行测试")
                new_entries = new_entries[:1]
            
            # 倒序推送
            for entry in reversed(new_entries):
                send_dingtalk(entry)
                time.sleep(2)
            
            # 更新最后一条记录
            with open(STATUS_FILE, "w") as f:
                f.write(feed.entries[0].link)
            print("✅ 状态保存成功")
        else:
            print("☕ 暂无新资讯。")

    except Exception as e:
        print(f"❌ 运行异常: {e}")

if __name__ == "__main__":
    main()
