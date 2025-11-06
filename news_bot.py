import os
import requests
import feedparser
import time
from datetime import datetime
from googletrans import Translator  # pip install googletrans==4.0.0-rc1

# 环境变量
WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# RSS源
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=southeast+asia+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=philippines+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=thailand+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=malaysia+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "https://news.google.com/rss/search?q=vietnam+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en"
]

translator = Translator()

def get_latest_news():
    news_items = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:  # 每源取前2条
                news_items.append({"title": entry.title, "link": entry.link})
        except Exception as e:
            print("RSS抓取失败:", e)
    return news_items

def summarize_with_gpt(news_title, retries=3, delay=2):
    """调用 GPT 生成摘要"""
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
                        {"role": "system", "content": "你是中文跨境电商新闻编辑，帮我用简洁中文总结新闻，突出对东南亚跨境电商影响。"},
                        {"role": "user", "content": f"新闻标题：{news_title}\n请用中文写一句简短摘要（15字内）"}
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
            print(f"摘要生成失败: {e}, 重试 {attempt+1}/{retries}")
        time.sleep(delay)

    # GPT失败时用Google翻译标题
    try:
        translated = translator.translate(news_title, src='en', dest='zh-cn')
        return translated.text
    except Exception as e:
        print("翻译失败:", e)
        return news_title  # 最后兜底用原文

def shorten_link(url):
    """简单缩短Google RSS链接"""
    if "articles/" in url:
        return "https://news.google.com/" + url.split("articles/")[1].split("?")[0]
    return url

def get_weather(city_name, country_code=""):
    """获取指定城市的天气情况"""
    if not OPENWEATHER_API_KEY:
        return "天气信息不可用"
    try:
        q = f"{city_name},{country_code}" if country_code else city_name
        url = f"http://api.openweathermap.org/data/2.5/weather?q={q}&appid={OPENWEATHER_API_KEY}&units=metric&lang=zh_cn"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"{desc}, {temp}°C"
    except Exception as e:
        print(f"天气获取失败 ({city_name}):", e)
        return "天气信息不可用"

def send_to_feishu(news_by_region):
    lines = []
    for region, items in news_by_region.items():
        # 获取天气
        if region == "Thailand":
            weather = get_weather("Bangkok", "TH")
        elif region == "Malaysia":
            weather = get_weather("Kuala Lumpur", "MY")
        elif region == "Vietnam":
            weather = get_weather("Hanoi", "VN")
        elif region == "Philippines":
            weather = get_weather("Manila", "PH")
        else:
            weather = "天气信息不可用"

        lines.append(f"🌤 {region} 今日天气：{weather}\n")

        for news in items:
            short_link = shorten_link(news['link'])
            lines.append(f"📰 {news['title']}\n💬 {news['summary']}\n🔗 {short_link}")

        lines.append("\n")  # 各地区分隔

    text = "\n".join(lines) if lines else "今日暂无相关新闻"

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

    # 按地区整理
    news_by_region = {
        "Thailand": [],
        "Malaysia": [],
        "Vietnam": [],
        "Philippines": [],
        "Singapore": []
    }

    for item in news_data:
        title_lower = item["title"].lower()
        if "thailand" in title_lower:
            news_by_region["Thailand"].append(item)
        elif "malaysia" in title_lower:
            news_by_region["Malaysia"].append(item)
        elif "vietnam" in title_lower:
            news_by_region["Vietnam"].append(item)
        elif "philippines" in title_lower:
            news_by_region["Philippines"].append(item)
        else:
            news_by_region["Singapore"].append(item)

    send_to_feishu(news_by_region)
