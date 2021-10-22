#!/usr/bin/env python3
# Copyright (C) @SakirBey1
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from utils import LOGGER
from contextlib import suppress
from config import Config
import calendar
import pytz
from datetime import datetime
import asyncio
import os
from pyrogram.errors.exceptions.bad_request_400 import (
    MessageIdInvalid, 
    MessageNotModified
)
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from utils import (
    cancel_all_schedules,
    edit_config, 
    is_admin, 
    leave_call, 
    restart,
    restart_playout,
    stop_recording, 
    sync_to_db,
    update, 
    is_admin, 
    chat_filter,
    sudo_filter,
    delete_messages,
    seek_file
)
from pyrogram import (
    Client, 
    filters
)

IST = pytz.timezone(Config.TIME_ZONE)
if Config.DATABASE_URI:
    from utils import db

HOME_TEXT = "<b>Hey  [{}](tg://user?id={}) 🙋‍♂️\n\nBen Telegram VoiceChat'lerde Video Oynatmak veya Yayınlamak İçin Oluşturulmuş Bir Bot'um.\nHerhangi bir YouTube Videosunu veya Bir Telgraf Dosyasını veya Hatta Bir YouTube Canlı Yayınını Yapabilirim.</b>"
admin_filter=filters.create(is_admin) 

@Client.on_message(filters.command(['start', f"start@{Config.BOT_USERNAME}"]))
async def start(client, message):
    if len(message.command) > 1:
        if message.command[1] == 'help':
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(f"oynat", callback_data='help_play'),
                        InlineKeyboardButton(f"ayarlar", callback_data=f"help_settings"),
                        InlineKeyboardButton(f"Kayıt", callback_data='help_record'),
                    ],
                    [
                        InlineKeyboardButton("zamanlama", callback_data="help_schedule"),
                        InlineKeyboardButton("kontrol", callback_data='help_control'),
                        InlineKeyboardButton("yöneticiler", callback_data="help_admin"),
                    ],
                    [
                        InlineKeyboardButton(f"Çeşitli", callback_data='help_misc'),
                        InlineKeyboardButton("Kapat", callback_data="close"),
                    ],
                ]
                )
            await message.reply("GrupMüzikbot'u kullanmayı öğrenin, Yardım menüsü gösteriliyor, Aşağıdaki seçeneklerden birini seçin.",
                reply_markup=reply_markup,
                disable_web_page_preview=True
                )
        elif 'sch' in message.command[1]:
            msg=await message.reply("Programlar kontrol ediliyor...")
            you, me = message.command[1].split("_", 1)
            who=Config.SCHEDULED_STREAM.get(me)
            if not who:
                return await msg.edit("Bir yere bir şey gitti.")
            del Config.SCHEDULED_STREAM[me]
            whom=f"{message.chat.id}_{msg.message_id}"
            Config.SCHEDULED_STREAM[whom] = who
            await sync_to_db()
            if message.from_user.id not in Config.ADMINS:
                return await msg.edit("OK da")
            today = datetime.now(IST)
            smonth=today.strftime("%B")
            obj = calendar.Calendar()
            thisday = today.day
            year = today.year
            month = today.month
            m=obj.monthdayscalendar(year, month)
            button=[]
            button.append([InlineKeyboardButton(text=f"{str(smonth)}  {str(year)}",callback_data=f"sch_month_choose_none_none")])
            days=["Mon", "Tues", "Wed", "Thu", "Fri", "Sat", "Sun"]
            f=[]
            for day in days:
                f.append(InlineKeyboardButton(text=f"{day}",callback_data=f"day_info_none"))
            button.append(f)
            for one in m:
                f=[]
                for d in one:
                    year_=year
                    if d < int(today.day):
                        year_ += 1
                    if d == 0:
                        k="\u2063"   
                        d="none"   
                    else:
                        k=d    
                    f.append(InlineKeyboardButton(text=f"{k}",callback_data=f"sch_month_{year_}_{month}_{d}"))
                button.append(f)
            button.append([InlineKeyboardButton("Kapat", callback_data="schclose")])
            await msg.edit(f"Sesli sohbeti planlamak istediğiniz ayın gününü seçin.\nbugün {thisday} {smonth} {year}. Bugünden önceki bir tarihin seçilmesi gelecek yıl olarak kabul edilecektir. {year+1}", reply_markup=InlineKeyboardMarkup(button))



        return
    buttons = [
        [
            InlineKeyboardButton('⚙️ Güncelleme', url='https://t.me/SakirBey1'),
            InlineKeyboardButton('🧩 Grup', url='https://t.me/kpdailesi')
        ],
        [
            InlineKeyboardButton('👨🏼‍🦯 Yardım', callback_data='help_main'),
            InlineKeyboardButton('🗑 Kapat', callback_data='close'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    k = await message.reply(HOME_TEXT.format(message.from_user.first_name, message.from_user.id), reply_markup=reply_markup)
    await delete_messages([message, k])



@Client.on_message(filters.command(["Yardım", f"help@{Config.BOT_USERNAME}"]))
async def show_help(client, message):
    reply_markup=InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Oynat", callback_data='help_play'),
                InlineKeyboardButton("ayarlar", callback_data=f"help_settings"),
                InlineKeyboardButton("Kayıt", callback_data='help_record'),
            ],
            [
                InlineKeyboardButton("zamanlama", callback_data="help_schedule"),
                InlineKeyboardButton("kontrol", callback_data='help_control'),
                InlineKeyboardButton("Adminler", callback_data="help_admin"),
            ],
            [
                InlineKeyboardButton("Çeşitli", callback_data='help_misc'),
                InlineKeyboardButton("Yapılandırma Değişkenleri", callback_data='help_env'),
                InlineKeyboardButton("Kapat!", callback_data="close"),
            ],
        ]
        )
    if message.chat.type != "özel" and message.from_user is None:
        k=await message.reply(
            text="Anonim bir yönetici olduğunuz için burada size yardımcı olamam. PM'de yardım alın",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(f"Yardım", url=f"https://telegram.dog/{Config.BOT_USERNAME}?start=help"),
                    ]
                ]
            ),)
        await delete_messages([message, k])
        return
    if Config.msg.get('help') is not None:
        await Config.msg['help'].delete()
    Config.msg['help'] = await message.reply_text(
        "GrupMüzikBotu'nu kullanmayı öğrenin, Yardım menüsü gösteriliyor, Aşağıdaki seçeneklerden birini seçin.",
        reply_markup=reply_markup,
        disable_web_page_preview=True
        )
    #await delete_messages([message])
