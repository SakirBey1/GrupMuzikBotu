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
from pyrogram.errors import BotInlineDisabled
from pyrogram import Client, filters
from config import Config
from user import group_call
import time
from asyncio import sleep
from pyrogram.raw.base import Update
from pyrogram.raw.functions.channels import GetFullChannel
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pyrogram.raw.types import (
    UpdateGroupCall, 
    GroupCallDiscarded, 
    UpdateGroupCallParticipants
)
from pytgcalls.types.groups import (
        JoinedVoiceChat, 
        LeftVoiceChat
    )
from pytgcalls.types.stream import (
    PausedStream, 
    ResumedStream, 
    MutedStream, 
    UnMutedStream, 
    StreamAudioEnded, 
    StreamVideoEnded
)
from utils import (
    start_record_stream,
    stop_recording, 
    edit_title, 
    stream_from_link, 
    leave_call, 
    start_stream, 
    skip, 
    sync_to_db,
    scheduler
)

async def is_reply(_, client, message):
    if Config.REPLY_PM:
        return True
    else:
        return False
reply_filter=filters.create(is_reply)

DUMBED=[]
async def dumb_it(_, client, message):
    if Config.RECORDING_DUMP and Config.LISTEN:
        return True
    else:
        return False
rec_filter=filters.create(dumb_it)

@Client.on_message(reply_filter & filters.private & ~filters.bot & filters.incoming & ~filters.service & ~filters.me & ~filters.chat([777000, 454000]))
async def reply(client, message): 
    try:
        inline = await client.get_inline_bot_results(Config.BOT_USERNAME, "ETHO_ORUTHAN_PM_VANNU")
        m=await client.send_inline_bot_result(
            message.chat.id,
            query_id=inline.query_id,
            result_id=inline.results[0].id,
            hide_via=True
            )
        old=Config.msg.get(message.chat.id)
        if old:
            await client.delete_messages(message.chat.id, [old["msg"], old["s"]])
        Config.msg[message.chat.id]={"msg":m.updates[1].message.id, "s":message.message_id}
    except BotInlineDisabled:
        LOGGER.error(f"Hata: için Satır İçi Mod @{Config.BOT_USERNAME} etkin değil. PM İzni'ni etkinleştirmek için @Botfather'dan etkinleştirin.")
        await message.reply(f"{Config.REPLY_MESSAGE}\n\n<b>Bu botu grubunuzda kullanamazsınız, bunun için kendi botunuzu oluşturmalısınız. [SOURCE CODE](https://github.com/SakirBey1/GrupMüzikBotu) Aşağıda.</b>", disable_web_page_preview=True)
    except Exception as e:
        LOGGER.error(e, exc_info=True)
        pass


@Client.on_message(filters.private & filters.media & filters.me & rec_filter)
async def dumb_to_log(client, message):
    if message.video and message.video.file_name == "record.mp4":
        await message.copy(int(Config.RECORDING_DUMP))
        DUMBED.append("video")
    if message.audio and message.audio.file_name == "record.ogg":
        await message.copy(int(Config.RECORDING_DUMP))
        DUMBED.append("audio")
    if Config.IS_VIDEO_RECORD:
        if len(DUMBED) == 2:
            DUMBED.clear()
            Config.LISTEN=False
    else:
        if len(DUMBED) == 1:
            DUMBED.clear()
            Config.LISTEN=False

    
@Client.on_message(filters.service & filters.chat(Config.CHAT))
async def service_msg(client, message):
    if message.service == 'voice_chat_started':
        Config.IS_ACTIVE=True
        k=scheduler.get_job(str(Config.CHAT), jobstore=None) #scheduled records
        if k:
            await start_record_stream()
            LOGGER.info("Kayda devam ediliyor...")
        elif Config.WAS_RECORDING:
            LOGGER.info("Önceki kayıt beklenmedik bir şekilde sonlandırıldı, Şimdi kayıtlara devam ediliyor.")
            await start_record_stream()#for unscheduled
        a = await client.send(
                GetFullChannel(
                    channel=(
                        await client.resolve_peer(
                            Config.CHAT
                            )
                        )
                    )
                )
        if a.full_chat.call is not None:
            Config.CURRENT_CALL=a.full_chat.call.id
        LOGGER.info("Sesli sohbet başladı.")
        await sync_to_db()
    elif message.service == 'voice_chat_scheduled':
        LOGGER.info("Sesli Sohbet Planlandı")
        Config.IS_ACTIVE=False
        Config.HAS_SCHEDULE=True
        await sync_to_db()
    elif message.service == 'voice_chat_ended':
        Config.IS_ACTIVE=False
        LOGGER.info("Sesli Sohbet sona erdi")
        Config.CURRENT_CALL=None
        if Config.IS_RECORDING:
            Config.WAS_RECORDING=True
            await stop_recording()
        await sync_to_db()
    else:
        pass

