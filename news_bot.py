import os
import requests
import feedparser
from googletrans import Translator

# --------- 配置 ---------
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# 国家和城市映射
COUNTRIES = {
    "Thailand": "Bangkok,TH",
    "Malaysia": "Kuala Lumpur,MY",
    "Vietnam": "Hanoi,VN",
    "Philippines": "Manila,PH",
    "Singapore": "Singapore,SG",
}

RSS_FEEDS = [
    ("Thailand", "https://news.google.com/rss/search?q=Thailand+cross-border+ecommerce&hl=en-US&gl=US&ceid=US:en"),
    ("Malaysia", "https://news.google.com/rss/search?q=Malaysia+cross-border+ecommerce&hl=en-US&gl=US&ceid=US:en"),
    ("Vietnam", "https://news.google.com/rss/search?q=Vietnam+cross-border+ecommerce&hl=en-US&gl=US&ceid=US:en"),
    ("Philippines", "https://news.google.com/rss/search?q=Philippines+cross-border+ecommerce&hl=en-US&gl=US&ceid=US:en"),
    ("Singapore", "https://news.google.com/rss/search?q=Singapore+cross-border+ecommerce&hl=en-US&gl=US&ceid=US:en"),
]

translator = Translator()

# --------- 获取天气 ---------
def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=zh_cn"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"{desc}，{temp:.2f}°C"
    except Exception as e:
        print("天气获取失败:", e)
        return "天气信息不可用"

# --------- 获取新闻 ---------
def get_news():
    result = ""
    for country, feed_url in RSS_FEEDS:
        result += f"\n🌤 {country} 今日天气：{get_weather(COUNTRIES[country])}\n"
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:  # 每个国家取最新2条
            title_en = entry.title
            title_cn = translator.translate(title_en, src='en', dest='zh-cn').text
            result += f"📰 {title_en}\n💬 {title_cn}\n🔗 {entry.link}\n"
    return result

# --------- 飞书推送 ---------
def send_to_feishu(content):
    headers = {"Content-Type": "application/json"}
    data = {"msg_type": "text", "content": {"text": content}}
    try:
        resp = requests.post(FEISHU_WEBHOOK, headers=headers, json=data)
        resp.raise_for_status()
        print("飞书推送成功")
    except Exception as e:
        print("飞书推送失败:", e)

# --------- 主函数 ---------
if __name__ == "__main__":
    news_content = "🌏 今日东南亚跨境电商快讯\n" + get_news()
    send_to_feishu(news_content)
