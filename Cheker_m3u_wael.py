import datetime
import re
import requests
import telebot

# توكن البوت الخاص بك
TOKEN = "8737760391:AAHD_DTsYA-wcqaadxwOtvzbTVfMnyHjZ7w"
bot = telebot.TeleBot(TOKEN)

# (اختياري) ضع هنا رقم مجموعة "الصندوق الأسود" لاحقاً إذا أردت إرسال التقارير لها تلقائياً
BLACK_BOX_CHAT_ID = None


def parse_m3u_advanced_for_bot(m3u_url):
  try:
    if "get.php" in m3u_url:
      base_url = m3u_url.split("/get.php")[0]
      match_user = re.search(r"username=([^&]+)", m3u_url)
      match_pass = re.search(r"password=([^&]+)", m3u_url)

      if match_user and match_pass:
        username = match_user.group(1)
        password = match_pass.group(1)

        api_url = (
            f"{base_url}/player_api.php?username={username}&password={password}"
        )
        response = requests.get(api_url, timeout=15)

        if response.status_code == 200:
          data = response.json()
          user_info = data.get("user_info", {})
          server_info = data.get("server_info", {})

          report = []
          # ترويسة باسم الصندوق الأسود
          report.append("💎 ━━━━━━━━━━━━━━━━━━━━ 💎")
          report.append("🌟     الـصـنـدوق الـأسـود     🌟")
          report.append("💎 ━━━━━━━━━━━━━━━━━━━━ 💎")
          report.append(f"🔗 رابط M3U: {m3u_url}")
          report.append(f"👤 اسم المستخدم: {username}")
          report.append(f"🔑 كلمة المرور: {password}")

          status = user_info.get("status", "غير معروف")
          status_text = "نشط (Active)" if status == "Active" else status
          report.append(f"🟢 حالة الحساب: {status_text}")

          exp_date = user_info.get("exp_date")
          if exp_date and exp_date != "null":
            readable_date = datetime.datetime.fromtimestamp(
                int(exp_date)
            ).strftime("%Y-%m-%d %H:%M:%S")
            report.append(f"📅 تاريخ الانتهاء: {readable_date}")
          else:
            report.append("📅 تاريخ الانتهاء: غير محدود (Unlimited)")

          report.append(
              f"🔌 الاتصالات المتاحة: {user_info.get('max_connections', '1')}"
          )
          report.append(
              f"🚫 الاتصالات النشطة: {user_info.get('active_cons', '0')}"
          )

          report.append("⭐ ---------------------------------------- ⭐")
          report.append("🌐 معلومات السيرفر الأساسية:")
          report.append(f"🌐 رابط البورت: {server_info.get('url', base_url)}")
          report.append(f"🔌 البورت (Port): {server_info.get('port', '80')}")
          report.append("⭐ ---------------------------------------- ⭐")

          # القنوات المباشرة
          try:
            live_cat_url = (
                f"{base_url}/player_api.php?username={username}&password={password}&action=get_live_categories"
            )
            live_res = requests.get(live_cat_url, timeout=10)
            if live_res.status_code == 200:
              live_cats = live_res.json()
              if isinstance(live_cats, list):
                report.append("\n📺 --- [ ⭐ قنوات مباشرة ⭐ ] ---")
                for i, cat in enumerate(live_cats[:6], 1):
                  report.append(f"  {i}. 🖥️ {cat.get('category_name')}")
          except Exception:
            pass

          # المسلسلات
          try:
            series_cat_url = (
                f"{base_url}/player_api.php?username={username}&password={password}&action=get_series_categories"
            )
            series_res = requests.get(series_cat_url, timeout=10)
            if series_res.status_code == 200:
              series_cats = series_res.json()
              if isinstance(series_cats, list):
                report.append("\n🎬 --- [ ⭐ قنوات مسلسلات ⭐ ] ---")
                for i, cat in enumerate(series_cats[:6], 1):
                  report.append(f"  {i}. 🎬 {cat.get('category_name')}")
          except Exception:
            pass

          # الأفلام
          try:
            vod_cat_url = (
                f"{base_url}/player_api.php?username={username}&password={password}&action=get_vod_categories"
            )
            vod_res = requests.get(vod_cat_url, timeout=10)
            if vod_res.status_code == 200:
              vod_cats = vod_res.json()
              if isinstance(vod_cats, list):
                report.append("\n🍿 --- [ ⭐ قنوات أفلام ⭐ ] ---")
                for i, cod in enumerate(vod_cats[:6], 1):
                  report.append(f"  {i}. 🎟️ {cod.get('category_name')}")
          except Exception:
            pass

          report.append("\n💎 [✔] تم فحص السيرفر بنجاح! 💎")
          return "\n".join(report)
        else:
          return (
              f"[❌] خطأ في الاتصال بالسيرفر (رمز الاستجابة:"
              f" {response.status_code})"
          )

    return "[⚠️] الرابط المدخل ليس بصيغة Xtream القياسية."
  except Exception as e:
    return f"[❌] حدث خطأ أثناء الاتصال أو المعالجة: {e}"


# أمر البدء في البوت
@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "أهلاً بك في بوت الصندوق الأسود لفحص اشتراكات الـ IPTV! 🚀\nأرسل لي رابط"
      " M3U وسأقوم بفحصه فوراً.",
  )


# استقبال أي رابط وإرسال التقرير
@bot.message_handler(func=lambda message: True)
def handle_m3u_input(message):
  url = message.text.strip()
  if "http" in url:
    sent_msg = bot.reply_to(
        message, "[⏳] جاري الاتصال بالسيرفر وجلب التفاصيل والقوائم..."
    )
    result_report = parse_m3u_advanced_for_bot(url)
    bot.edit_message_text(
        chat_id=message.chat.id, message_id=sent_msg.message_id, text=result_report
    )
  else:
    bot.reply_to(message, "[⚠️] الرجاء إرسال رابط M3U صالح يبدأ بـ http.")


if __name__ == "__main__":
  print("[⚡] بوت الصندوق الأسود يعمل الآن بالشكل المطلوب...")
  bot.infinity_polling()