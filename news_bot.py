import os
import requests
import feedparser
from googletrans import Translator

translator = Translator()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")

COUNTRIES = {
    "Thailand": "Bangkok,TH",
    "Malaysia": "Kuala Lumpur,MY",
    "Vietnam": "Hanoi,VN",
    "Philippines": "Manila,PH",
    "Singapore": "Singapore,SG"
}

def get_weather(city_code):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_code}&appid={OPENWEATHER_API_KEY}&units=metric&lang=zh_cn"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        desc = data['weather'][0]['description']
        temp = data['main']['temp']
        return f"{desc}，{temp:.2f}°C"
    except Exception as e:
        print(f"天气获取失败: {e}")
        return "天气信息不可用"

def get_news(feed_url):
    feed = feedparser.parse(feed_url)
    news_list = []
    for entry in feed.entries[:2]:  # 每个国家取最新2条
        title = translator.translate(entry.title, dest="zh-cn").text
        link = entry.link
        news_list.append(f"📰 {entry.title}\n💬 {title}\n🔗 {link}")
    return news_list

def send_to_feishu(content):
    payload = {"msg_type": "text", "content": {"text": content}}
    r = requests.post(FEISHU_WEBHOOK, json=payload)
    return r.status_code

if __name__ == "__main__":
    message = "🌏 今日东南亚跨境电商快讯\n\n"
    for country, city_code in COUNTRIES.items():
        weather = get_weather(city_code)
        message += f"🌤 {country} 今日天气：{weather}\n\n"

        # 示例 RSS，可替换为你的真实 RSS 链接
        feed_url = f"https://news.google.com/rss/search?q={country}+business&hl=en-US&gl={country[:2]}&ceid={country[:2]}:en"
        news_items = get_news(feed_url)
        message += "\n".join(news_items) + "\n\n"

    status = send_to_feishu(message)
    print(f"飞书推送状态: {status}")
