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

from .logger import LOGGER
from config import Config
import os
import time
from threading import Thread
import sys
if Config.DATABASE_URI:
    from .database import db
from pyrogram import (
    Client, 
    filters
)
from pyrogram.errors import (
    MessageIdInvalid, 
    MessageNotModified
)
from pyrogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Message
)
from contextlib import suppress

debug = Client(
    "hata ayıklama",
    Config.API_ID,
    Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
)


@debug.on_message(filters.command(['env', f"env@{Config.BOT_USERNAME}", "config", f"config@{Config.BOT_USERNAME}"]) & filters.private & filters.user(Config.ADMINS))
async def set_heroku_var(client, message):
    if message.from_user.id not in Config.SUDO:
        return await message.reply(f"/env command can only be used by creator of the bot, ({str(Config.SUDO)})")
    with suppress(MessageIdInvalid, MessageNotModified):
        m = await message.reply("Yapılandırma değişkenleri kontrol ediliyor...")
        if " " in message.text:
            cmd, env = message.text.split(" ", 1)
            if  not "=" in env:
                await m.edit("env için değer belirtmelisiniz.\nÖrnek: /env Sohpet=-100213658211")
                return
            var, value = env.split("=", 1)
        else:
            await m.edit("env için herhangi bir değer sağlamadınız, doğru formatı izlemelisiniz.\nÖrnek: <code>/env CHAT=-1020202020202</code> CHAT'ı değiştirmek veya ayarlamak için var.\n<code>/env REPLY_MESSAGE= <code>Silmek REPLY_MESSAGE.")
            return

        if Config.DATABASE_URI and var in ["STARTUP_STREAM", "CHAT", "LOG_GROUP", "REPLY_MESSAGE", "DELAY", "RECORDING_DUMP"]:      
            await m.edit("Mongo DB Bulundu, Yapılandırma değişkenleri ayarlanıyor...") 
            if not value:
                await m.edit(f"env için değer belirtilmedi. env'yi silmeye çalışıyorum {var}.")
                if var in ["STARTUP_STREAM", "CHAT", "DELAY"]:
                    await m.edit("Bu zorunlu bir değişkendir ve silinemez.")
                    return
                await edit_config(var, False)
                await m.edit(f"Başarıyla silindi {var}")
           
                return
            else:
                if var in ["CHAT", "LOG_GROUP", "RECORDING_DUMP"]:
                    try:
                        value=int(value)
                    except:
                        await m.edit("Bana bir sohbet kimliği vermelisin. Bir interger olmalı.")
        
                        return
                    if var == "CHAT":
                        Config.ADMIN_CACHE=False
                        Config.CHAT=int(value)
                    await edit_config(var, int(value))
                    await m.edit(f"Başarıyla değiştirildi {var} to {value}")
    
                    return
                else:
                    if var == "STARTUP_STREAM":
                        Config.STREAM_SETUP=False
                    await edit_config(var, value)
                    await m.edit(f"Başarıyla değiştirildi {var} to {value}")
                    return
        else:
            if not Config.HEROKU_APP:
                buttons = [[InlineKeyboardButton('Heroku API_KEY', url='https://dashboard.heroku.com/account/applications/authorizations/new'), InlineKeyboardButton('🗑 Kapat', callback_data='close'),]]
                await m.edit(
                    text="No heroku app found, this command needs the following heroku vars to be set.\n\n1. <code>HEROKU_API_KEY</code>: Your heroku account api key.\n2. <code>HEROKU_APP_NAME</code>: Your heroku app name.", 
                    reply_markup=InlineKeyboardMarkup(buttons)) 
                return     
            config = Config.HEROKU_APP.config()
            if not value:
                await m.edit(f"env için değer belirtilmedi. env'yi silmeye çalışıyorum {var}.")
                if var in ["STARTUP_STREAM", "CHAT", "DELAY", "API_ID", "API_HASH", "BOT_TOKEN", "SESSION_STRING", "ADMINS"]:
                    await m.edit("Bunlar zorunlu değişkenlerdir ve silinemezler.")
    
                    return
                if var in config:
                    await m.edit(f"Başarıyla silindi {var}")
                    await m.edit("Şimdi değişiklik yapmak için uygulamayı yeniden başlatıyoruz.")
                    if Config.DATABASE_URI:
                        msg = {"msg_id":m.message_id, "chat_id":m.chat.id}
                        if not await db.is_saved("Tekrar başlat"):
                            db.add_config("Tekrar başlat", msg)
                        else:
                            await db.edit_config("Tekrar Başlat", msg)
                    del config[var]                
                    config[var] = None               
                else:
                    k = await m.edit(f"env adlı bir ortam yok {var} bulundu. Hiçbir şey değişmedi.")
                return
            if var in config:
                await m.edit(f"Değişken zaten bulundu. Şimdi düzenlendi {value}")
            else:
                await m.edit(f"Değişken bulunamadı, Şimdi yeni değişken olarak ayarlanıyor.")
            await m.edit(f"Başarıyla ayarlandı {var} değeri olan {value}, Şimdi değişikliklerin yürürlüğe girmesi için yeniden başlatılıyor...")
            if Config.DATABASE_URI:
                msg = {"msg_id":m.message_id, "chat_id":m.chat.id}
                if not await db.is_saved("TEKRAR BAŞLAT"):
                    db.add_config("TEKRAR BAŞLAT", msg)
                else:
                    await db.edit_config("TEKRAR BAŞLAT", msg)
            config[var] = str(value)

