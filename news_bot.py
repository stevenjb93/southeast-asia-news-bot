import os
import feedparser
import requests
from googletrans import Translator  # pip install googletrans==4.0.0-rc1

# —— 配置部分 —— #

FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
OWM_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# 目标国家与城市
countries = {
    "Thailand": "Bangkok,TH",
    "Malaysia": "Kuala Lumpur,MY",
    "Vietnam": "Hanoi,VN",
    "Philippines": "Manila,PH",
    "Singapore": "Singapore,SG"
}

# RSS 源（聚焦电商、TikTok、Shopee）
rss_feeds = {
    "Thailand": "https://news.google.com/rss/search?q=Thailand+TikTok+OR+Shopee+OR+Lazada+OR+ecommerce&hl=en-US&gl=US&ceid=US:en",
    "Malaysia": "https://news.google.com/rss/search?q=Malaysia+TikTok+OR+Shopee+OR+Lazada+OR+ecommerce&hl=en-US&gl=US&ceid=US:en",
    "Vietnam": "https://news.google.com/rss/search?q=Vietnam+TikTok+OR+Shopee+OR+Lazada+OR+ecommerce&hl=en-US&gl=US&ceid=US:en",
    "Philippines": "https://news.google.com/rss/search?q=Philippines+TikTok+OR+Shopee+OR+Lazada+OR+ecommerce&hl=en-US&gl=US&ceid=US:en",
    "Singapore": "https://news.google.com/rss/search?q=Singapore+TikTok+OR+Shopee+OR+Lazada+OR+ecommerce&hl=en-US&gl=US&ceid=US:en"
}

# 优先级关键词
priority_keywords = ["Typhoon", "Storm", "Flood", "台风", "暴雨", "Shopee", "TikTok", "Lazada"]

# —— 函数部分 —— #

def get_weather(city):
    """获取城市天气"""
    if not OWM_API_KEY:
        return "未配置天气API Key"
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
    """抓取新闻并按关键词优先级排序"""
    feed_url = rss_feeds.get(country)
    if not feed_url:
        return []

    feed = feedparser.parse(feed_url)
    news_list = []

    for entry in feed.entries[:10]:
        score = 0
        for kw in priority_keywords:
            if kw.lower() in entry.title.lower() or kw.lower() in entry.summary.lower():
                score += 10
        news_list.append((score, entry))

    news_list.sort(key=lambda x: x[0], reverse=True)
    return [entry for score, entry in news_list[:3]]  # 取前3条最重要新闻

def send_to_feishu(message):
    """发送消息到飞书机器人"""
    if not FEISHU_WEBHOOK:
        print("未配置飞书 Webhook")
        return

    data = {"msg_type": "text", "content": {"text": message}}
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=data)
        print("Feishu response:", resp.status_code, resp.text)
        resp.raise_for_status()
        print("✅ 消息已发送到飞书")
    except Exception as e:
        print(f"❌ 飞书消息发送失败: {e}")

# —— 主程序 —— #

translator = Translator()
message = "🌏 今日东南亚跨境电商快讯\n\n"

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

send_to_feishu(message)
