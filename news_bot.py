import os
import requests
import feedparser
import time
from datetime import datetime
from googletrans import Translator  # pip install googletrans==4.0.0-rc1

# 环境变量
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# RSS源
RSS_FEEDS = {
    "Thailand": "https://news.google.com/rss/search?q=thailand+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "Malaysia": "https://news.google.com/rss/search?q=malaysia+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "Vietnam": "https://news.google.com/rss/search?q=vietnam+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "Philippines": "https://news.google.com/rss/search?q=philippines+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en",
    "Singapore": "https://news.google.com/rss/search?q=singapore+ecommerce+OR+cross-border+OR+logistics+OR+policy+OR+weather&hl=en&gl=SG&ceid=SG:en"
}

# 国家对应 OpenWeatherMap 的 ISO 3166-1 alpha-2 代码
COUNTRY_CODES = {
    "Thailand": "TH",
    "Malaysia": "MY",
    "Vietnam": "VN",
    "Philippines": "PH",
    "Singapore": "SG"
}

translator = Translator()

def get_weather(city_name, country_code):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name},{country_code}&appid={OPENWEATHER_API_KEY}&units=metric&lang=zh_cn"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        description = data['weather'][0]['description']
        temp = data['main']['temp']
        return f"{description}, {temp}℃"
    except Exception as e:
        print(f"天气获取失败 ({city_name}):", e)
        return "天气信息不可用"

def get_latest_news():
    news_data = {}
    for country, url in RSS_FEEDS.items():
        news_items = []
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:
                news_items.append({"title": entry.title, "link": entry.link})
        except Exception as e:
            print(f"{country} RSS抓取失败:", e)
        news_data[country] = news_items
    return news_data

def summarize_with_gpt(news_title, retries=3, delay=2):
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

    try:
        translated = translator.translate(news_title, src='en', dest='zh-cn')
        return translated.text
    except Exception as e:
        print("翻译失败:", e)
        return news_title

def shorten_link(url):
    if "articles/" in url:
        return "https://news.google.com/" + url.split("articles/")[1].split("?")[0]
    return url

def send_to_feishu(news_data):
    lines = []
    for country, items in news_data.items():
        country_code = COUNTRY_CODES.get(country, "")
        weather_info = get_weather(country, country_code)
        lines.append(f"🌤 {country} 今日天气：{weather_info}\n")
        for news in items:
            short_link = shorten_link(news['link'])
            lines.append(f"📰 {news['title']}\n💬 {news['summary']}\n🔗 {short_link}")
        lines.append("\n")
    
    text = "\n".join(lines) if lines else "今日暂无相关新闻"
    payload = {
        "msg_type": "text",
        "content": {"text": f"🌏 今日东南亚跨境电商快讯（{datetime.now().strftime('%Y-%m-%d %H:%M')}）\n\n{text}"}
    }
    try:
        r = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
        r.raise_for_status()
        print("飞书发送成功")
    except Exception as e:
        print("飞书发送失败:", e)

if __name__ == "__main__":
    news_data = get_latest_news()
    for country, items in news_data.items():
        for item in items:
            item["summary"] = summarize_with_gpt(item["title"])
    send_to_feishu(news_data)