@debug.on_message(filters.command(["Tekrar Başlat", f"restart@{Config.BOT_USERNAME}"]) & filters.private & filters.user(Config.ADMINS))
async def update(bot, message):
    m=await message.reply("Yeni değişikliklerle yeniden başlatılıyor...")
    if Config.DATABASE_URI:
        msg = {"msg_id":m.message_id, "chat_id":m.chat.id}
        if not await db.is_saved("Tekrar Başlat"):
            db.add_config("Tekrar Başlat", msg)
        else:
            await db.edit_config("Tekrar Başlat", msg)
    if Config.HEROKU_APP:
        Config.HEROKU_APP.restart()
    else:
        Thread(
            target=stop_and_restart()
            ).start()

@debug.on_message(filters.command(["temiz çalma listesi", f"clearplaylist@{Config.BOT_USERNAME}"]) & filters.private & filters.user(Config.ADMINS))
async def clear_play_list(client, m: Message):
    if not Config.playlist:
        k = await m.reply("Oynatma listesi boş.")  
        return
    Config.playlist.clear()
    k=await m.reply_text(f"Oynatma Listesi Temizlendi.")
    await clear_db_playlist(all=True)

    
@debug.on_message(filters.command(["Atla", f"skip@{Config.BOT_USERNAME}"]) & filters.private & filters.user(Config.ADMINS))
async def skip_track(_, m: Message):
    msg=await m.reply('kuyruktan atlamaya çalışıyor..')
    if not Config.playlist:
        await msg.edit("Oynatma Listesi Boş.")
        return
    if len(m.command) == 1:
        old_track = Config.playlist.pop(0)
        await clear_db_playlist(song=old_track)
    else:
        #https://github.com/callsmusic/tgvc-userbot/blob/dev/plugins/vc/player.py#L268-L288
        try:
            items = list(dict.fromkeys(m.command[1:]))
            items = [int(x) for x in items if x.isdigit()]
            items.sort(reverse=True)
            for i in items:
                if 2 <= i <= (len(Config.playlist) - 1):
                    await msg.edit(f"Oynatma Listesinden Başarıyla Kaldırıldı- {i}. **{Config.playlist[i][1]}**")
                    await clear_db_playlist(song=Config.playlist[i])
                    Config.playlist.pop(i)
                else:
                    await msg.edit(f"İlk iki şarkıyı atlayamazsın- {i}")
        except (ValueError, TypeError):
            await msg.edit("Geçersiz Giriş")
    pl=await get_playlist_str()
    await msg.edit(pl, disable_web_page_preview=True)


@debug.on_message(filters.command(['Loglar', f"logs@{Config.BOT_USERNAME}"]) & filters.private & filters.user(Config.ADMINS))
async def get_logs(client, message):
    m=await message.reply("Günlükler kontrol ediliyor...")
    if os.path.exists("botlog.txt"):
        await message.reply_document('botlog.txt', caption="Bot Logs")
        await m.delete()
    else:
        k = await m.edit("Günlük dosyası bulunamadı.")