@Client.on_message(filters.command(['repo', f"repo@{Config.BOT_USERNAME}"]))
async def repo_(client, message):
    buttons = [
        [
            InlineKeyboardButton('🧩 Grubumuza Gelin', url='https://t.me/kpdailesi'),
            InlineKeyboardButton('💻 Developer-Sahib', url='https://t.me/SakirBey1'),     
        ],
        [
            InlineKeyboardButton("🎞 How to Deploy", url='https://youtu.be/mnWgZMrNe_0'),
            InlineKeyboardButton('🗑 Kapat!', callback_data='close'),
        ]
    ]
    await message.reply("<b> [💻Developer](https://t.me/SakirBey1) </b>", reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
    await delete_messages([message])

@Client.on_message(filters.command(['restart', 'update', f"restart@{Config.BOT_USERNAME}", f"update@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def update_handler(client, message):
    if Config.HEROKU_APP:
        k = await message.reply("Heroku APP bulundu, Güncellemek için uygulama yeniden başlatılıyor.")
        if Config.DATABASE_URI:
            msg = {"msg_id":k.message_id, "chat_id":k.chat.id}
            if not await db.is_saved("TEKRAR BAŞLAT"):
                db.add_config("TEKRAR BAŞLAT", msg)
            else:
                await db.edit_config("TEKRAR BAŞLAT", msg)
            await sync_to_db()
    else:
        k = await message.reply("Heroku APP bulunamadı, yeniden başlatılmaya çalışılıyor.")
        if Config.DATABASE_URI:
            msg = {"msg_id":k.message_id, "chat_id":k.chat.id}
            if not await db.is_saved("RESTART"):
                db.add_config("TEKRAR BAŞLAT", msg)
            else:
                await db.edit_config("TEKRAR BAŞLAT", msg)
    try:
        await message.delete()
    except:
        pass
    await update()

@Client.on_message(filters.command(['logs', f"logs@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def get_logs(client, message):
    m=await message.reply("Günlükler kontrol ediliyor...")
    if os.path.exists("botlog.txt"):
        await message.reply_document('botlog.txt', caption="Bot Logları")
        await m.delete()
        await delete_messages([message])
    else:
        k = await m.edit("Günlük dosyası bulunamadı.")
        await delete_messages([message, k])

@Client.on_message(filters.command(['env', f"env@{Config.BOT_USERNAME}", "config", f"config@{Config.BOT_USERNAME}"]) & sudo_filter & chat_filter)
async def set_heroku_var(client, message):
    with suppress(MessageIdInvalid, MessageNotModified):
        m = await message.reply("Yapılandırma değişkenleri kontrol ediliyor..")
        if " " in message.text:
            cmd, env = message.text.split(" ", 1)
            if "=" in env:
                var, value = env.split("=", 1)
            else:
                if env == "STARTUP_STREAM":
                    env_ = "STREAM_URL"
                elif env == "QUALITY":
                    env_ = "CUSTOM_QUALITY" 
                else:
                    env_ = env
                ENV_VARS = ["ADMINS", "SUDO", "CHAT", "LOG_GROUP", "STREAM_URL", "SHUFFLE", "ADMIN_ONLY", "REPLY_MESSAGE", 
                        "EDIT_TITLE", "RECORDING_DUMP", "RECORDING_TITLE", "IS_VIDEO", "IS_LOOP", "DELAY", "PORTRAIT", 
                        "IS_VIDEO_RECORD", "PTN", "CUSTOM_QUALITY"]
                if env_ in ENV_VARS:
                    await m.edit(f"Geçerli Değer `{env}`  is `{getattr(Config, env_)}`")
                    await delete_messages([message])
                    return
                else:
                    await m.edit("Bu geçersiz bir env değeridir. Mevcut env değişkenleri hakkında bilgi edinmek için env ile ilgili yardımı okuyun.")
                    await delete_messages([message, m])
                    return     
            
        else:
            await m.edit("env için herhangi bir değer sağlamadınız, doğru formatı izlemelisiniz.\nÖrnek: <code>/env CHAT=-1001302875094</code> CHAT'ı değiştirmek veya ayarlamak için var.\n<code>/env REPLY_MESSAGE= <code>silmek REPLY_MESSAGE.")
            await delete_messages([message, m])
            return

        if Config.DATABASE_URI and var in ["STARTUP_STREAM", "CHAT", "LOG_GROUP", "REPLY_MESSAGE", "DELAY", "RECORDING_DUMP", "QUALITY"]:      
            await m.edit("Mongo DB Bulundu, Yapılandırma değişkenleri ayarlanıyor...")
            await asyncio.sleep(2)  
            if not value:
                await m.edit(f"env için değer belirtilmedi. env'yi silmeye çalışıyorum {var}.")
                await asyncio.sleep(2)
                if var in ["STARTUP_STREAM", "CHAT", "DELAY"]:
                    await m.edit("Bu zorunlu bir değişkendir ve silinemez.")
                    await delete_messages([message, m]) 
                    return
                await edit_config(var, False)
                await m.edit(f"başarıyla silindi {var}")
                await delete_messages([message, m])           
                return
            else:
                if var in ["CHAT", "LOG_GROUP", "RECORDING_DUMP", "QUALITY"]:
                    try:
                        value=int(value)
                    except:
                        if var == "QUALITY":
                            if not value.lower() in ["düşük", "orta", "Yükseklik"]:
                                await m.edit("10 - 100 arasında bir değer belirtmelisiniz.")
                                await delete_messages([message, m])
                                return
                            else:
                                value = value.lower()
                                if value == "yüksek":
                                    value = 100
                                elif value == "orta":
                                    value = 66.9
                                elif value == "düşük":
                                    value = 50
                        else:
                            await m.edit("Bana bir sohbet kimliği vermelisin. Bir interger olmalı.")
                            await delete_messages([message, m])
                            return
                    if var == "CHAT":
                        await leave_call()
                        Config.ADMIN_CACHE=False
                        if Config.IS_RECORDING:
                            await stop_recording()
                        await cancel_all_schedules()
                        Config.CHAT=int(value)
                        await restart()
                    await edit_config(var, int(value))
                    if var == "QUALITY":
                        if Config.CALL_STATUS:
                            data=Config.DATA.get('FILE_DATA')
                            if not data \
                                or data.get('dur', 0) == 0:
                                await restart_playout()
                                return
                            k, reply = await seek_file(0)
                            if k == False:
                                await restart_playout()
                    await m.edit(f"Başarıyla değiştirildi {var} to {value}")
                    await delete_messages([message, m])
                    return
                else:
                    if var == "STARTUP_STREAM":
                        Config.STREAM_SETUP=False
                    await edit_config(var, value)
                    await m.edit(f"Başarıyla değiştirildi {var} to {value}")
                    await delete_messages([message, m])
                    await restart_playout()
                    return
        else:
            if not Config.HEROKU_APP:
                buttons = [[InlineKeyboardButton('Heroku API_KEY', url='https://dashboard.heroku.com/account/applications/authorizations/new'), InlineKeyboardButton('🗑 Kapat!', callback_data='close'),]]
                await m.edit(
                    text="Heroku uygulaması bulunamadı, bu komutun ayarlanması için aşağıdaki heroku değişkenlerinin ayarlanması gerekiyor.\n\n1. <code>HEROKU_API_KEY</code>: Heroku hesabınızın API anahtarı.\n2. <code>HEROKU_APP_NAME</code>: Heroku uygulamanızın adı.", 
                    reply_markup=InlineKeyboardMarkup(buttons)) 
                await delete_messages([message])
                return     
            config = Config.HEROKU_APP.config()
            if not value:
                await m.edit(f"env için değer belirtilmedi. env'yi silmeye çalışıyorum {var}.")
                await asyncio.sleep(2)
                if var in ["STARTUP_STREAM", "CHAT", "DELAY", "API_ID", "API_HASH", "BOT_TOKEN", "SESSION_STRING", "ADMINS"]:
                    await m.edit("Bunlar zorunlu değişkenlerdir ve silinemezler.")
                    await delete_messages([message, m])
                    return
                if var in config:
                    await m.edit(f"başarıyla silindi {var}")
                    await asyncio.sleep(2)
                    await m.edit("Şimdi değişiklik yapmak için uygulamayı yeniden başlatıyoruz.")
                    if Config.DATABASE_URI:
                        msg = {"msg_id":m.message_id, "chat_id":m.chat.id}
                        if not await db.is_saved("TEKRAR BAŞLAT"):
                            db.add_config("TEKRAR BAŞLAT", msg)
                        else:
                            await db.edit_config("TEKRAR BAŞLAT", msg)
                    del config[var]                
                    config[var] = None               
                else:
                    k = await m.edit(f"env adlı bir ortam yok {var} bulundu. Hiçbir şey değişmedi.")
                    await delete_messages([message, k])
                return
            if var in config:
                await m.edit(f"Değişken zaten bulundu. Şimdi düzenlendi {value}")
            else:
                await m.edit(f"Değişken bulunamadı, Şimdi yeni değişken olarak ayarlanıyor.")
            await asyncio.sleep(2)
            await m.edit(f"Başarıyla ayarlandı {var} değeri olan {value}, Şimdi değişikliklerin yürürlüğe girmesi için yeniden başlatılıyor...")
            if Config.DATABASE_URI:
                msg = {"msg_id":m.message_id, "chat_id":m.chat.id}
                if not await db.is_saved("TEKRAR BAŞLAT"):
                    db.add_config("TEKRAR BAŞLAT", msg)
                else:
                    await db.edit_config("TEKRAR BAŞLAT", msg)
            config[var] = str(value)




