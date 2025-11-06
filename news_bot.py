import os
import requests
import feedparser
import time
from datetime import datetime
from googletrans import Translator  # pip install googletrans==4.0.0-rc1

# 读取环境变量
WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 新闻RSS源（东南亚跨境电商方向）
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=southeast+asia+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=philippines+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=thailand+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=malaysia+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=vietnam+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en"
]

translator = Translator()

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

def summarize_with_gpt(news_item, retries=3, delay=2):
    """调用 GPT 生成中文摘要，如果失败则 fallback 翻译标题"""
    prompt_text = f"新闻标题：{news_item['title']}\n请用中文写一句15字内摘要，突出经济、政策或天气对电商影响。"
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
                        {"role": "system", "content": "你是中文跨境电商新闻编辑。"},
                        {"role": "user", "content": prompt_text}
                    ],
                    "max_tokens": 60,
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            summary = data["choices"][0]["message"]["content"].strip()
            if summary:
                return summary
        except Exception as e:
            print(f"GPT摘要失败: {e}, 重试 {attempt+1}/{retries}")
            time.sleep(delay)
    # fallback 翻译标题
    try:
        translated = translator.translate(news_item['title'], src='en', dest='zh-cn')
        return translated.text
    except Exception as e:
        print("翻译失败:", e)
        return news_item['title']

def shorten_link(url):
    """使用 TinyURL API 生成短链接"""
    try:
        resp = requests.get(f"http://tinyurl.com/api-create.php?url={url}", timeout=5)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print("短链接生成失败:", e)
    # fallback 返回原链接
    return url

def send_to_feishu(news_list):
    """发送新闻到飞书"""
    if not news_list:
        text = "今日暂无相关新闻"
    else:
        lines = []
        for news in news_list:
            short_url = shorten_link(news['link'])
            lines.append(f"📰 {news['title']}\n💬 {news['summary']}\n🔗 {short_url}")
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
        item["summary"] = summarize_with_gpt(item)
    send_to_feishu(news_data)
