import feedparser
import requests
import time
import os

# --- 配置区 ---
RSS_URL = "https://www.jiqizhixin.com/rss"
WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK")
STATUS_FILE = "last_id.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def send_dingtalk(entry):
    print(f"DEBUG: 正在尝试推送文章: {entry.title}")
    summary_text = entry.get('summary', '点击链接查看详情')
    
    if "<" in summary_text:
        import re
        summary_text = re.sub('<[^<]+?>', '', summary_text)

    if len(summary_text) > 200:
        summary_text = f"{summary_text[:200]}..."

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AI 资讯更新",
            "text": f"## AI 资讯: {entry.title}\n\n"
                    f"> 发布时间: {entry.get('published', '未知时间')}\n\n"
                    f"{summary_text}\n\n"
                    f"[点击阅读全文]({entry.link})"
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        print(f"DEBUG: 钉钉接口返回: {response.text}")
    except Exception as e:
        print(f"ERROR: 发送到钉钉失败: {e}")

def main():
    # 1. 检查环境变量
    if not WEBHOOK_URL:
        print("ERROR: 环境变量 DINGTALK_WEBHOOK 未配置或为空！")
        return
    print(f"DEBUG: 环境变量 DINGTALK_WEBHOOK 已读取（长度: {len(WEBHOOK_URL)}）")

    # 2. 抓取 RSS
    print(f"DEBUG: 正在抓取 RSS: {RSS_URL}")
    try:
        response = requests.get(RSS_URL, headers=HEADERS, timeout=20)
        print(f"DEBUG: RSS 请求状态码: {response.status_code}")
        feed = feedparser.parse(response.content)
        print(f"DEBUG: 本次抓取到文章总数: {len(feed.entries)}")
    except Exception as e:
        print(f"ERROR: 抓取 RSS 过程出错: {e}")
        return

    if not feed.entries:
        return

    # 3. 读取记录文件
    last_id = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            last_id = f.read().strip()
        print(f"DEBUG: 读取到上次推送的 ID: {last_id}")
    else:
        print(f"DEBUG: 未发现状态文件 {STATUS_FILE}，将进行首次推送")

    # 4. 筛选新内容
    new_entries = []
    for entry in feed.entries:
        if entry.id == last_id:
            print(f"DEBUG: 匹配到旧记录，停止筛选。新文章数量: {len(new_entries)}")
            break
        new_entries.append(entry)

    # 如果运行过但没有新文章
    if not new_entries and last_id:
        print("DEBUG: 所有的内容都已经推送过了，没有新内容。")

    # 5. 推送
    if new_entries:
        # 如果是第一次运行，为了防止轰炸，只推送最新的 3 条
        if not last_id and len(new_entries) > 3:
            print("DEBUG: 首次运行，仅推送最新的 3 条以防轰炸")
            new_entries = new_entries[:3]

        for entry in reversed(new_entries):
            send_dingtalk(entry)
            time.sleep(1.5)
            
        with open(STATUS_FILE, "w") as f:
            f.write(new_entries[0].id)
        print(f"DEBUG: 状态已更新为最新 ID: {new_entries[0].id}")

if __name__ == "__main__":
    main()
