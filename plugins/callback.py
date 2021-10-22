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
from pyrogram import Client
from contextlib import suppress
from config import Config
from asyncio import sleep
import datetime
import pytz
import calendar
from utils import (
    cancel_all_schedules,
    delete_messages,
    get_admins, 
    get_buttons, 
    get_playlist_str,
    leave_call, 
    mute, 
    pause,
    recorder_settings, 
    restart, 
    restart_playout, 
    resume,
    schedule_a_play, 
    seek_file, 
    set_config, 
    settings_panel, 
    shuffle_playlist, 
    skip,
    start_record_stream,
    stop_recording,
    sync_to_db, 
    unmute,
    volume,
    volume_buttons
    )
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from pyrogram.errors import (
    MessageNotModified,
    MessageIdInvalid,
    QueryIdInvalid
)
from pyrogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)

IST = pytz.timezone(Config.TIME_ZONE)

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    with suppress(MessageIdInvalid, MessageNotModified, QueryIdInvalid):
        admins = await get_admins(Config.CHAT)
        if query.data.startswith("info"):
            me, you = query.data.split("_")
            text="Join @kpdailesi"
            if you == "Ses":
                await query.answer()
                await query.message.edit_reply_markup(reply_markup=await volume_buttons())
                return
            if you == "Oyuncu":
                if not Config.CALL_STATUS:
                    return await query.answer("Hiçbir şey Oynamamak.", show_alert=True)
                await query.message.edit_reply_markup(reply_markup=await get_buttons())
                await query.answer()
                return
            if you == "video":
                text="Botunuzu Video / Ses Oynatıcı olarak değiştirin."
            elif you == "Karıştır":
                text="Otomatik oynatma listesi karıştırmayı etkinleştirin veya devre dışı bırakın"
            elif you == "yönetici":
                text="Oynatma komutunu yalnızca yöneticiler için kısıtlamak için etkinleştirin."
            elif you == "mod":
                text="Kesintisiz oynatmanın etkinleştirilmesi, oynatıcının 7 gün 24 saat çalışmasını ve yeniden başlatıldığında otomatik olarak başlatılmasını sağlar. "
            elif you == "başlık":
                text="VideoChat başlığını Şu anda çalan şarkının başlığına göre düzenlemeyi etkinleştirin."
            elif you == "cevap vermek":
                text="Userbot için gönderilen mesajların otomatik olarak yanıtlanıp yanıtlanmayacağını seçin. "
            elif you == "video kaydı":
                text = "Hem video hem de ses kaydetmeyi etkinleştirin, devre dışı bırakılırsa yalnızca ses kaydedilir."
            elif you == "video boyutu":
                text = "Kayıt videosunun boyutlarını seçin"
            elif you == "düzeltme":
                text = "Sohbet kayıtlarınız için özel bir başlık, Başlık belirlemek için /rtitle komutunu kullanın"
            elif you == "recdmb":
                text = "Tüm kayıtların yönlendirildiği bir kanal. Kullanıcı hesabının orada yönetici olduğundan emin olun. /env veya /config kullanarak birini ayarlayın."
            await query.answer(text=text, show_alert=True)
            return


        elif query.data.startswith("yardım"):
            if query.message.chat.type != "özel" and query.message.reply_to_message.from_user is None:
                return await query.answer("Anonim bir yönetici olduğunuz için burada size yardımcı olamam, bana özel sohbette mesaj atın.", show_alert=True)
            elif query.message.chat.type != "özel" and query.from_user.id != query.message.reply_to_message.from_user.id:
                return await query.answer("tamam", show_alert=True)
            me, nyav = query.data.split("_")
            back=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("geri", callback_data="help_main"),
                        InlineKeyboardButton("kapat", callback_data="close"),
                    ],
                ]
                )
            if nyav == 'main':
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
                            InlineKeyboardButton("Yapılandırma Değişkenleri", callback_data='help_env'),
                            InlineKeyboardButton("Kapat", callback_data="close"),
                        ],
                    ]
                    )
                await query.message.edit("Yardım menüsü gösteriliyor, Aşağıdaki seçeneklerden birini seçin.", reply_markup=reply_markup, disable_web_page_preview=True)
            elif nyav == 'oynat':
                await query.message.edit(Config.PLAY_HELP, reply_markup=back, disable_web_page_preview=True)
            elif nyav == 'ayarlar':
                await query.message.edit(Config.SETTINGS_HELP, reply_markup=back, disable_web_page_preview=True)
            elif nyav == 'Takvim':
                await query.message.edit(Config.SCHEDULER_HELP, reply_markup=back, disable_web_page_preview=True)
            elif nyav == 'kontrol':
                await query.message.edit(Config.CONTROL_HELP, reply_markup=back, disable_web_page_preview=True)
            elif nyav == 'yönetici':
                await query.message.edit(Config.ADMIN_HELP, reply_markup=back, disable_web_page_preview=True)
            elif nyav == 'çeşitli':
                await query.message.edit(Config.MISC_HELP, reply_markup=back, disable_web_page_preview=True)
            elif nyav == 'kayıt':
                await query.message.edit(Config.RECORDER_HELP, reply_markup=back, disable_web_page_preview=True)
            elif nyav == 'env':
                await query.message.edit(Config.ENV_HELP, reply_markup=back, disable_web_page_preview=True)
            return
            
        if not query.from_user.id in admins:
            await query.answer(
                "😒 Played Joji.mp3",
                show_alert=True
                )
            return
        #scheduler stuffs
        if query.data.startswith("sch"):
            if query.message.chat.type != "özel" and query.message.reply_to_message.from_user is None:
                return await query.answer("Anonim bir yönetici olduğunuz için burada zamanlamayı kullanamazsınız. Özel sohbetten programlayın.", show_alert=True)
            if query.message.chat.type != "özel" and query.from_user.id != query.message.reply_to_message.from_user.id:
                return await query.answer("Tamam", show_alert=True)
            data = query.data
            today = datetime.datetime.now(IST)
            smonth=today.strftime("%B")
            obj = calendar.Calendar()
            thisday = today.day
            year = today.year
            month = today.month
            if data.startswith("sch_month"):
                none, none , yea_r, month_, day = data.split("_")
                if yea_r == "Seç":
                    year=int(year)
                    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                    button=[]
                    button_=[]
                    k=0
                    for month in months:
                        k+=1
                        year_ = year
                        if k < int(today.month):
                            year_ += 1
                            button_.append([InlineKeyboardButton(text=f"{str(month)}  {str(year_)}",callback_data=f"sch_showdate_{year_}_{k}")])
                        else:
                            button.append([InlineKeyboardButton(text=f"{str(month)}  {str(year_)}",callback_data=f"sch_showdate_{year_}_{k}")])
                    button = button + button_
                    button.append([InlineKeyboardButton("Kapat!", callback_data="schclose")])
                    await query.message.edit("Şimdi sesli sohbet planlamak için ayı seçinㅤ ㅤㅤ", reply_markup=InlineKeyboardMarkup(button))
                elif day == "yok":
                    return
                else:
                    year = int(yea_r)
                    month = int(month_)
                    date = int(day)
                    datetime_object = datetime.datetime.strptime(str(month), "%m")
                    smonth = datetime_object.strftime("%B")
                    button=[]
                    if year == today.year and month == today.month and date == today.day:
                        now = today.hour
                    else:
                        now=0
                    l = list()
                    for i in range(now, 24):
                        l.append(i)
                    splited=[l[i:i + 6] for i in range(0, len(l), 6)]
                    for i in splited:
                        k=[]
                        for d in i:
                            k.append(InlineKeyboardButton(text=f"{d}",callback_data=f"sch_day_{year}_{month}_{date}_{d}"))
                        button.append(k)
                    if month == today.month and date < today.day and year==today.year+1:
                        pyear=year-1
                    else:
                        pyear=year
                    button.append([InlineKeyboardButton("Geri", callback_data=f"sch_showdate_{pyear}_{month}"), InlineKeyboardButton("Kapat!", callback_data="schclose")])
                    await query.message.edit(f"saatini seçin {date} {smonth} {year} Bir sesli sohbet planlamak için", reply_markup=InlineKeyboardMarkup(button))

            elif data.startswith("sch_day"):
                none, none, year, month, day, hour = data.split("_")
                year = int(year)
                month = int(month)
                day = int(day)
                hour = int(hour)
                datetime_object = datetime.datetime.strptime(str(month), "%m")
                smonth = datetime_object.strftime("%B")
                if year == today.year and month == today.month and day == today.day and hour == today.hour:
                    now=today.minute
                else:
                    now=0
                button=[]
                l = list()
                for i in range(now, 60):
                    l.append(i)
                for i in range(0, len(l), 6):
                    chunk = l[i:i + 6]
                    k=[]
                    for d in chunk:
                        k.append(InlineKeyboardButton(text=f"{d}",callback_data=f"sch_minute_{year}_{month}_{day}_{hour}_{d}"))
                    button.append(k)
                button.append([InlineKeyboardButton("Geri", callback_data=f"sch_month_{year}_{month}_{day}"), InlineKeyboardButton("Kapat", callback_data="schclose")])
                await query.message.edit(f"Dakikayı seçin {hour}saat açık {day} {smonth} {year} Sesli sohbeti planlamak için", reply_markup=InlineKeyboardMarkup(button))

            elif data.startswith("sch_minute"):
                none, none, year, month, day, hour, minute = data.split("_")
                year = int(year)
                month = int(month)
                day = int(day)
                hour = int(hour)
                minute = int(minute)
                datetime_object = datetime.datetime.strptime(str(month), "%m")
                smonth = datetime_object.strftime("%B")
                if year == today.year and month == today.month and day == today.day and hour == today.hour and minute <= today.minute:
                    await query.answer("Geçmişe gidecek bir zaman makinem yok!!!.")
                    return 
                final=f"{day}th {smonth} {year} at {hour}:{minute}"
                button=[
                    [
                        InlineKeyboardButton("Onaylamak", callback_data=f"schconfirm_{year}-{month}-{day} {hour}:{minute}"),
                        InlineKeyboardButton("Geri", callback_data=f"sch_day_{year}_{month}_{day}_{hour}")
                    ],
                    [
                        InlineKeyboardButton("Kapat!", callback_data="schclose")
                    ]
                ]
                data=Config.SCHEDULED_STREAM.get(f"{query.message.chat.id}_{query.message.message_id}")
                if not data:
                    await query.answer("Bu programın süresi doldu", show_alert=True)
                if data['3'] == "telegram":
                    title=data['1']
                else:
                    title=f"[{data['1']}]({data['2']})"
                await query.message.edit(f"Akışınız {title} şimdi başlaması planlanıyor {final}\n\nSaati onaylamak için Onayla'ya tıklayın.", reply_markup=InlineKeyboardMarkup(button), disable_web_page_preview=True)                

            elif data.startswith("sch_showdate"):
                tyear=year
                none, none, year, month = data.split("_")
                datetime_object = datetime.datetime.strptime(month, "%m")
                thissmonth = datetime_object.strftime("%B")
                obj = calendar.Calendar()
                thisday = today.day
                year = int(year)
                month = int(month)
                m=obj.monthdayscalendar(year, month)
                button=[]
                button.append([InlineKeyboardButton(text=f"{str(thissmonth)}  {str(year)}",callback_data=f"sch_month_choose_none_none")])
                days=["Mon", "Tues", "Wed", "Thu", "Fri", "Sat", "Sun"]
                f=[]
                for day in days:
                    f.append(InlineKeyboardButton(text=f"{day}",callback_data=f"day_info_none"))
                button.append(f)
                for one in m:
                    f=[]
                    for d in one:
                        year_=year
                        if year==today.year and month == today.month and d < int(today.day):
                            year_ += 1
                        if d == 0:
                            k="\u2063"
                            d="yok"
                        else:
                            k=d
                        f.append(InlineKeyboardButton(text=f"{k}",callback_data=f"sch_month_{year_}_{month}_{d}"))
                    button.append(f)
                button.append([InlineKeyboardButton("kapat", callback_data="schclose")])
                await query.message.edit(f"Sesli sohbeti planlamak istediğiniz ayın gününü seçin.\nBugün {thisday} {smonth} {tyear}. Bugünden önce bir tarih seçilmesi gelecek yıl olarak kabul edilecektir. {year+1}", reply_markup=InlineKeyboardMarkup(button))

            elif data.startswith("schonayla"):
                none, date = data.split("_")
                date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M')
                local_dt = IST.localize(date, is_dst=None)
                utc_dt = local_dt.astimezone(pytz.utc).replace(tzinfo=None)
                job_id=f"{query.message.chat.id}_{query.message.message_id}"
                Config.SCHEDULE_LIST.append({"job_id":job_id, "date":utc_dt})
                Config.SCHEDULE_LIST = sorted(Config.SCHEDULE_LIST, key=lambda k: k['date'])
                await schedule_a_play(job_id, utc_dt)
                await query.message.edit(f"Akış için başarıyla planlandı <code> {date.strftime('%b %d %Y, %I:%M %p')} </code>")
                await delete_messages([query.message, query.message.reply_to_message])
                
            elif query.data == 'schcancellall':
                await cancel_all_schedules()
                await query.message.edit("Tüm Planlanmış Akışlar başarıyla iptal edildi.")

            elif query.data == "schcancel":
                buttons = [
                    [
                        InlineKeyboardButton('Evet eminim!!', callback_data='schcancelall'),
                        InlineKeyboardButton('Hayır', callback_data='schclose'),
                    ]
                ]
                await query.message.edit("Planlanmış tüm akışları iptal etmek istediğinizden emin misiniz?", reply_markup=InlineKeyboardMarkup(buttons))
            elif data == "schclose":
                await query.answer("Menü Kapalı")
                await query.message.delete()
                await query.message.reply_to_message.delete()

        elif query.data == "Karıştır":
            if not Config.playlist:
                await query.answer("Oynatma listesi boş.", show_alert=True)
                return
            await shuffle_playlist()
            await query.answer("Oynatma listesi karıştırıldı.")
            await sleep(1)        
            await query.message.edit_reply_markup(reply_markup=await get_buttons())
    

        elif query.data.lower() == "duraklat":
            if Config.PAUSE:
                await query.answer("Zaten Duraklatıldı", show_alert=True)
            else:
                await pause()
                await query.answer("Akış Duraklatıldı")
                await sleep(1)

            await query.message.edit_reply_markup(reply_markup=await get_buttons())
 
        
        elif query.data.lower() == "devam et":   
            if not Config.PAUSE:
                await query.answer("Devam etmek için hiçbir şey duraklatılmadı", show_alert=True)
            else:
                await resume()
                await query.answer("Akışı azalttı")
                await sleep(1)
            await query.message.edit_reply_markup(reply_markup=await get_buttons())
          
        elif query.data=="atla": 
            if not Config.playlist:
                await query.answer("Çalma listesinde şarkı yok", show_alert=True)
            else:
                await query.answer("Oynatma listesinden atlanmaya çalışılıyor.")
                await skip()
                await sleep(1)
            if Config.playlist:
                title=f"<b>{Config.playlist[0][1]}</b>\nㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
            elif Config.STREAM_LINK:
                title=f"<b>Kullanarak Akış [Url]({Config.DATA['FILE_DATA']['file']})</b>ㅤ  ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
            else:
                title=f"<b>Akış Başlangıcı [stream]({Config.STREAM_URL})</b> ㅤ ㅤ  ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
            await query.message.edit(f"<b>{title}</b>",
                disable_web_page_preview=True,
                reply_markup=await get_buttons()
            )

        elif query.data=="tekrar oynatma":
            if not Config.playlist:
                await query.answer("Çalma listesinde şarkı yok", show_alert=True)
            else:
                await query.answer("oynatıcıyı yeniden başlatmaya çalışmak")
                await restart_playout()
                await sleep(1)
            await query.message.edit_reply_markup(reply_markup=await get_buttons())


        elif query.data.lower() == "sessiz":
            if Config.MUTED:
                await unmute()
                await query.answer("Sesi açılmamış akış")
            else:
                await mute()
                await query.answer("Sessiz akış")
            await sleep(1)
            await query.message.edit_reply_markup(reply_markup=await volume_buttons())

        elif query.data.lower() == 'aramak':
            if not Config.CALL_STATUS:
                return await query.answer("Hiçbir şey Oynamamak.", show_alert=True)
            #if not (Config.playlist or Config.STREAM_LINK):
                #return await query.answer("Başlangıç ​​akışı aranamıyor.", show_alert=True)
            await query.answer("aramaya çalışıyor.")
            data=Config.DATA.get('FILE_DATA')
            if not data.get('dur', 0) or \
                data.get('dur') == 0:
                return await query.answer("Bu bir canlı yayındır ve aranamaz.", show_alert=True)
            k, reply = await seek_file(10)
            if k == False:
                return await query.answer(reply, show_alert=True)
            await query.message.edit_reply_markup(reply_markup=await get_buttons())

        elif query.data.lower() == 'geri sarma':
            if not Config.CALL_STATUS:
                return await query.answer("Hiçbir şey Oynamamak.", show_alert=True)
            #if not (Config.playlist or Config.STREAM_LINK):
                #return await query.answer("Başlangıç ​​akışı aranamıyor.", show_alert=True)
            await query.answer("geri sarmaya çalışıyor.")
            data=Config.DATA.get('FILE_DATA')
            if not data.get('dur', 0) or \
                data.get('dur') == 0:
                return await query.answer("Bu bir canlı yayındır ve aranamaz.", show_alert=True)
            k, reply = await seek_file(-10)
            if k == False:
                return await query.answer(reply, show_alert=True)
            await query.message.edit_reply_markup(reply_markup=await get_buttons())

    
        elif query.data == 'Tekrar Başlat':
            if not Config.CALL_STATUS:
                if not Config.playlist:
                    await query.answer("Oyuncu boş, başlıyor STARTUP_STREAM.")
                else:
                    await query.answer('Oynatma listesini devam ettirme')
            await query.answer("Oyuncuyu yeniden başlatmak")
            await restart()
            await query.message.edit(text=await get_playlist_str(), reply_markup=await get_buttons(), disable_web_page_preview=True)

        elif query.data.startswith("ses"):
            me, you = query.data.split("_")  
            if you == "main":
                await query.message.edit_reply_markup(reply_markup=await volume_buttons())
            if you == "add":
                if 190 <= Config.VOLUME <=200:
                    vol=200 
                else:
                    vol=Config.VOLUME+10
                if not (1 <= vol <= 200):
                    return await query.answer("Sadece 1-200 aralığı kabul edildi.")
                await volume(vol)
                Config.VOLUME=vol
                await query.message.edit_reply_markup(reply_markup=await volume_buttons())
            elif you == "less":
                if 1 <= Config.VOLUME <=10:
                    vol=1
                else:
                    vol=Config.VOLUME-10
                if not (1 <= vol <= 200):
                    return await query.answer("Sadece 1-200 aralığı kabul edildi.")
                await volume(vol)
                Config.VOLUME=vol
                await query.message.edit_reply_markup(reply_markup=await volume_buttons())
            elif you == "back":
                await query.message.edit_reply_markup(reply_markup=await get_buttons())


        elif query.data in ["is_loop", "is_video", "admin_only", "edit_title", "set_shuffle", "reply_msg", "set_new_chat", "record", "record_video", "record_dim"]:
            if query.data == "is_loop":
                Config.IS_LOOP = set_config(Config.IS_LOOP)
                await query.message.edit_reply_markup(reply_markup=await settings_panel())
  
            elif query.data == "is_video":
                Config.IS_VIDEO = set_config(Config.IS_VIDEO)
                await query.message.edit_reply_markup(reply_markup=await settings_panel())
                data=Config.DATA.get('FILE_DATA')
                if not data \
                    or data.get('dur', 0) == 0:
                    await restart_playout()
                    return
                k, reply = await seek_file(0)
                if k == False:
                    await restart_playout()

            elif query.data == "admin_only":
                Config.ADMIN_ONLY = set_config(Config.ADMIN_ONLY)
                await query.message.edit_reply_markup(reply_markup=await settings_panel())
        
            elif query.data == "edit_title":
                Config.EDIT_TITLE = set_config(Config.EDIT_TITLE)
                await query.message.edit_reply_markup(reply_markup=await settings_panel())
        
            elif query.data == "set_shuffle":
                Config.SHUFFLE = set_config(Config.SHUFFLE)
                await query.message.edit_reply_markup(reply_markup=await settings_panel())
        
            elif query.data == "reply_msg":
                Config.REPLY_PM = set_config(Config.REPLY_PM)
                await query.message.edit_reply_markup(reply_markup=await settings_panel())
        
            elif query.data == "record_dim":
                if not Config.IS_VIDEO_RECORD:
                    return await query.answer("Bu, ses kayıtları için kullanılamaz")
                Config.PORTRAIT=set_config(Config.PORTRAIT)
                await query.message.edit_reply_markup(reply_markup=(await recorder_settings()))
            elif query.data == 'record_video':
                Config.IS_VIDEO_RECORD=set_config(Config.IS_VIDEO_RECORD)
                await query.message.edit_reply_markup(reply_markup=(await recorder_settings()))

            elif query.data == 'record':
                if Config.IS_RECORDING:
                    k, msg = await stop_recording()
                    if k == False:
                        await query.answer(msg, show_alert=True)
                    else:
                        await query.answer("Kayıt Durduruldu")
                else:
                    k, msg = await start_record_stream()
                    if k == False:
                        await query.answer(msg, show_alert=True)
                    else:
                        await query.answer("Kayıt başladı")
                await query.message.edit_reply_markup(reply_markup=(await recorder_settings()))

            elif query.data == "set_new_chat":
                if query.from_user is None:
                    return await query.answer("Anonim bir yönetici olduğunuz için burada zamanlama yapamazsınız. Özel sohbetten programlayın.", show_alert=True)
                if query.from_user.id in Config.SUDO:
                    await query.answer("Yeni CHAT kurma")
                    chat=query.message.chat.id
                    if Config.IS_RECORDING:
                        await stop_recording()
                    await cancel_all_schedules()
                    await leave_call()
                    Config.CHAT=chat
                    Config.ADMIN_CACHE=False
                    await restart()
                    await query.message.edit("Sohbet Başarıyla Değiştirildi")
                    await sync_to_db()
                else:
                    await query.answer("Bu yalnızca SUDO kullanıcıları tarafından kullanılabilir", show_alert=True)
            if not Config.DATABASE_URI:
                await query.answer("DATABASE bulunamadı, bu değişiklikler geçici olarak kaydedilir ve yeniden başlatıldığında geri alınır. Bunu kalıcı hale getirmek için MongoDb'yi ekleyin.")
        elif query.data.startswith("kapat"):
            if "sudo" in query.data:
                if query.from_user.id in Config.SUDO:
                    await query.message.delete()
                else:
                    await query.answer("Bu yalnızca SUDO kullanıcıları tarafından kullanılabilir", show_alert=True)  
            else:
                if query.message.chat.type != "özel" and query.message.reply_to_message:
                    if query.message.reply_to_message.from_user is None:
                        pass
                    elif query.from_user.id != query.message.reply_to_message.from_user.id:
                        return await query.answer("Okda", show_alert=True)
                elif query.from_user.id in Config.ADMINS:
                    pass
                else:
                    return await query.answer("Okda", show_alert=True)
                await query.answer("Menü kapandı")
                await query.message.delete()
        await query.answer()