@Client.on_raw_update()
async def handle_raw_updates(client: Client, update: Update, user: dict, chat: dict):
    if isinstance(update, UpdateGroupCallParticipants):
        if not Config.CURRENT_CALL:
            a = await client.send(
                GetFullChannel(
                    channel=(
                        await client.resolve_peer(
                            Config.CHAT
                            )
                        )
                    )
                )
            if a.full_chat.call is not None:
                Config.CURRENT_CALL=a.full_chat.call.id
        if Config.CURRENT_CALL and update.call.id == Config.CURRENT_CALL:
            all=update.participants
            old=list(filter(lambda k:k.peer.user_id if hasattr(k.peer,'user_id') else k.peer.channel_id == Config.USER_ID, all))
            if old:
                for me in old:
                    if me.volume:
                        Config.VOLUME=round(int(me.volume)/100)


    if isinstance(update, UpdateGroupCall) and (update.chat_id == int(-1000000000000-Config.CHAT)):
        if update.call is None:
            Config.IS_ACTIVE = False
            Config.CURRENT_CALL=None
            LOGGER.warning("Etkin Grup Araması Bulunamadı.")
            if Config.IS_RECORDING:
                Config.WAS_RECORDING=True
                await stop_recording()
                LOGGER.warning("Grup araması sonlandırıldı ve bu nedenle kayıt durduruldu.")
            Config.HAS_SCHEDULE = False
            await sync_to_db()
            return

        else:
            call=update.call
            if isinstance(call, GroupCallDiscarded):
                Config.CURRENT_CALL=None
                Config.IS_ACTIVE=False
                if Config.IS_RECORDING:
                    Config.WAS_RECORDING=True
                    await stop_recording()
                LOGGER.warning("Grup Görüşmesi Sonlandırıldı")
                Config.CALL_STATUS = False
                await sync_to_db()
                return
            Config.IS_ACTIVE=True
            Config.CURRENT_CALL=call.id
            if Config.IS_RECORDING and not call.record_video_active:
                Config.LISTEN=True
                await stop_recording()
                LOGGER.warning("Kayıt kullanıcı tarafından sonlandırıldı, dolayısıyla programlar durduruldu.")
                return
            if call.schedule_date:
                Config.HAS_SCHEDULE=True
            else:
                Config.HAS_SCHEDULE=False
        await sync_to_db()
 
@group_call.on_raw_update()
async def handler(client: PyTgCalls, update: Update):
    if isinstance(update, JoinedVoiceChat):
        Config.CALL_STATUS = True
        if Config.EDIT_TITLE:
            await edit_title()
        who=await group_call.get_participants(Config.CHAT)
        you=list(filter(lambda k:k.user_id == Config.USER_ID, who))
        if you:
            for me in you:
                if me.volume:
                    Config.VOLUME=round(int(me.volume))
    elif isinstance(update, LeftVoiceChat):
        Config.CALL_STATUS = False
    elif isinstance(update, PausedStream):
        Config.DUR['PAUSE'] = time.time()
        Config.PAUSE=True
    elif isinstance(update, ResumedStream):
        pause=Config.DUR.get('PAUSE')
        if pause:
            diff = time.time() - pause
            start=Config.DUR.get('TIME')
            if start:
                Config.DUR['TIME']=start+diff
        Config.PAUSE=False
    elif isinstance(update, MutedStream):
        Config.MUTED = True
    elif isinstance(update, UnMutedStream):
        Config.MUTED = False



@group_call.on_stream_end()
async def handler(client: PyTgCalls, update: Update):
    if isinstance(update, StreamAudioEnded) or isinstance(update, StreamVideoEnded):
        if not Config.STREAM_END.get("DURUM"):
            Config.STREAM_END["DURUM"]=str(update)
            if Config.STREAM_LINK and len(Config.playlist) == 0:
                if Config.IS_LOOP:
                    await stream_from_link(Config.STREAM_LINK)
                else:
                    await leave_call()
            elif not Config.playlist:
                if Config.IS_LOOP:
                    await start_stream()
                else:
                    await leave_call()
            else:
                await skip()          
            await sleep(15) #wait for max 15 sec
            try:
                del Config.STREAM_END["DURUM"]
            except:
                pass
        else:
            try:
                del Config.STREAM_END["DURUM"]
            except:
                pass

       