@debug.on_message(filters.text & filters.private)
async def reply_else(bot, message):
    await message.reply(f"Geliştirme modu etkinleştirildi.\nBu, botun başlatılmasında bazı hatalar olduğunda ortaya çıkar.\nGeliştirme modunda yalnızca Yapılandırma komutları çalışır.\nKullanılabilir komutlar /env, /skip, /clearplaylist ve /restart ve /logs\n\n**Geliştirme modunun etkinleştirilmesinin nedeni şuydu:**\n\n`{str(Config.STARTUP_ERROR)}`")

def stop_and_restart():
    os.system("git çek")
    time.sleep(10)
    os.execl(sys.executable, sys.executable, *sys.argv)

async def get_playlist_str():
    if not Config.playlist:
        pl = f"🔈 Oynatma listesi boş.)ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
    else:
        if len(Config.playlist)>=25:
            tplaylist=Config.playlist[:25]
            pl=f"Toplam ilk 25 şarkı listeleniyor {len(Config.playlist)} Şarkılar.\n"
            pl += f"▶️ **Oynatma Listesi**: ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ\n" + "\n".join([
                f"**{i}**. **🎸{x[1]}**\n   👤**tarafından talep edildi:** {x[4]}"
                for i, x in enumerate(tplaylist)
                ])
            tplaylist.clear()
        else:
            pl = f"▶️ **Oynatma Listesi**: ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ\n" + "\n".join([
                f"**{i}**. **🎸{x[1]}**\n   👤**tarafından talep edildi:** {x[4]}\n"
                for i, x in enumerate(Config.playlist)
            ])
    return pl



async def sync_to_db():
    if Config.DATABASE_URI:
        await check_db() 
        await db.edit_config("ADMINS", Config.ADMINS)
        await db.edit_config("IS_VIDEO", Config.IS_VIDEO)
        await db.edit_config("IS_LOOP", Config.IS_LOOP)
        await db.edit_config("REPLY_PM", Config.REPLY_PM)
        await db.edit_config("ADMIN_ONLY", Config.ADMIN_ONLY)  
        await db.edit_config("SHUFFLE", Config.SHUFFLE)
        await db.edit_config("EDIT_TITLE", Config.EDIT_TITLE)
        await db.edit_config("CHAT", Config.CHAT)
        await db.edit_config("SUDO", Config.SUDO)
        await db.edit_config("REPLY_MESSAGE", Config.REPLY_MESSAGE)
        await db.edit_config("LOG_GROUP", Config.LOG_GROUP)
        await db.edit_config("STREAM_URL", Config.STREAM_URL)
        await db.edit_config("DELAY", Config.DELAY)
        await db.edit_config("SCHEDULED_STREAM", Config.SCHEDULED_STREAM)
        await db.edit_config("SCHEDULE_LIST", Config.SCHEDULE_LIST)
        await db.edit_config("IS_VIDEO_RECORD", Config.IS_VIDEO_RECORD)
        await db.edit_config("IS_RECORDING", Config.IS_RECORDING)
        await db.edit_config("WAS_RECORDING", Config.WAS_RECORDING)
        await db.edit_config("PORTRAIT", Config.PORTRAIT)
        await db.edit_config("RECORDING_DUMP", Config.RECORDING_DUMP)
        await db.edit_config("RECORDING_TITLE", Config.RECORDING_TITLE)
        await db.edit_config("HAS_SCHEDULE", Config.HAS_SCHEDULE)

async def sync_from_db():
    if Config.DATABASE_URI:  
        await check_db()     
        Config.ADMINS = await db.get_config("ADMINS") 
        Config.IS_VIDEO = await db.get_config("IS_VIDEO")
        Config.IS_LOOP = await db.get_config("IS_LOOP")
        Config.REPLY_PM = await db.get_config("REPLY_PM")
        Config.ADMIN_ONLY = await db.get_config("ADMIN_ONLY")
        Config.SHUFFLE = await db.get_config("SHUFFLE")
        Config.EDIT_TITLE = await db.get_config("EDIT_TITLE")
        Config.CHAT = int(await db.get_config("CHAT"))
        Config.playlist = await db.get_playlist()
        Config.LOG_GROUP = await db.get_config("LOG_GROUP")
        Config.SUDO = await db.get_config("SUDO") 
        Config.REPLY_MESSAGE = await db.get_config("REPLY_MESSAGE") 
        Config.DELAY = await db.get_config("DELAY") 
        Config.STREAM_URL = await db.get_config("STREAM_URL") 
        Config.SCHEDULED_STREAM = await db.get_config("SCHEDULED_STREAM") 
        Config.SCHEDULE_LIST = await db.get_config("SCHEDULE_LIST")
        Config.IS_VIDEO_RECORD = await db.get_config('IS_VIDEO_RECORD')
        Config.IS_RECORDING = await db.get_config("IS_RECORDING")
        Config.WAS_RECORDING = await db.get_config('WAS_RECORDING')
        Config.PORTRAIT = await db.get_config("PORTRAIT")
        Config.RECORDING_DUMP = await db.get_config("RECORDING_DUMP")
        Config.RECORDING_TITLE = await db.get_config("RECORDING_TITLE")
        Config.HAS_SCHEDULE = await db.get_config("HAS_SCHEDULE")

