import os
import requests
import feedparser
from googletrans import Translator

# --------- 配置 ---------
COUNTRIES = {
    "Thailand": "TH",
    "Malaysia": "MY",
    "Vietnam": "VN",
    "Philippines": "PH",
    "Singapore": "SG"
}
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

RSS_FEEDS = [
    # 示例: Nation Thailand
    "https://news.google.com/rss/search?q=Thailand",
    "https://news.google.com/rss/search?q=Malaysia",
    "https://news.google.com/rss/search?q=Vietnam",
    "https://news.google.com/rss/search?q=Philippines",
    "https://news.google.com/rss/search?q=Singapore"
]

translator = Translator()

def get_weather(city, country_code):
    params = {
        "q": f"{city},{country_code}",
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "zh_cn"
    }
    try:
        r = requests.get(WEATHER_URL, params=params)
        r.raise_for_status()
        data = r.json()
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"{desc}，{temp:.2f}°C"
    except Exception as e:
        print(f"天气获取失败: {e}")
        return "天气信息不可用"

def get_news():
    news_list = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:  # 每个 feed 取前 2 条
            title = entry.title
            link = entry.link
            translated = translator.translate(title, dest="zh-cn").text
            news_list.append(f"📰 {title}\n💬 {translated}\n🔗 {link}")
    return news_list

def send_to_feishu(message):
    if not FEISHU_WEBHOOK:
        print("未配置 FEISHU_WEBHOOK")
        return
    payload = {"msg_type": "text", "content": {"text": message}}
    try:
        r = requests.post(FEISHU_WEBHOOK, json=payload)
        r.raise_for_status()
        print("消息已发送到飞书")
    except Exception as e:
        print(f"飞书发送失败: {e}")

def main():
    msg = "🌏 今日东南亚跨境电商快讯\n\n"
    for country, code in COUNTRIES.items():
        weather = get_weather(country, code)
        msg += f"🌤 {country} 今日天气：{weather}\n\n"

    news_items = get_news()
    msg += "\n".join(news_items)

    print(msg)  # 调试输出
    send_to_feishu(msg)

if __name__ == "__main__":
    main()
