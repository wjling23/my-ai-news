import feedparser
import requests
import time
import os

# 配置区
RSS_URL = "https://www.jiqizhixin.com/rss"
# 对应 GitHub Secrets 中的 DINGTALK_WEBHOOK
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

def send_dingtalk(entry):
    # 直接使用 Webhook URL，无需加签计算
    url = WEBHOOK_URL
    
    # 提取摘要，处理可能缺失 summary 的情况
    summary_text = entry.get('summary', '点击链接查看详情')
    if len(summary_text) > 200:
        summary_text = f"{summary_text[:200]}..."

    # 构建消息：标题必须包含关键词 "AI"
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AI 资讯更新（机器之心）",
            "text": f"## AI 资讯: {entry.title}\n\n"
                    f"> 发布时间: {entry.get('published', '未知')}\n\n"
                    f"{summary_text}\n\n"
                    f"[点击阅读全文]({entry.link})"
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"钉钉返回结果: {response.text}")
    except Exception as e:
        print(f"发送失败: {e}")

def main():
    print("正在抓取 RSS 源...")
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        print("未抓取到任何内容")
        return

    # 读取上一次推送成功的 ID
    last_id = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            last_id = f.read().strip()

    new_entries = []
    for entry in feed.entries:
        # 这里的 entry.id 是识别文章是否重复的关键
        if entry.id == last_id:
            break
        new_entries.append(entry)

    # 倒序推送（从旧到新），并更新状态
    if new_entries:
        print(f"检测到 {len(new_entries)} 条新内容，开始推送...")
        for entry in reversed(new_entries):
            send_dingtalk(entry)
            time.sleep(1) # 避开钉钉每分钟 20 条的限制
            
        # 将本次抓取到的最顶端（最新）的一条 ID 存入文件
        with open(STATUS_FILE, "w") as f:
            f.write(new_entries[0].id)
        print("状态文件已更新")
    else:
        print("暂无新内容需要推送")

if __name__ == "__main__":
    main()
