import os
import feedparser
import requests
from googletrans import Translator  # pip install googletrans==4.0.0-rc1

# —— 配置部分 —— #

# 飞书机器人 webhook
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")

# OpenWeatherMap API Key
OWM_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# 国家与城市
countries = {
    "Thailand": "Bangkok,TH",
    "Malaysia": "Kuala Lumpur,MY",
    "Vietnam": "Hanoi,VN",
    "Philippines": "Manila,PH",
    "Singapore": "Singapore,SG"
}

# RSS feeds（示例，可替换成跨境电商相关RSS）
rss_feeds = {
    "Thailand": "https://news.google.com/rss/search?q=Thailand+ecommerce+OR+TikTok+OR+Shopee&hl=en-US&gl=US&ceid=US:en",
    "Malaysia": "https://news.google.com/rss/search?q=Malaysia+ecommerce+OR+TikTok+OR+Shopee&hl=en-US&gl=US&ceid=US:en",
    "Vietnam": "https://news.google.com/rss/search?q=Vietnam+ecommerce+OR+TikTok+OR+Shopee&hl=en-US&gl=US&ceid=US:en",
    "Philippines": "https://news.google.com/rss/search?q=Philippines+ecommerce+OR+TikTok+OR+Shopee&hl=en-US&gl=US&ceid=US:en",
    "Singapore": "https://news.google.com/rss/search?q=Singapore+ecommerce+OR+TikTok+OR+Shopee&hl=en-US&gl=US&ceid=US:en"
}

# 高优先级关键词
priority_keywords = ["Typhoon", "Storm", "Flood", "台风", "暴雨", "Shopee", "TikTok"]

# —— 函数部分 —— #

def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang=zh_cn"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"{desc}，{temp}°C"
    except Exception as e:
        print(f"天气获取失败: {e}")
        return "天气信息不可用"

def fetch_news(country):
    feed_url = rss_feeds.get(country)
    if not feed_url:
        return []
    feed = feedparser.parse(feed_url)
    news_list = []
    for entry in feed.entries[:10]:  # 取前10条新闻用于排序
        score = 0
        for kw in priority_keywords:
            if kw.lower() in entry.title.lower() or kw.lower() in entry.summary.lower():
                score += 10
        news_list.append((score, entry))
    # 按分数降序排序
    news_list.sort(key=lambda x: x[0], reverse=True)
    return [entry for score, entry in news_list[:3]]  # 取前3条最重要新闻

def send_to_feishu(message):
    if not FEISHU_WEBHOOK:
        print("未配置飞书Webhook")
        return
    data = {"msg_type": "text", "content": {"text": message}}
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=data)
        resp.raise_for_status()
        print("消息已发送飞书")
    except Exception as e:
        print(f"飞书消息发送失败: {e}")

# —— 主程序 —— #

translator = Translator()
message = f"🌏 今日东南亚跨境电商快讯（2025-11-06）\n\n"

for country, city in countries.items():
    weather = get_weather(city)
    message += f"🌤 {country} 今日天气：{weather}\n"

    news_entries = fetch_news(country)
    if news_entries:
        for entry in news_entries:
            title = translator.translate(entry.title, dest="zh-cn").text
            summary = translator.translate(entry.summary, dest="zh-cn").text
            link = entry.link
            message += f"📰 {title}\n💬 {summary}\n🔗 {link}\n\n"
    else:
        message += "⚡ 今日暂无重要电商新闻\n\n"

# 发送到飞书
send_to_feishu(message)
