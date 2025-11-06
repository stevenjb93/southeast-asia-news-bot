import os
import requests
import feedparser
from deep_translator import GoogleTranslator

# 配置
COUNTRIES = {
    "Thailand": "Bangkok,TH",
    "Singapore": "Singapore,SG",
    "Malaysia": "Kuala Lumpur,MY",
    "Vietnam": "Hanoi,VN",
    "Philippines": "Manila,PH"
}

API_KEY = os.getenv("OPENWEATHER_API_KEY")
UNITS = "metric"
LANG = "zh_cn"

# 获取天气
def get_weather(city_code):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_code}&appid={API_KEY}&units={UNITS}&lang={LANG}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        desc = data['weather'][0]['description']
        temp = data['main']['temp']
        return f"{desc}，{temp:.2f}°C"
    except Exception as e:
        print(f"天气获取失败: {e}")
        return "天气信息不可用"

# 获取 RSS 新闻
RSS_FEEDS = {
    "Thailand": "https://news.google.com/rss/search?q=Thailand+business&hl=en-US&gl=US&ceid=US:en",
    "Singapore": "https://news.google.com/rss/search?q=Singapore+business&hl=en-US&gl=US&ceid=US:en",
    "Malaysia": "https://news.google.com/rss/search?q=Malaysia+business&hl=en-US&gl=US&ceid=US:en",
    "Vietnam": "https://news.google.com/rss/search?q=Vietnam+business&hl=en-US&gl=US&ceid=US:en",
    "Philippines": "https://news.google.com/rss/search?q=Philippines+business&hl=en-US&gl=US&ceid=US:en",
}

print(f"🌏 今日东南亚跨境电商快讯")

for country, city_code in COUNTRIES.items():
    weather = get_weather(city_code)
    print(f"\n🌤 {country} 今日天气：{weather}")

    feed = feedparser.parse(RSS_FEEDS[country])
    for entry in feed.entries[:2]:  # 每国取前 2 条新闻
        title_en = entry.title
        title_cn = GoogleTranslator(source='en', target='zh-CN').translate(title_en)
        print(f"📰 {title_en}")
        print(f"💬 {title_cn}")
        print(f"🔗 {entry.link}")
