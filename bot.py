import json
import asyncio
import logging
import requests
import xml.etree.ElementTree as ET
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8835537614:AAEYS-x5arN0kAcvJuvCuqqxGrD2Qn2_qBQ"
CHANNEL_ID     = "@EtoFact_channel"
YOUTUBE_CHANNEL_ID = "YOUTUBE_CHANNEL_ID ="UCF86jKHCogORfF94qAQ6pKw"
POSTED_FILE = "posted_ids.json"
CHECK_INTERVAL = 3600  # проверять каждый час


def load_posted():
    try:
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()


def save_posted(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted), f)


def get_youtube_videos(limit=10):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/'
        }
        videos = []
        for entry in root.findall('atom:entry', ns)[:limit]:
            video_id = entry.find('yt:videoId', ns).text
            title = entry.find('atom:title', ns).text
            link = f"https://www.youtube.com/shorts/{video_id}"
            videos.append({
                "id": video_id,
                "title": title,
                "link": link,
            })
        return videos
    except Exception as e:
        logger.error(f"Ошибка YouTube: {e}")
        return []


async def post_video(bot, video):
    try:
        text = f"🎬 {video['title']}\n\n👉 {video['link']}\n\n📌 @EtoFact_channel"
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
        )
        logger.info(f"Опубликовано: {video['title'][:50]}")
    except TelegramError as e:
        logger.error(f"Ошибка Telegram: {e}")


async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    me = await bot.get_me()
    logger.info(f"Бот запущен: @{me.username}")

    posted = load_posted()

    # При первом запуске — публикуем последние 10 видео
    if not posted:
        logger.info("Первый запуск — загружаем последние 10 видео...")
        videos = get_youtube_videos(limit=10)
        for video in reversed(videos):
            await post_video(bot, video)
            posted.add(video["id"])
            save_posted(posted)
            await asyncio.sleep(5)

    # Дальше проверяем каждый час
    while True:
        logger.info("Проверяю новые видео...")
        videos = get_youtube_videos(limit=5)
        for video in reversed(videos):
            if video["id"] not in posted:
                await post_video(bot, video)
                posted.add(video["id"])
                save_posted(posted)
                await asyncio.sleep(3)
        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
