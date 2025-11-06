# news_bot.py
import os
import requests
import feedparser
from googletrans import Translator  # pip install googletrans==4.0.0-rc1

# 飞书 Webhook
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")  # GitHub Actions 中用 Secrets 设置
# OpenWeather API Key
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# RSS 新闻源
RSS_FEED = "https://news.google.com/rss/search?q=Southeast+Asia+ecommerce&hl=en-US&gl=US&ceid=US:en"

# 需要获取天气的国家
COUNTRIES = {
    "Thailand": "Bangkok,TH",
    "Malaysia": "Kuala Lumpur,MY",
    "Vietnam": "Hanoi,VN",
    "Philippines": "Manila,PH",
    "Singapore": "Singapore,SG"
}

translator = Translator()

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=zh_cn"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        description = data['weather'][0]['description']
        temp = data['main']['temp']
        return f"{description}，{temp:.2f}°C"
    except Exception as e:
        print("天气获取失败:", e)
        return "天气信息不可用"

def get_news():
    feed = feedparser.parse(RSS_FEED)
    news_items = []
    for entry in feed.entries[:5]:  # 取最新5条
        title = entry.title
        link = entry.link
        translated = translator.translate(title, dest='zh-cn').text
        news_items.append({
            "title": title,
            "link": link,
            "translated": translated
        })
    return news_items

def send_to_feishu(content):
    headers = {"Content-Type": "application/json"}
    data = {
        "msg_type": "text",
        "content": {"text": content}
    }
    try:
        resp = requests.post(FEISHU_WEBHOOK, headers=headers, json=data)
        resp.raise_for_status()
        print("飞书消息发送成功")
    except Exception as e:
        print("飞书消息发送失败:", e)

def main():
    report = "🌏 今日东南亚跨境电商快讯\n\n"

    # 天气
    for country, city in COUNTRIES.items():
        weather = get_weather(city)
        report += f"🌤 {country} 今日天气：{weather}\n\n"

    # 新闻
    news_items = get_news()
    for item in news_items:
        report += f"📰 {item['title']}\n💬 {item['translated']}\n🔗 {item['link']}\n\n"

    send_to_feishu(report)

if __name__ == "__main__":
    main()