async def add_to_db_playlist(song):
    if Config.DATABASE_URI:
        song_={str(k):v for k,v in song.items()}
        db.add_to_playlist(song[5], song_)

async def clear_db_playlist(song=None, all=False):
    if Config.DATABASE_URI:
        if all:
            await db.clear_playlist()
        else:
            await db.del_song(song[5])

async def check_db():
    if not await db.is_saved("ADMINS"):
        db.add_config("ADMINS", Config.ADMINS)
    if not await db.is_saved("IS_VIDEO"):
        db.add_config("IS_VIDEO", Config.IS_VIDEO)
    if not await db.is_saved("IS_LOOP"):
        db.add_config("IS_LOOP", Config.IS_LOOP)
    if not await db.is_saved("REPLY_PM"):
        db.add_config("REPLY_PM", Config.REPLY_PM)
    if not await db.is_saved("ADMIN_ONLY"):
        db.add_config("ADMIN_ONLY", Config.ADMIN_ONLY)
    if not await db.is_saved("SHUFFLE"):
        db.add_config("SHUFFLE", Config.SHUFFLE)
    if not await db.is_saved("EDIT_TITLE"):
        db.add_config("EDIT_TITLE", Config.EDIT_TITLE)
    if not await db.is_saved("CHAT"):
        db.add_config("CHAT", Config.CHAT)
    if not await db.is_saved("SUDO"):
        db.add_config("SUDO", Config.SUDO)
    if not await db.is_saved("REPLY_MESSAGE"):
        db.add_config("REPLY_MESSAGE", Config.REPLY_MESSAGE)
    if not await db.is_saved("STREAM_URL"):
        db.add_config("STREAM_URL", Config.STREAM_URL)
    if not await db.is_saved("DELAY"):
        db.add_config("DELAY", Config.DELAY)
    if not await db.is_saved("LOG_GROUP"):
        db.add_config("LOG_GROUP", Config.LOG_GROUP)
    if not await db.is_saved("SCHEDULED_STREAM"):
        db.add_config("SCHEDULED_STREAM", Config.SCHEDULED_STREAM)
    if not await db.is_saved("SCHEDULE_LIST"):
        db.add_config("SCHEDULE_LIST", Config.SCHEDULE_LIST)
    if not await db.is_saved("IS_VIDEO_RECORD"):
        db.add_config("IS_VIDEO_RECORD", Config.IS_VIDEO_RECORD)
    if not await db.is_saved("PORTRAIT"):
        db.add_config("PORTRAIT", Config.PORTRAIT)  
    if not await db.is_saved("IS_RECORDING"):
        db.add_config("IS_RECORDING", Config.IS_RECORDING)
    if not await db.is_saved('WAS_RECORDING'):
        db.add_config('WAS_RECORDING', Config.WAS_RECORDING)
    if not await db.is_saved("RECORDING_DUMP"):
        db.add_config("RECORDING_DUMP", Config.RECORDING_DUMP)
    if not await db.is_saved("RECORDING_TITLE"):
        db.add_config("RECORDING_TITLE", Config.RECORDING_TITLE)
    if not await db.is_saved('HAS_SCHEDULE'):
        db.add_config("HAS_SCHEDULE", Config.HAS_SCHEDULE)

async def edit_config(var, value):
    if var == "STARTUP_STREAM":
        Config.STREAM_URL = value
    elif var == "CHAT":
        Config.CHAT = int(value)
    elif var == "LOG_GROUP":
        Config.LOG_GROUP = int(value)
    elif var == "DELAY":
        Config.DELAY = int(value)
    elif var == "REPLY_MESSAGE":
        Config.REPLY_MESSAGE = value
    elif var == "RECORDING_DUMP":
        Config.RECORDING_DUMP = value
    await sync_to_db()

    
