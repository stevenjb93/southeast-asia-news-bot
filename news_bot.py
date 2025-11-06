import os
import requests
import feedparser
from googletrans import Translator

# ==== 配置部分 ====
API_KEY = os.getenv("OPENWEATHER_API_KEY")
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")  # 飞书群机器人Webhook

if not API_KEY or not FEISHU_WEBHOOK:
    print("请先设置 OPENWEATHER_API_KEY 和 FEISHU_WEBHOOK 环境变量")
    exit()

translator = Translator()

countries = {
    "Thailand": "Bangkok,TH",
    "Singapore": "Singapore,SG",
    "Malaysia": "Kuala Lumpur,MY",
    "Vietnam": "Hanoi,VN",
    "Philippines": "Manila,PH"
}

# 天气获取函数
def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=zh_cn"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        weather_desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"{weather_desc}，{temp:.1f}°C"
    except Exception as e:
        print(f"天气获取失败: {e}")
        return "天气信息不可用"

# 新闻 RSS 源（重点电商资讯）
rss_feeds = {
    "Thailand": "https://news.google.com/rss/search?q=Thailand+TikTok+Shopee+Lazada+cross+border",
    "Singapore": "https://news.google.com/rss/search?q=Singapore+TikTok+Shopee+Lazada+cross+border",
    "Malaysia": "https://news.google.com/rss/search?q=Malaysia+TikTok+Shopee+Lazada+cross+border",
    "Vietnam": "https://news.google.com/rss/search?q=Vietnam+TikTok+Shopee+Lazada+cross+border",
    "Philippines": "https://news.google.com/rss/search?q=Philippines+TikTok+Shopee+Lazada+cross+border"
}

# 构建消息
message = "🌏 今日东南亚跨境电商快讯（2025-11-06）\n\n"

for country, city in countries.items():
    weather = get_weather(city)
    message += f"🌤 {country} 今日天气：{weather}\n"
    
    feed_url = rss_feeds.get(country)
    feed = feedparser.parse(feed_url)
    if feed.entries:
        entry = feed.entries[0]  # 取最新一条新闻
        title = translator.translate(entry.title, dest="zh-cn").text
        summary = translator.translate(entry.summary, dest="zh-cn").text
        link = entry.link
        message += f"📰 {title}\n💬 {summary}\n🔗 {link}\n\n"
    else:
        message += "⚡ 今日暂无重要电商新闻\n\n"

# ==== 推送飞书 ====
def push_to_feishu(text):
    headers = {"Content-Type": "application/json"}
    payload = {"msg_type": "text", "content": {"text": text}}
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=payload, headers=headers)
        resp.raise_for_status()
        print("推送成功")
    except Exception as e:
        print(f"飞书推送失败: {e}")

print(message)
push_to_feishu(message)
