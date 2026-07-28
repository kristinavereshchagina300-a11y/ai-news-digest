"""
AI News Digest Bot
Читает RSS-ленты про ИИ, суммирует новости через Claude API,
отправляет дайджест в Telegram.
"""

import os
import sys
import feedparser
import requests

# ---------- Настройки ----------

RSS_FEEDS = [
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.artificialintelligence-news.com/feed/",
    # добавь свои источники сюда
]

MAX_ITEMS = 3  # сколько новостей брать за раз

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


# ---------- Шаг 1. Собираем новости из RSS ----------

def fetch_news():
    items = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:MAX_ITEMS]:
            items.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", entry.get("description", "")),
                "link": entry.get("link", ""),
            })
    return items[:MAX_ITEMS]


# ---------- Шаг 2. Суммаризация через Claude ----------

def summarize(items):
    if not items:
        return "Сегодня новых новостей не найдено."

    news_text = "\n\n".join(
        f"Заголовок: {item['title']}\nОписание: {item['summary']}\nСсылка: {item['link']}"
        for item in items
    )

    prompt = (
        "Вот несколько новостей про ИИ:\n\n"
        f"{news_text}\n\n"
        "Выбери самое важное и объясни простыми словами, понятными новичку в ИИ. "
        "Для каждой новости — 2-3 предложения, без сложных терминов. "
        "Формат: эмодзи + короткий заголовок, затем объяснение. "
        "В конце добавь ссылку на источник."
    )

    response = requests.post(
        ANTHROPIC_URL,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": "claude-sonnet-5",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return "".join(block["text"] for block in data["content"] if block["type"] == "text")


# ---------- Шаг 3. Отправка в Telegram ----------

def send_to_telegram(text):
    response = requests.post(
        TELEGRAM_URL,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=30,
    )
    response.raise_for_status()


# ---------- Запуск ----------

def main():
    try:
        news = fetch_news()
        digest = summarize(news)
        send_to_telegram(digest)
        print("Дайджест отправлен успешно.")
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
