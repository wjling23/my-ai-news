import feedparser
import requests
import time
import os
import re

print(">>> 脚本启动成功，正在初始化...")

# --- 配置区 ---
# 36氪全站快讯源
RSS_URL = "https://36kr.com/feed"
# 对应 GitHub Secrets 中的 DINGTALK_WEBHOOK
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

# 模拟真实浏览器，防止被拦截
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/xml,application/rss+xml,text/xml;q=0.9,*/*;q=0.8'
}

def send_dingtalk(entry):
    """发送 36氪 资讯到钉钉"""
    print(f"DEBUG: 准备推送文章: {entry.title}")
    
    # 获取摘要并清洗 HTML 标签
    summary_text = entry.get('summary', '点击链接查看详情')
    summary_text = re.sub('<[^<]+?>', '', summary_text) 
    
    # 限制字数，防止消息过长
    if len(summary_text) > 200:
        summary_text = f"{summary_text[:200]}..."

    # 构建消息：确保标题包含你的钉钉机器人关键词 "AI"
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AI 资讯更新 (36氪)",
            "text": f"### AI 资讯: {entry.title}\n\n"
                    f"> 发布时间: {entry.get('published', '刚刚')}\n\n"
                    f"{summary_text}\n\n"
                    f"[点击阅读全文]({entry.link})"
        }
    }
    
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        print(f"DEBUG: 钉钉返回结果: {res.text}")
    except Exception as e:
        print(f"ERROR: 推送出错: {e}")

def main():
    if not WEBHOOK_URL:
        print("ERROR: 环境变量 DINGTALK_WEBHOOK 缺失，请检查 GitHub Secrets 配置。")
        return

    print(f"DEBUG: 正在尝试抓取 36氪 RSS: {RSS_URL}")
    try:
        # 使用 requests 获取内容，应用 Headers
        response = requests.get(RSS_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        # 解析内容
        feed = feedparser.parse(response.content)
        print(f"DEBUG: 抓取成功，当前共有 {len(feed.entries)} 条文章")
        
        if not feed.entries:
            print("WARNING: 未抓取到任何内容。")
            return

        # 读取上次记录（排重）
        last_id = ""
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                last_id = f.read().strip()
            print(f"DEBUG: 上次已读最新 ID: {last_id}")
        else:
            print("DEBUG: 首次运行，准备进行初始推送")

        # 筛选新内容
        new_entries = []
        for entry in feed.entries:
            if entry.id == last_id:
                break
            new_entries.append(entry)

        # 执行推送
        if new_entries:
            print(f"DEBUG: 检测到 {len(new_entries)} 条更新")
            
            # 如果是第一次运行，为了防止消息轰炸，只发最新的 3 条
            if not last_id:
                print("DEBUG: 首次运行
