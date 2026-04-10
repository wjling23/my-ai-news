import feedparser
import requests
import time
import os
import re

print(">>> AI 机器人启动：正在初始化...")

# --- 配置区 ---
# 36氪 AI 频道源 (经测试在 GitHub Actions 访问相对稳定)
RSS_URL = "https://36kr.com/columns/ai/feed"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def send_dingtalk(entry):
    """推送高质量 AI 资讯"""
    print(f"DEBUG: 正在推送 AI 文章: {entry.title}")
    
    summary_text = entry.get('summary', '点击链接查看全文')
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
        print(f"ERROR: 推送出错: {e}")

def main():
    if not WEBHOOK_URL:
        print("ERROR: 环境变量 DINGTALK_WEBHOOK 缺失!")
        return

    print(f"DEBUG: 正在抓取 36氪 AI 垂直频道: {RSS_URL}")
    try:
        response = requests.get(RSS_URL, headers=HEADERS, timeout=30)
        # 如果 36kr 还是拦截，这里会抛出异常
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        print(f"DEBUG: 抓取成功，共有 {len(feed.entries)} 条 AI 文章")
        
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
            # 36氪使用 link 作为唯一标识比较稳妥
            current_id = getattr(entry, 'link', '')
            if current_id == last_link:
                break
            new_entries.append(entry)

        if new_entries:
            print(f"DEBUG: 发现 {len(new_entries)} 条新内容")
            
            # 首次运行或切换源，仅推 1 条防止骚扰
            if not last_link:
                new_entries = new_entries[:1]
            
            for entry in reversed(new_entries):
                send_dingtalk(entry)
                time.sleep(1.5)
            
            # 保存最后一条的链接
            with open(STATUS_FILE, "w") as f:
                f.write(new_entries[0].link)
            print("✅ 状态保存成功")
        else:
            print("☕ 暂无 AI 更新")

    except Exception as e:
        print(f"❌ 运行异常: {e}")
        # 如果还是 403，建议联系我尝试更底层的代理或换源

if __name__ == "__main__":
    main()
