import os
import requests
import feedparser
from datetime import datetime

# 读取环境变量
WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 新闻RSS源
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=southeast+asia&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=philippines&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=thailand&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=malaysia&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=vietnam&hl=en&gl=SG&ceid=SG:en"
]

def get_latest_news():
    """抓取新闻标题和链接"""
    news_items = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:2]:  # 每个源取2条
            news_items.append({"title": entry.title, "link": entry.link})
    return news_items

def summarize_with_gpt(news_title):
    """调用 OpenAI GPT 生成中文摘要"""
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "你是一个中文新闻编辑，帮我用简洁的中文总结新闻标题。"},
                    {"role": "user", "content": f"新闻标题：{news_title}\n请用中文写一句简短摘要（15字内，概述重点）。"}
                ],
                "max_tokens": 60,
            },
            timeout=15
        )
        data = response.json()
        summary = data["choices"][0]["message"]["content"].strip()
        return summary
    except Exception as e:
        return "（摘要生成失败）"

def send_to_feishu(news_list):
    """发送到飞书"""
    if not news_list:
        text = "今日暂无相关新闻"
    else:
        lines = []
        for news in news_list:
            lines.append(f"📰 {news['title']}\n💬 {news['summary']}\n🔗 [点击查看原文]({news['link']})")
        text = "\n\n".join(lines)

    payload = {
        "msg_type": "text",
        "content": {"text": f"🌏 今日东南亚快讯（{datetime.now().strftime('%Y-%m-%d')})\n\n{text}"}
    }
    r = requests.post(WEBHOOK_URL, json=payload)
    print(r.status_code, r.text)

if __name__ == "__main__":
    news_data = get_latest_news()
    for item in news_data:
        item["summary"] = summarize_with_gpt(item["title"])
    send_to_feishu(news_data)
