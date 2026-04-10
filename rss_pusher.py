import feedparser
import requests
import time
import os

# --- 配置区 ---
RSS_URL = "https://www.jiqizhixin.com/rss"
# 对应 GitHub Secrets 中的 DINGTALK_WEBHOOK
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

# 模拟浏览器 Header，防止 403 拦截
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def send_dingtalk(entry):
    """发送消息到钉钉"""
    # 提取摘要，处理可能缺失 summary 的情况
    summary_text = entry.get('summary', '点击链接查看详情')
    
    # 清洗简单的 HTML 标签（可选）
    if "<" in summary_text:
        import re
        summary_text = re.sub('<[^<]+?>', '', summary_text)

    if len(summary_text) > 200:
        summary_text = f"{summary_text[:200]}..."

    # 构建消息体：确保标题包含你的钉钉关键词 "AI"
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AI 资讯更新（机器之心）",
            "text": f"## AI 资讯: {entry.title}\n\n"
                    f"> 发布时间: {entry.get('published', '未知时间')}\n\n"
                    f"{summary_text}\n\n"
                    f"[点击阅读全文]({entry.link})"
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        print(f"钉钉返回结果: {response.text}")
    except Exception as e:
        print(f"发送到钉钉失败: {e}")

def main():
    print(f"正在从 {RSS_URL} 抓取内容...")
    
    try:
        # 使用 requests 获取内容以应用 Headers
        response = requests.get(RSS_URL, headers=HEADERS, timeout=20)
        response.raise_for_status() # 如果状态码不是 200 则抛出异常
        
        # 解析 RSS 内容
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print("未抓取到任何有效的文章条目。")
            return

        # 读取上一次推送成功的 ID（记忆功能）
        last_id = ""
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                last_id = f.read().strip()

        new_entries = []
        for entry in feed.entries:
            if entry.id == last_id:
                break
            new_entries.append(entry)

        # 倒序推送并更新状态
        if new_entries:
            print(f"检测到 {len(new_entries)} 条新内容，开始推送...")
            for entry in reversed(new_entries):
                send_dingtalk(entry)
                time.sleep(1.5) # 稍微增加延迟，确保钉钉接收顺畅
            
            # 记录最新一条的 ID
            with open(STATUS_FILE, "w") as f:
                f.write(new_entries[0].id)
            print("✅ 状态文件已更新，推送任务完成。")
        else:
            print("☕ 暂无新内容。")

    except Exception as e:
        print(f"❌ 程序运行出错: {e}")

if __name__ == "__main__":
    main()
