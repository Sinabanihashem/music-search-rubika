import rubpy
from rubpy import Client
from rubpy.types import Updates
import aiohttp
from urllib.parse import quote, unquote
import os

bot = Client("music_bot")


chat_histories = {}

async def search_music(query):
    """جستجوی موسیقی از ParsSource API"""
    try:
        api_url = f"https://api.ParsSource.ir/search_music?name_music={quote(query)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("API response:", data)  # برای دیباگ در ترمینال
                    return data
                else:
                    print("API returned status:", response.status)
                    return None
    except Exception as e:
        print(f"Error in search_music: {e}")
        return None

def pretty_from_url(url):
    """
    تبدیل لینک به یک عنوان خوانا.
    مثال: https://.../Ebi%20-%20Shab.mp3  -> (artist='Ebi', title='Shab')
    """
    try:
        path = unquote(url)  # decode %20 و غیره
        base = os.path.basename(path)
        name, _ = os.path.splitext(base)
        if " - " in name:
            # قالب معمول: Artist - Title
            parts = name.split(" - ", 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            # اگر قالب متفاوت باشه، کل اسم رو بعنوان title استفاده می‌کنیم
            artist = "ناشناخته"
            title = name.strip()
        return artist, title
    except Exception:
        return "ناشناخته", url

@bot.on_message_updates()
async def handle_message(message: Updates):
    if not message.text:
        return
    
    user_text = message.text.strip()
    chat_key = message.object_guid

    if chat_key not in chat_histories:
        chat_histories[chat_key] = []

    # بررسی اینکه پیام با "جستجو " شروع بشه (توجه: فاصله بعد از 'جستجو' ضروریه)
    if user_text.startswith("جستجو"):
        parts = user_text.split(" ", 1)
        if len(parts) == 1 or not parts[1].strip():
            await message.reply("⚠️ برای جستجو، بعد از کلمه‌ی «جستجو» نام آهنگ یا خواننده را وارد کنید. مثال: جستجو محسن یگانه")
            return

        query = parts[1].strip()
        chat_histories[chat_key].append(query)
        if len(chat_histories[chat_key]) > 20:
            chat_histories[chat_key].pop(0)

        await message.reply(f"🔍 در حال جستجو برای '{query}' ...")
        results = await search_music(query)
        
        # بررسی ساختار پاسخ بر اساس نمونه‌ای که فرستادی
        if results and isinstance(results, dict) and results.get("status") and isinstance(results.get("result"), list):
            urls = results.get("result", [])
            if not urls:
                await message.reply("❌ هیچ نتیجه‌ای یافت نشد.")
                return

            # ۵ نتیجه اول
            lines = []
            max_show = min(5, len(urls))
            for i in range(max_show):
                url = urls[i]
                artist, title = pretty_from_url(url)
                lines.append(f"{i+1}. 🎵 {title}\n   👤 {artist}\n   🔗 {url}")

            if len(urls) > max_show:
                lines.append(f"و {len(urls)-max_show} نتیجهٔ بیشتر...")

            response = "\n\n".join(lines)
            await message.reply(response)
        else:
            
            await message.reply("❌ پاسخ نامعتبر از سرویس جستجو دریافت شد.")
            print("Unexpected API response structure:", results)
    else:
        return 

if name == "main":
    print("ربات موسیقی در حال اجرا است...")
    bot.run()
