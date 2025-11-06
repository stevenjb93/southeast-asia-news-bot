import os
import requests
import feedparser
import time
from datetime import datetime

# 从系统环境变量读取 Key
WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 检查环境变量
if not WEBHOOK_URL or not OPENAI_API_KEY:
    raise ValueError("请先在系统环境变量中设置 FEISHU_WEBHOOK 和 OPENAI_API_KEY")

# 新闻RSS源（东南亚跨境电商方向）
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=southeast+asia+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=philippines+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=thailand+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=malaysia+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=vietnam+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en"
]

def get_latest_news():
    """抓取新闻标题和链接"""
    news_items = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:  # 每个源取前2条
                news_items.append({"title": entry.title, "link": entry.link})
        except Exception as e:
            print("RSS抓取失败:", e)
    return news_items

def summarize_with_gpt(news_title, retries=3, delay=2):
    """调用 OpenAI GPT 生成中文摘要（仅用标题），带重试机制"""
    for attempt in range(retries):
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "你是一个中文跨境电商新闻编辑，帮我用简洁中文总结新闻，突出对东南亚跨境电商可能的影响。"},
                        {"role": "user", "content": f"新闻标题：{news_title}\n请用中文写一句简短摘要（15字内），突出经济、政策或天气对电商影响。"}
                    ],
                    "max_tokens": 60,
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            summary = data["choices"][0]["message"]["content"].strip()
            return summary
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}, 尝试重试 {attempt+1}/{retries}")
        except Exception as e:
            print(f"其他错误: {e}, 尝试重试 {attempt+1}/{retries}")
        time.sleep(delay)
    return "（摘要生成失败）"

def send_to_feishu(news_list):
    """发送到飞书"""
    if not news_list:
        text = "今日暂无相关新闻"
    else:
        lines = []
        for news in news_list:
            lines.append(f"📰 {news['title']}\n💬 {news['summary']}\n🔗 {news['link']}")
        text = "\n\n".join(lines)

    payload = {
        "msg_type": "text",
        "content": {"text": f"🌏 今日东南亚跨境电商快讯（{datetime.now().strftime('%Y-%m-%d %H:%M')}）\n\n{text}"}
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
        print("飞书发送成功")
    except Exception as e:
        print("飞书发送失败:", e)

if __name__ == "__main__":
    news_data = get_latest_news()
    for item in news_data:
        item["summary"] = summarize_with_gpt(item["title"])
    send_to_feishu(news_data)
