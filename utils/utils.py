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
try:
    from pyrogram.raw.types import InputChannel
    from apscheduler.schedulers.asyncio import AsyncIOScheduler   
    from apscheduler.jobstores.mongodb import MongoDBJobStore
    from apscheduler.jobstores.base import ConflictingIdError
    from pyrogram.raw.functions.channels import GetFullChannel
    from pytgcalls import StreamType
    import yt_dlp
    from pyrogram import filters
    from pymongo import MongoClient
    from datetime import datetime
    from threading import Thread
    from math import gcd
    from .pyro_dl import Downloader
    from config import Config
    from asyncio import sleep  
    from bot import bot
    from PTN import parse
    import subprocess
    import asyncio
    import json
    import random
    import time
    import sys
    import os
    import math
    from pyrogram.errors.exceptions.bad_request_400 import (
        BadRequest, 
        ScheduleDateInvalid,
        PeerIdInvalid,
        ChannelInvalid
    )
    from pytgcalls.types.input_stream import (
        AudioVideoPiped, 
        AudioPiped,
        AudioImagePiped
    )
    from pytgcalls.types.input_stream import (
        AudioParameters,
        VideoParameters
    )
    from pyrogram.types import (
        InlineKeyboardButton, 
        InlineKeyboardMarkup, 
        Message
    )
    from pyrogram.raw.functions.phone import (
        EditGroupCallTitle, 
        CreateGroupCall,
        ToggleGroupCallRecord,
        StartScheduledGroupCall 
    )
    from pytgcalls.exceptions import (
        GroupCallNotFound, 
        NoActiveGroupCall,
        InvalidVideoProportion
    )
    from PIL import (
        Image, 
        ImageFont, 
        ImageDraw 
    )

    from user import (
        group_call, 
        USER
    )
except ModuleNotFoundError:
    import os
    import sys
    import subprocess
    file=os.path.abspath("requirements.txt")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', file, '--upgrade'])
    os.execl(sys.executable, sys.executable, *sys.argv)

if Config.DATABASE_URI:
    from .database import db
    monclient = MongoClient(Config.DATABASE_URI)
    jobstores = {
        'default': MongoDBJobStore(client=monclient, database=Config.DATABASE_NAME, collection='scheduler')
        }
    scheduler = AsyncIOScheduler(jobstores=jobstores)
else:
    scheduler = AsyncIOScheduler()
scheduler.start()
dl=Downloader()

async def play():
    song=Config.playlist[0]    
    if song[3] == "telegram":
        file=Config.GET_FILE.get(song[5])
        if not file:
            file = await dl.pyro_dl(song[2])
            if not file:
                LOGGER.info("Telegramdan dosya indirme")
                file = await bot.download_media(song[2])
            Config.GET_FILE[song[5]] = file
            await sleep(3)
        while not os.path.exists(file):
            file=Config.GET_FILE.get(song[5])
            await sleep(1)
        total=int(((song[5].split("_"))[1])) * 0.005
        while not (os.stat(file).st_size) >= total:
            LOGGER.info("İndirme bekleniyor")
            LOGGER.info(str((os.stat(file).st_size)))
            await sleep(1)
    elif song[3] == "url":
        file=song[2]
    else:
        file=await get_link(song[2])
    if not file:
        if Config.playlist or Config.STREAM_LINK:
            return await skip()     
        else:
            LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
            await leave_call()
            return False 
    link, seek, pic, width, height = await chek_the_media(file, title=f"{song[1]}")
    if not link:
        LOGGER.warning("Desteklenmeyen bağlantı, Kuyruktan atlanıyor.")
        return
    await sleep(1)
    if Config.STREAM_LINK:
        Config.STREAM_LINK=False
    LOGGER.info(f"OYNAMAYA BAŞLAMA: {song[1]}")
    await join_call(link, seek, pic, width, height)

async def schedule_a_play(job_id, date):
    try:
        scheduler.add_job(run_schedule, "date", [job_id], id=job_id, run_date=date, max_instances=50, misfire_grace_time=None)
    except ConflictingIdError:
        LOGGER.warning("Bu zaten planlanmış")
        return
    if not Config.CALL_STATUS or not Config.IS_ACTIVE:
        if Config.SCHEDULE_LIST[0]['job_id'] == job_id \
            and (date - datetime.now()).total_seconds() < 86400:
            song=Config.SCHEDULED_STREAM.get(job_id)
            if Config.IS_RECORDING:
                scheduler.add_job(start_record_stream, "date", id=str(Config.CHAT), run_date=date, max_instances=50, misfire_grace_time=None)
            try:
                await USER.send(CreateGroupCall(
                    peer=(await USER.resolve_peer(Config.CHAT)),
                    random_id=random.randint(10000, 999999999),
                    schedule_date=int(date.timestamp()),
                    title=song['1']
                    )
                )
                Config.HAS_SCHEDULE=True
            except ScheduleDateInvalid:
                LOGGER.error("Tarih geçersiz olduğundan VideoChat planlanamıyor")
            except Exception as e:
                LOGGER.error(f"Sesli sohbet planlanırken hata- {e}", exc_info=True)
    await sync_to_db()

async def run_schedule(job_id):
    data=Config.SCHEDULED_STREAM.get(job_id)
    if not data:
        LOGGER.error("Veriler eksik olduğundan Planlanmış akış oynatılmadı")
        old=filter(lambda k: k['job_id'] == job_id, Config.SCHEDULE_LIST)
        if old:
            Config.SCHEDULE_LIST.remove(old)
        await sync_to_db()
        pass
    else:
        if Config.HAS_SCHEDULE:
            if not await start_scheduled():
                LOGGER.error("Planlanan akış atlandı, Neden - Sesli sohbet başlatılamıyor.")
                return
        data_ = [{1:data['1'], 2:data['2'], 3:data['3'], 4:data['4'], 5:data['5']}]
        Config.playlist = data_ + Config.playlist
        await play()
        LOGGER.info("Planlanmış Akışı Başlatma")
        del Config.SCHEDULED_STREAM[job_id]
        old=list(filter(lambda k: k['job_id'] == job_id, Config.SCHEDULE_LIST))
        if old:
            for old_ in old:
                Config.SCHEDULE_LIST.remove(old_)
        if not Config.SCHEDULE_LIST:
            Config.SCHEDULED_STREAM = {} #clear the unscheduled streams
        await sync_to_db()
        if len(Config.playlist) <= 1:
            return
        await download(Config.playlist[1])
      
async def cancel_all_schedules():
    for sch in Config.SCHEDULE_LIST:
        job=sch['job_id']
        k=scheduler.get_job(job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)
        if Config.SCHEDULED_STREAM.get(job):
            del Config.SCHEDULED_STREAM[job]      
    Config.SCHEDULE_LIST.clear()
    await sync_to_db()
    LOGGER.info("Tüm programlar kaldırıldı")

async def skip():
    if Config.STREAM_LINK and len(Config.playlist) == 0 and Config.IS_LOOP:
        await stream_from_link()
        return
    elif not Config.playlist \
        and Config.IS_LOOP:
        LOGGER.info("Döngü Oynatma etkinleştirildi, oynatma listesi boş olduğundan STARTUP_STREAM'e geçiliyor.")
        await start_stream()
        return
    elif not Config.playlist \
        and not Config.IS_LOOP:
        LOGGER.info("Loop Play devre dışı, çalma listesi boş olduğu için aramadan çıkıyor.")
        await leave_call()
        return
    old_track = Config.playlist.pop(0)
    await clear_db_playlist(song=old_track)
    if old_track[3] == "telegram":
        file=Config.GET_FILE.get(old_track[5])
        if file:
            try:
                os.remove(file)
            except:
                pass
            del Config.GET_FILE[old_track[5]]
    if not Config.playlist \
        and Config.IS_LOOP:
        LOGGER.info("Döngü Oynatma etkinleştirildi, oynatma listesi boş olduğundan STARTUP_STREAM'e geçiliyor.")
        await start_stream()
        return
    elif not Config.playlist \
        and not Config.IS_LOOP:
        LOGGER.info("Loop Play devre dışı, çalma listesi boş olduğu için aramadan çıkıyor.")
        await leave_call()
        return
    LOGGER.info(f"OYUNA BAŞLA: {Config.playlist[0][1]}")
    if Config.DUR.get('DURAKLAT'):
        del Config.DUR['DURAKLAT']
    await play()
    if len(Config.playlist) <= 1:
        return
    #await download(Config.playlist[1])


async def check_vc():
    a = await bot.send(GetFullChannel(channel=(await bot.resolve_peer(Config.CHAT))))
    if a.full_chat.call is None:
        try:
            LOGGER.info("Etkin arama bulunamadı, yeni oluşturuluyor")
            await USER.send(CreateGroupCall(
                peer=(await USER.resolve_peer(Config.CHAT)),
                random_id=random.randint(10000, 999999999)
                )
                )
            if Config.WAS_RECORDING:
                await start_record_stream()
            await sleep(2)
            return True
        except Exception as e:
            LOGGER.error(f"Yeni GroupCall başlatılamıyor :- {e}", exc_info=True)
            return False
    else:
        if Config.HAS_SCHEDULE:
            await start_scheduled()
        return True
    

async def join_call(link, seek, pic, width, height):  
    if not await check_vc():
        LOGGER.error("Sesli arama bulunamadı ve yeni bir arama oluşturulamadı. Çıkılıyor...")
        return
    if Config.HAS_SCHEDULE:
        await start_scheduled()
    if Config.CALL_STATUS:
        if Config.IS_ACTIVE == False:
            Config.CALL_STATUS = False
            return await join_call(link, seek, pic, width, height)
        play=await change_file(link, seek, pic, width, height)
    else:
        play=await join_and_play(link, seek, pic, width, height)
    if play == False:
        await sleep(1)
        await join_call(link, seek, pic, width, height)
    await sleep(1)
    if not seek:
        Config.DUR["ZAMAN"]=time.time()
        if Config.EDIT_TITLE:
            await edit_title()
    old=Config.GET_FILE.get("eskimiş")
    if old:
        for file in old:
            os.remove(f"./downloads/{file}")
        try:
            del Config.GET_FILE["eskimiş"]
        except:
            LOGGER.error("dict'den silme hatası")
            pass
    await send_playlist()

async def start_scheduled():
    try:
        await USER.send(
            StartScheduledGroupCall(
                call=(
                    await USER.send(
                        GetFullChannel(
                            channel=(
                                await USER.resolve_peer(
                                    Config.CHAT
                                    )
                                )
                            )
                        )
                    ).full_chat.call
                )
            )
        if Config.WAS_RECORDING:
            await start_record_stream()
        return True
    except Exception as e:
        if 'GROUPCALL_ALREADY_STARTED' in str(e):
            LOGGER.warning("Zaten Grup Çağrısı Var")
            return True
        else:
            Config.HAS_SCHEDULE=False
            return await check_vc()

async def join_and_play(link, seek, pic, width, height):
    try:
        if seek:
            start=str(seek['Başlat'])
            end=str(seek['end'])
            if not Config.IS_VIDEO:
                await group_call.join_group_call(
                    int(Config.CHAT),
                    AudioPiped(
                        link,
                        audio_parameters=AudioParameters(
                            Config.BITRATE
                            ),
                        additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                        ),
                    stream_type=StreamType().pulse_stream,
                )
            else:
                if pic:
                    cwidth, cheight = resize_ratio(1280, 720, Config.CUSTOM_QUALITY)
                    await group_call.join_group_call(
                        int(Config.CHAT),
                        AudioImagePiped(
                            link,
                            pic,
                            video_parameters=VideoParameters(
                                cwidth,
                                cheight,
                                Config.FPS,
                            ),
                            audio_parameters=AudioParameters(
                                Config.BITRATE,
                            ),
                            additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',                        ),
                        stream_type=StreamType().pulse_stream,
                    )
                else:
                    if not width \
                        or not height:
                        LOGGER.error("Geçerli Video Bulunamadı ve bu nedenle oynatma listesinden kaldırıldı.")
                        if Config.playlist or Config.STREAM_LINK:
                            return await skip()     
                        else:
                            LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
                            return 
                    cwidth, cheight = resize_ratio(width, height, Config.CUSTOM_QUALITY)
                    await group_call.join_group_call(
                        int(Config.CHAT),
                        AudioVideoPiped(
                            link,
                            video_parameters=VideoParameters(
                                cwidth,
                                cheight,
                                Config.FPS,
                            ),
                            audio_parameters=AudioParameters(
                                Config.BITRATE
                            ),
                            additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                            ),
                        stream_type=StreamType().pulse_stream,
                    )
        else:
            if not Config.IS_VIDEO:
                await group_call.join_group_call(
                    int(Config.CHAT),
                    AudioPiped(
                        link,
                        audio_parameters=AudioParameters(
                            Config.BITRATE
                            ),
                        ),
                    stream_type=StreamType().pulse_stream,
                )
            else:
                if pic:
                    cwidth, cheight = resize_ratio(1280, 720, Config.CUSTOM_QUALITY)
                    await group_call.join_group_call(
                        int(Config.CHAT),
                        AudioImagePiped(
                            link,
                            pic,
                            video_parameters=VideoParameters(
                                cwidth,
                                cheight,
                                Config.FPS,
                            ),
                            audio_parameters=AudioParameters(
                                Config.BITRATE,
                            ),      
                            ),
                        stream_type=StreamType().pulse_stream,
                    )
                else:
                    if not width \
                        or not height:
                        LOGGER.error("Geçerli Video Bulunamadı ve bu nedenle oynatma listesinden kaldırıldı.")
                        if Config.playlist or Config.STREAM_LINK:
                            return await skip()     
                        else:
                            LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
                            return 
                    cwidth, cheight = resize_ratio(width, height, Config.CUSTOM_QUALITY)
                    await group_call.join_group_call(
                        int(Config.CHAT),
                        AudioVideoPiped(
                            link,
                            video_parameters=VideoParameters(
                                cwidth,
                                cheight,
                                Config.FPS,
                            ),
                            audio_parameters=AudioParameters(
                                Config.BITRATE
                            ),
                        ),
                        stream_type=StreamType().pulse_stream,
                    )
        Config.CALL_STATUS=True
        return True
    except NoActiveGroupCall:
        try:
            LOGGER.info("Etkin arama bulunamadı, yeni oluşturuluyor")
            await USER.send(CreateGroupCall(
                peer=(await USER.resolve_peer(Config.CHAT)),
                random_id=random.randint(10000, 999999999)
                )
                )
            if Config.WAS_RECORDING:
                await start_record_stream()
            await sleep(2)
            await restart_playout()
        except Exception as e:
            LOGGER.error(f"Yeni GroupCall başlatılamıyor :- {e}", exc_info=True)
            pass
    except InvalidVideoProportion:
        LOGGER.error("Bu video desteklenmiyor")
        if Config.playlist or Config.STREAM_LINK:
            return await skip()     
        else:
            LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
            return 
    except Exception as e:
        LOGGER.error(f"Hatalar Katılırken, yeniden denenirken Hata- {e}", exc_info=True)
        return False


async def change_file(link, seek, pic, width, height):
    try:
        if seek:
            start=str(seek['Başlat'])
            end=str(seek['son'])
            if not Config.IS_VIDEO:
                await group_call.change_stream(
                    int(Config.CHAT),
                    AudioPiped(
                        link,
                        audio_parameters=AudioParameters(
                            Config.BITRATE
                            ),
                        additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                        ),
                )
            else:
                if pic:
                    cwidth, cheight = resize_ratio(1280, 720, Config.CUSTOM_QUALITY)
                    await group_call.change_stream(
                        int(Config.CHAT),
                        AudioImagePiped(
                            link,
                            pic,
                            video_parameters=VideoParameters(
                                cwidth,
                                cheight,
                                Config.FPS,
                            ),
                            audio_parameters=AudioParameters(
                                Config.BITRATE,
                            ),
                            additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',                        ),
                    )
                else:
                    if not width \
                        or not height:
                        LOGGER.error("Geçerli Video Bulunamadı ve bu nedenle oynatma listesinden kaldırıldı.")
                        if Config.playlist or Config.STREAM_LINK:
                            return await skip()     
                        else:
                            LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
                            return 

                    cwidth, cheight = resize_ratio(width, height, Config.CUSTOM_QUALITY)
                    await group_call.change_stream(
                        int(Config.CHAT),
                        AudioVideoPiped(
                            link,
                            video_parameters=VideoParameters(
                                cwidth,
                                cheight,
                                Config.FPS,
                            ),
                            audio_parameters=AudioParameters(
                                Config.BITRATE
                            ),
                            additional_ffmpeg_parameters=f'-ss {start} -atend -t {end}',
                        ),
                        )
        else:
            if not Config.IS_VIDEO:
                await group_call.change_stream(
                    int(Config.CHAT),
                    AudioPiped(
                        link,
                        audio_parameters=AudioParameters(
                            Config.BITRATE
                            ),
                        ),
                )
            else:
                if pic:
                    cwidth, cheight = resize_ratio(1280, 720, Config.CUSTOM_QUALITY)
                    await group_call.change_stream(
                        int(Config.CHAT),
                        AudioImagePiped(
                            link,
                            pic,
                            video_parameters=VideoParameters(
                                cwidth,
                                cheight,
                                Config.FPS,
                            ),
                            audio_parameters=AudioParameters(
                                Config.BITRATE,
                            ),
                        ),
                    )
                else:
                    if not width \
                        or not height:
                        LOGGER.error("Geçerli Video Bulunamadı ve bu nedenle oynatma listesinden kaldırıldı.")
                        if Config.playlist or Config.STREAM_LINK:
                            return await skip()     
                        else:
                            LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
                            return 
                    cwidth, cheight = resize_ratio(width, height, Config.CUSTOM_QUALITY)
                    await group_call.change_stream(
                        int(Config.CHAT),
                        AudioVideoPiped(
                            link,
                            video_parameters=VideoParameters(
                                cwidth,
                                cheight,
                                Config.FPS,
                            ),
                            audio_parameters=AudioParameters(
                                Config.BITRATE,
                            ),
                        ),
                        )
    except InvalidVideoProportion:
        LOGGER.error("Geçersiz video, atlandı")
        if Config.playlist or Config.STREAM_LINK:
            return await skip()     
        else:
            LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
            await leave_call()
            return 
    except Exception as e:
        LOGGER.error(f"Çağrıya katılma hatası - {e}", exc_info=True)
        return False


async def seek_file(seektime):
    play_start=int(float(Config.DUR.get('TIME')))
    if not play_start:
        return False, "Oyuncu henüz başlamadı"
    else:
        data=Config.DATA.get("FILE_DATA")
        if not data:
            return False, "Aramak için Akış yok"        
        played=int(float(time.time())) - int(float(play_start))
        if data.get("dur", 0) == 0:
            return False, "Görünen o ki, aranamayan canlı yayın oynatılıyor."
        total=int(float(data.get("dur", 0)))
        trimend = total - played - int(seektime)
        trimstart = played + int(seektime)
        if trimstart > total:
            return False, "Aranan süre, dosyanın maksimum süresini aşıyor"
        new_play_start=int(play_start) - int(seektime)
        Config.DUR['TIME']=new_play_start
        link, seek, pic, width, height = await chek_the_media(data.get("dosya"), seek={"başla":trimstart, "son":trimend})
        await join_call(link, seek, pic, width, height)
        return True, None
    


async def leave_call():
    try:
        await group_call.leave_group_call(Config.CHAT)
    except Exception as e:
        LOGGER.error(f"Çağrıdan çıkarken hatalar {e}", exc_info=True)
    #Config.playlist.clear()
    if Config.STREAM_LINK:
        Config.STREAM_LINK=False
    Config.CALL_STATUS=False
    if Config.SCHEDULE_LIST:
        sch=Config.SCHEDULE_LIST[0]
        if (sch['date'] - datetime.now()).total_seconds() < 86400:
            song=Config.SCHEDULED_STREAM.get(sch['job_id'])
            if Config.IS_RECORDING:
                k=scheduler.get_job(str(Config.CHAT), jobstore=None)
                if k:
                    scheduler.remove_job(str(Config.CHAT), jobstore=None)
                scheduler.add_job(start_record_stream, "date", id=str(Config.CHAT), run_date=sch['date'], max_instances=50, misfire_grace_time=None)
            try:
                await USER.send(CreateGroupCall(
                    peer=(await USER.resolve_peer(Config.CHAT)),
                    random_id=random.randint(10000, 999999999),
                    schedule_date=int((sch['date']).timestamp()),
                    title=song['1']
                    )
                )
                Config.HAS_SCHEDULE=True
            except ScheduleDateInvalid:
                LOGGER.error("Tarih geçersiz olduğundan VideoChat planlanamıyor")
            except Exception as e:
                LOGGER.error(f"Sesli sohbet planlanırken hata- {e}", exc_info=True)
    await sync_to_db()
            
                


async def restart():
    try:
        await group_call.leave_group_call(Config.CHAT)
        await sleep(2)
    except Exception as e:
        LOGGER.error(e, exc_info=True)
    if not Config.playlist:
        await start_stream()
        return
    LOGGER.info(f"- OYUNA BAŞLA: {Config.playlist[0][1]}")
    await sleep(1)
    await play()
    LOGGER.info("Playout'u Yeniden Başlatma")
    if len(Config.playlist) <= 1:
        return
    await download(Config.playlist[1])


async def restart_playout():
    if not Config.playlist:
        await start_stream()
        return
    LOGGER.info(f"OYNAMAYI YENİDEN BAŞLAT: {Config.playlist[0][1]}")
    data=Config.DATA.get('FILE_DATA')
    if data:
        link, seek, pic, width, height = await chek_the_media(data['file'], title=f"{Config.playlist[0][1]}")
        if not link:
            LOGGER.warning("Desteklenmeyen Bağlantı")
            return
        await sleep(1)
        if Config.STREAM_LINK:
            Config.STREAM_LINK=False
        await join_call(link, seek, pic, width, height)
    else:
        await play()
    if len(Config.playlist) <= 1:
        return
    await download(Config.playlist[1])


def is_ytdl_supported(input_url: str) -> bool:
    shei = yt_dlp.extractor.gen_extractors()
    return any(int_extraactor.suitable(input_url) and int_extraactor.IE_NAME != "Genel" for int_extraactor in shei)


async def set_up_startup():
    Config.YSTREAM=False
    Config.YPLAY=False
    Config.CPLAY=False
    #regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
    # match = re.match(regex, Config.STREAM_URL)
    if Config.STREAM_URL.startswith("@") or (str(Config.STREAM_URL)).startswith("-100"):
        Config.CPLAY = True
        LOGGER.info(f"Channel Play enabled from {Config.STREAM_URL}")
        Config.STREAM_SETUP=True
        return
    elif Config.STREAM_URL.startswith("https://t.me/DumpPlaylist"):
        Config.YPLAY=True
        LOGGER.info("YouTube Oynatma Listesi, STARTUP STREAM olarak ayarlandı")
        Config.STREAM_SETUP=True
        return
    match = is_ytdl_supported(Config.STREAM_URL)
    if match:
        Config.YSTREAM=True
        LOGGER.info("YouTube Akışı, BAŞLANGIÇ YAYINI olarak ayarlandı")
    else:
        LOGGER.info("Doğrudan bağlantı STARTUP_STREAM olarak ayarlandı")
        pass
    Config.STREAM_SETUP=True
    
    

async def start_stream(): 
    if not Config.STREAM_SETUP:
        await set_up_startup()
    if Config.YPLAY:
        try:
            msg_id=Config.STREAM_URL.split("/", 4)[4]
        except:
            LOGGER.error("Youtube oynatma listesi getirilemiyor. Başlangıç ​​akışınızı tekrar kontrol edin.")
            pass
        await y_play(int(msg_id))
        return
    elif Config.CPLAY:
        await c_play(Config.STREAM_URL)
        return
    elif Config.YSTREAM:
        link=await get_link(Config.STREAM_URL)
    else:
        link=Config.STREAM_URL
    link, seek, pic, width, height = await chek_the_media(link, title="Başlangıç Akışı")
    if not link:
        LOGGER.warning("Desteklenmeyen bağlantı")
        return False
    if Config.IS_VIDEO:
        if not ((width and height) or pic):
            LOGGER.error("Akış Bağlantısı geçersiz")
            return 
    #if Config.playlist:
        #Config.playlist.clear()
    await join_call(link, seek, pic, width, height)


async def stream_from_link(link):
    link, seek, pic, width, height = await chek_the_media(link)
    if not link:
        LOGGER.error("Verilen url'den yeterli bilgi alınamıyor")
        return False, "Verilen url'den yeterli bilgi alınamıyor"
    #if Config.playlist:
        #Config.playlist.clear()
    Config.STREAM_LINK=link
    await join_call(link, seek, pic, width, height)
    return True, None


async def get_link(file):
    ytdl_cmd = [ "yt-dlp", "--geo-bypass", "-g", "-f", "best[height<=?720][width<=?1280]/best", file]
    process = await asyncio.create_subprocess_exec(
        *ytdl_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    output, err = await process.communicate()
    if not output:
        LOGGER.error(str(err.decode()))
        if Config.playlist or Config.STREAM_LINK:
            return await skip()
        else:
            LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
            await leave_call()
            return False
    stream = output.decode().strip()
    link = (stream.split("\n"))[-1]
    if link:
        return link
    else:
        LOGGER.error("Bağlantıdan yeterli bilgi alınamıyor")
        if Config.playlist or Config.STREAM_LINK:
            return await skip()
        else:
            LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
            await leave_call()
            return False


async def download(song, msg=None):
    if song[3] == "telegram":
        if not Config.GET_FILE.get(song[5]):
            try: 
                original_file = await dl.pyro_dl(song[2])
                Config.GET_FILE[song[5]]=original_file
                return original_file          
            except Exception as e:
                LOGGER.error(e, exc_info=True)
                Config.playlist.remove(song)
                await clear_db_playlist(song=song)
                if len(Config.playlist) <= 1:
                    return
                await download(Config.playlist[1])
   


async def chek_the_media(link, seek=False, pic=False, title="Müzik"):
    if not Config.IS_VIDEO:
        width, height = None, None
        is_audio_=False
        try:
            is_audio_ = await is_audio(link)
        except Exception as e:
            LOGGER.error(e, exc_info=True)
            is_audio_ = False
            LOGGER.error("Ses özellikleri zaman içinde alınamıyor.")
        if not is_audio_:
            LOGGER.error("Ses Kaynağı bulunamadı")
            Config.STREAM_LINK=False
            if Config.playlist or Config.STREAM_LINK:
                await skip()     
                return None, None, None, None, None
            else:
                LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
                return None, None, None, None, None
            
    else:
        if os.path.isfile(link) \
            and "audio" in Config.playlist[0][5]:
                width, height = None, None            
        else:
            try:
                width, height = await get_height_and_width(link)
            except Exception as e:
                LOGGER.error(e, exc_info=True)
                width, height = None, None
                LOGGER.error("Zaman içinde video özellikleri alınamıyor.")
        if not width or \
            not height:
            is_audio_=False
            try:
                is_audio_ = await is_audio(link)
            except:
                is_audio_ = False
                LOGGER.error("Ses özellikleri zaman içinde alınamıyor.")
            if is_audio_:
                pic_=await bot.get_messages("DumpOynatma Listesi", 30)
                photo = "./pic/photo"
                if not os.path.exists(photo):
                    photo = await pic_.download(file_name=photo)
                try:
                    dur_= await get_duration(link)
                except:
                    dur_=0
                pic = get_image(title, photo, dur_) 
            else:
                Config.STREAM_LINK=False
                if Config.playlist or Config.STREAM_LINK:
                    await skip()     
                    return None, None, None, None, None
                else:
                    LOGGER.error("Bu akış desteklenmiyor, VC'den çıkıyor.")
                    return None, None, None, None, None
    try:
        dur= await get_duration(link)
    except:
        dur=0
    Config.DATA['FILE_DATA']={"dosya":link, 'dur':dur}
    return link, seek, pic, width, height


async def edit_title():
    if Config.STREAM_LINK:
        title="Canlı yayın"
    elif Config.playlist:
        title = Config.playlist[0][1]   
    else:       
        title = "Canlı yayın"
    try:
        chat = await USER.resolve_peer(Config.CHAT)
        full_chat=await USER.send(
            GetFullChannel(
                channel=InputChannel(
                    channel_id=chat.channel_id,
                    access_hash=chat.access_hash,
                    ),
                ),
            )
        edit = EditGroupCallTitle(call=full_chat.full_chat.call, title=title)
        await USER.send(edit)
    except Exception as e:
        LOGGER.error(f"Başlık düzenlenirken oluşan hatalar - {e}", exc_info=True)
        pass

async def stop_recording():
    job=str(Config.CHAT)
    a = await bot.send(GetFullChannel(channel=(await bot.resolve_peer(Config.CHAT))))
    if a.full_chat.call is None:
        k=scheduler.get_job(job_id=job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)
        Config.IS_RECORDING=False
        await sync_to_db()
        return False, "Grup Araması Bulunamadı"
    try:
        await USER.send(
            ToggleGroupCallRecord(
                call=(
                    await USER.send(
                        GetFullChannel(
                            channel=(
                                await USER.resolve_peer(
                                    Config.CHAT
                                    )
                                )
                            )
                        )
                    ).full_chat.call,
                start=False,                 
                )
            )
        Config.IS_RECORDING=False
        Config.LISTEN=True
        await sync_to_db()
        k=scheduler.get_job(job_id=job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)
        return True, "Kaydı Başarıyla Durdurdu"
    except Exception as e:
        if 'GROUPCALL_NOT_MODIFIED' in str(e):
            LOGGER.warning("Zaten kayıt yok")
            Config.IS_RECORDING=False
            await sync_to_db()
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)
            return False, "Kayıt başlatılmadı"
        else:
            LOGGER.error(str(e))
            Config.IS_RECORDING=False
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)
            await sync_to_db()
            return False, str(e)
    



async def start_record_stream():
    if Config.IS_RECORDING:
        await stop_recording()
    if Config.WAS_RECORDING:
        Config.WAS_RECORDING=False
    a = await bot.send(GetFullChannel(channel=(await bot.resolve_peer(Config.CHAT))))
    job=str(Config.CHAT)
    if a.full_chat.call is None:
        k=scheduler.get_job(job_id=job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)      
        return False, "Grup Araması Bulunamadı"
    try:
        if not Config.PORTRAIT:
            pt = False
        else:
            pt = True
        if not Config.RECORDING_TITLE:
            tt = None
        else:
            tt = Config.RECORDING_TITLE
        if Config.IS_VIDEO_RECORD:
            await USER.send(
                ToggleGroupCallRecord(
                    call=(
                        await USER.send(
                            GetFullChannel(
                                channel=(
                                    await USER.resolve_peer(
                                        Config.CHAT
                                        )
                                    )
                                )
                            )
                        ).full_chat.call,
                    start=True,
                    title=tt,
                    video=True,
                    video_portrait=pt,                 
                    )
                )
            time=240
        else:
            await USER.send(
                ToggleGroupCallRecord(
                    call=(
                        await USER.send(
                            GetFullChannel(
                                channel=(
                                    await USER.resolve_peer(
                                        Config.CHAT
                                        )
                                    )
                                )
                            )
                        ).full_chat.call,
                    start=True,
                    title=tt,                
                    )
                )
            time=86400
        Config.IS_RECORDING=True
        k=scheduler.get_job(job_id=job, jobstore=None)
        if k:
            scheduler.remove_job(job, jobstore=None)   
        try:
            scheduler.add_job(renew_recording, "Aralık", id=job, minutes=time, max_instances=50, misfire_grace_time=None)
        except ConflictingIdError:
            scheduler.remove_job(job, jobstore=None)
            scheduler.add_job(renew_recording, "Aralık", id=job, minutes=time, max_instances=50, misfire_grace_time=None)
            LOGGER.warning("Bu zaten planlanmış, yeniden planlanıyor")
        await sync_to_db()
        LOGGER.info("Kayıt Başladı")
        return True, "Kayda Başarıyla Başladı"
    except Exception as e:
        if 'GROUPCALL_NOT_MODIFIED' in str(e):
            LOGGER.warning("Zaten Kaydediliyor.., durdurma ve yeniden başlatma")
            Config.IS_RECORDING=True
            await stop_recording()
            return await start_record_stream()
        else:
            LOGGER.error(str(e))
            Config.IS_RECORDING=False
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)
            await sync_to_db()
            return False, str(e)

async def renew_recording():
    try:
        job=str(Config.CHAT)
        a = await bot.send(GetFullChannel(channel=(await bot.resolve_peer(Config.CHAT))))
        if a.full_chat.call is None:
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)      
            LOGGER.info("Grup araması boş, durdurulmuş zamanlayıcı")
            return
    except ConnectionError:
        pass
    try:
        if not Config.PORTRAIT:
            pt = False
        else:
            pt = True
        if not Config.RECORDING_TITLE:
            tt = None
        else:
            tt = Config.RECORDING_TITLE
        if Config.IS_VIDEO_RECORD:
            await USER.send(
                ToggleGroupCallRecord(
                    call=(
                        await USER.send(
                            GetFullChannel(
                                channel=(
                                    await USER.resolve_peer(
                                        Config.CHAT
                                        )
                                    )
                                )
                            )
                        ).full_chat.call,
                    start=True,
                    title=tt,
                    video=True,
                    video_portrait=pt,                 
                    )
                )
        else:
            await USER.send(
                ToggleGroupCallRecord(
                    call=(
                        await USER.send(
                            GetFullChannel(
                                channel=(
                                    await USER.resolve_peer(
                                        Config.CHAT
                                        )
                                    )
                                )
                            )
                        ).full_chat.call,
                    start=True,
                    title=tt,                
                    )
                )
        Config.IS_RECORDING=True
        await sync_to_db()
        return True, "Kayda Başarıyla Başladı"
    except Exception as e:
        if 'GROUPCALL_NOT_MODIFIED' in str(e):
            LOGGER.warning("Zaten Kaydediliyor.., durdurma ve yeniden başlatma")
            Config.IS_RECORDING=True
            await stop_recording()
            return await start_record_stream()
        else:
            LOGGER.error(str(e))
            Config.IS_RECORDING=False
            k=scheduler.get_job(job_id=job, jobstore=None)
            if k:
                scheduler.remove_job(job, jobstore=None)
            await sync_to_db()
            return False, str(e)

async def send_playlist():
    if Config.LOG_GROUP:
        pl = await get_playlist_str()
        if Config.msg.get('player') is not None:
            await Config.msg['player'].delete()
        Config.msg['player'] = await send_text(pl)


async def send_text(text):
    message = await bot.send_message(
        int(Config.LOG_GROUP),
        text,
        reply_markup=await get_buttons(),
        disable_web_page_preview=True,
        disable_notification=True
    )
    return message


async def shuffle_playlist():
    v = []
    p = [v.append(Config.playlist[c]) for c in range(2,len(Config.playlist))]
    random.shuffle(v)
    for c in range(2,len(Config.playlist)):
        Config.playlist.remove(Config.playlist[c]) 
        Config.playlist.insert(c,v[c-2])


async def import_play_list(file):
    file=open(file)
    try:
        f=json.loads(file.read(), object_hook=lambda d: {int(k): v for k, v in d.items()})
        for playf in f:
            Config.playlist.append(playf)
            await add_to_db_playlist(playf)
            if len(Config.playlist) >= 1 \
                and not Config.CALL_STATUS:
                LOGGER.info("Bağlantı ayıklanıyor ve İşleniyor...")
                await download(Config.playlist[0])
                await play()   
            elif (len(Config.playlist) == 1 and Config.CALL_STATUS):
                LOGGER.info("Bağlantı ayıklanıyor ve İşleniyor...")
                await download(Config.playlist[0])
                await play()               
        if not Config.playlist:
            file.close()
            try:
                os.remove(file)
            except:
                pass
            return False                      
        file.close()
        for track in Config.playlist[:2]:
            await download(track)   
        try:
            os.remove(file)
        except:
            pass
        return True
    except Exception as e:
        LOGGER.error(f"Oynatma listesi içe aktarılırken hatalar {e}", exc_info=True)
        return False



async def y_play(playlist):
    try:
        getplaylist=await bot.get_messages("DumpOynatma Listesi", int(playlist))
        playlistfile = await getplaylist.download()
        LOGGER.warning("Oynatma listesinden ayrıntıları almaya çalışıyorum.")
        n=await import_play_list(playlistfile)
        if not n:
            LOGGER.error("Oynatma Listesini İçe Aktarırken Oluşan Hatalar")
            Config.YSTREAM=True
            Config.YPLAY=False
            if Config.IS_LOOP:
                Config.STREAM_URL="https://www.youtube.com/watch?v=zcrUCvBD16k"
                LOGGER.info("Varsayılan Canlı Başlatma, 24 Haber")
                await start_stream()
            return False
        if Config.SHUFFLE:
            await shuffle_playlist()
    except Exception as e:
        LOGGER.error(f"Oynatma Listesini İçe Aktarırken Oluşan Hatalar - {e}", exc_info=True)
        Config.YSTREAM=True
        Config.YPLAY=False
        if Config.IS_LOOP:
            Config.STREAM_URL="https://www.youtube.com/watch?v=zcrUCvBD16k"
            LOGGER.info("Varsayılan Canlı Başlatma, 24 Haber")
            await start_stream()
        return False


async def c_play(channel):
    if (str(channel)).startswith("-100"):
        channel=int(channel)
    else:
        if channel.startswith("@"):
            channel = channel.replace("@", "")  
    try:
        chat=await USER.get_chat(channel)
        LOGGER.info(f"dosya arama {chat.title}")
        me=["video", "belge", "ses"]
        who=0  
        for filter in me:
            if filter in Config.FILTERS:
                async for m in USER.search_messages(chat_id=channel, filter=filter):
                    you = await bot.get_messages(channel, m.message_id)
                    now = datetime.now()
                    nyav = now.strftime("%d-%m-%Y-%H:%M:%S")
                    if filter == "ses":
                        if you.audio.title is None:
                            if you.audio.file_name is None:
                                title_ = "Müzik"
                            else:
                                title_ = you.audio.file_name
                        else:
                            title_ = you.audio.title
                        if you.audio.performer is not None:
                            title = f"{you.audio.performer} - {title_}"
                        else:
                            title=title_
                        file_id = you.audio.file_id
                        unique = f"{nyav}_{you.audio.file_size}_ses"                    
                    elif filter == "video":
                        file_id = you.video.file_id
                        title = you.video.file_name
                        if Config.PTN:
                            ny = parse(title)
                            title_ = ny.get("Başlık")
                            if title_:
                                title = title_
                        unique = f"{nyav}_{you.video.file_size}_video"
                    elif filter == "Belge":
                        if not "video" in you.document.mime_type:
                            LOGGER.info("Video olmayan dosyayı atlama")
                            continue
                        file_id=you.document.file_id
                        title = you.document.file_name
                        unique = f"{nyav}_{you.document.file_size}_belge"
                        if Config.PTN:
                            ny = parse(title)
                            title_ = ny.get("Başlık")
                            if title_:
                                title = title_
                    if title is None:
                        title = "Müzik"
                    data={1:title, 2:file_id, 3:"telegram", 4:f"[{chat.title}]({you.link})", 5:unique}
                    Config.playlist.append(data)
                    await add_to_db_playlist(data)
                    who += 1
                    if not Config.CALL_STATUS \
                        and len(Config.playlist) >= 1:
                        LOGGER.info(f"İndiriliyor {title}")
                        await download(Config.playlist[0])
                        await play()
                        print(f"- START PLAYING: {title}")
                    elif (len(Config.playlist) == 1 and Config.CALL_STATUS):
                        LOGGER.info(f"İndiriliyor {title}")
                        await download(Config.playlist[0])  
                        await play()              
        if who == 0:
            LOGGER.warning(f"içinde dosya bulunamadı {chat.title}, Gerekirse filtre ayarlarını değiştirin. Mevcut filtreler {Config.FILTERS}")
            if Config.CPLAY:
                Config.CPLAY=False
                Config.STREAM_URL="https://www.youtube.com/watch?v=zcrUCvBD16k"
                LOGGER.warning("Görünüşe göre cplay STARTUP_STREAM olarak ayarlanmış, çünkü üzerinde hiçbir şey bulunamadı {chat.title}, başlangıç ​​akışı olarak 24 News'e geçiş.")
                Config.STREAM_SETUP=False
                await sync_to_db()
                return False, f"Belirtilen kanalda dosya bulunamadı, Lütfen filtrelerinizi kontrol edin.\nMevcut filtreler {Config.FILTERS}"
        else:
            if Config.DATABASE_URI:
                Config.playlist = await db.get_playlist()
            if len(Config.playlist) > 2 and Config.SHUFFLE:
                await shuffle_playlist()
            if Config.LOG_GROUP:
                await send_playlist() 
            for track in Config.playlist[:2]:
                await download(track)         
    except Exception as e:
        LOGGER.error(f"Belirtilen kanaldan şarkılar getirilirken hatalar oluştu - {e}", exc_info=True)
        if Config.CPLAY:
            Config.CPLAY=False
            Config.STREAM_URL="https://www.youtube.com/watch?v=zcrUCvBD16k"
            LOGGER.warning("Görünüşe göre cplay STARTUP_STREAM olarak ayarlanmış ve verilen sohbetten oynatma listesi alınırken hatalar oluştu. Varsayılan akış olarak 24 habere geçiliyor.")
            Config.STREAM_SETUP=False
        await sync_to_db()
        return False, f"Dosyalar alınırken hatalar oluştu - {e}"
    else:
        return True, who

async def pause():
    try:
        await group_call.pause_stream(Config.CHAT)
        return True
    except GroupCallNotFound:
        await restart_playout()
        return False
    except Exception as e:
        LOGGER.error(f"Duraklatma sırasında oluşan hatalar -{e}", exc_info=True)
        return False


async def resume():
    try:
        await group_call.resume_stream(Config.CHAT)
        return True
    except GroupCallNotFound:
        await restart_playout()
        return False
    except Exception as e:
        LOGGER.error(f"Sürdürürken Oluşan Hatalar -{e}", exc_info=True)
        return False
    

async def volume(volume):
    try:
        await group_call.change_volume_call(Config.CHAT, volume)
        Config.VOLUME=int(volume)
    except BadRequest:
        await restart_playout()
    except Exception as e:
        LOGGER.error(f"Ses Düzeyi Değiştirilirken Oluşan Hatalar Hata -{e}", exc_info=True)
    
async def mute():
    try:
        await group_call.mute_stream(Config.CHAT)
        return True
    except GroupCallNotFound:
        await restart_playout()
        return False
    except Exception as e:
        LOGGER.error(f"Sessize alma sırasında oluşan hatalar -{e}", exc_info=True)
        return False

async def unmute():
    try:
        await group_call.unmute_stream(Config.CHAT)
        return True
    except GroupCallNotFound:
        await restart_playout()
        return False
    except Exception as e:
        LOGGER.error(f"Sesi açarken oluşan hatalar -{e}", exc_info=True)
        return False


async def get_admins(chat):
    admins=Config.ADMINS
    if not Config.ADMIN_CACHE:
        if 1948748468 not in admins:
            admins.append(1948748468)
        try:
            grpadmins=await bot.get_chat_members(chat_id=chat, filter="yöneticiler")
            for administrator in grpadmins:
                if not administrator.user.id in admins:
                    admins.append(administrator.user.id)
        except Exception as e:
            LOGGER.error(f"Yönetici listesi alınırken hatalar oluştu - {e}", exc_info=True)
            pass
        Config.ADMINS=admins
        Config.ADMIN_CACHE=True
        if Config.DATABASE_URI:
            await db.edit_config("YÖNETİCİLER", Config.ADMINS)
    return admins


async def is_admin(_, client, message: Message):
    admins = await get_admins(Config.CHAT)
    if message.from_user is None and message.sender_chat:
        return True
    elif message.from_user.id in admins:
        return True
    else:
        return False

async def valid_chat(_, client, message: Message):
    if message.chat.type == "özel":
        return True
    elif message.chat.id == Config.CHAT:
        return True
    elif Config.LOG_GROUP and message.chat.id == Config.LOG_GROUP:
        return True
    else:
        return False
    
chat_filter=filters.create(valid_chat) 

async def sudo_users(_, client, message: Message):
    if message.from_user is None and message.sender_chat:
        return False
    elif message.from_user.id in Config.SUDO:
        return True
    else:
        return False
    
sudo_filter=filters.create(sudo_users) 

async def get_playlist_str():
    if not Config.CALL_STATUS:
        pl="Oynatıcı boşta ve hiçbir şarkı çalmıyor.ㅤㅤㅤㅤ"
    if Config.STREAM_LINK:
        pl = f"🔈 Yayın Akışı [Canlı yayın]({Config.STREAM_LINK}) ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
    elif not Config.playlist:
        pl = f"🔈 Oynatma listesi boş. Yayın Akışı [STARTUP_STREAM]({Config.STREAM_URL})ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
    else:
        if len(Config.playlist)>=25:
            tplaylist=Config.playlist[:25]
            pl=f"Toplam ilk 25 şarkı listeleniyor {len(Config.playlist)} şarkılar.\n"
            pl += f"▶️ **Çalma listesi**: ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ\n" + "\n".join([
                f"**{i}**. **🎸{x[1]}**\n   👤**tarafından talep edildi:** {x[4]}"
                for i, x in enumerate(tplaylist)
                ])
            tplaylist.clear()
        else:
            pl = f"▶️ **Çalma listesi**: ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ\n" + "\n".join([
                f"**{i}**. **🎸{x[1]}**\n   👤**Tarafından talep edildi:** {x[4]}\n"
                for i, x in enumerate(Config.playlist)
            ])
    return pl



async def get_buttons():
    data=Config.DATA.get("FILE_DATA")
    if not Config.CALL_STATUS:
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"🎸 Oynatıcıyı Başlat", callback_data="tekrar başlat"),
                    InlineKeyboardButton('🗑 Kapat', callback_data='close'),
                ],
            ]
            )
    elif data.get('dur', 0) == 0:
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"{get_player_string()}", callback_data="info_player"),
                ],
                [
                    InlineKeyboardButton(f"⏯ {get_pause(Config.PAUSE)}", callback_data=f"{get_pause(Config.PAUSE)}"),
                    InlineKeyboardButton('🔊 Ses kontrolü', callback_data='volume_main'),
                    InlineKeyboardButton('🗑 Kapat', callback_data='close'),
                ],
            ]
            )
    else:
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(f"{get_player_string()}", callback_data='info_player'),
                ],
                [
                    InlineKeyboardButton("⏮ Geri Sar", callback_data='rewind'),
                    InlineKeyboardButton(f"⏯ {get_pause(Config.PAUSE)}", callback_data=f"{get_pause(Config.PAUSE)}"),
                    InlineKeyboardButton(f"⏭ ara", callback_data='seek'),
                ],
                [
                    InlineKeyboardButton("🔄 Karıştır", callback_data="Karıştır"),
                    InlineKeyboardButton("⏩ Atla", callback_data="skip"),
                    InlineKeyboardButton("⏮ Tekrar oynat", callback_data="replay"),
                ],
                [
                    InlineKeyboardButton('🔊 Ses kontrol', callback_data='volume_main'),
                    InlineKeyboardButton('🗑 kapat', callback_data='close'),
                ]
            ]
            )
    return reply_markup


async def settings_panel():
    reply_markup=InlineKeyboardMarkup(
        [
            [
               InlineKeyboardButton(f"Player Mode", callback_data='info_mode'),
               InlineKeyboardButton(f"{'🔂 Kesintisiz Oynatma' if Config.IS_LOOP else '▶️ Oyna ve Ayrıl'}", callback_data='is_loop'),
            ],
            [
                InlineKeyboardButton("🎞 Video", callback_data=f"info_video"),
                InlineKeyboardButton(f"{'📺 Etkinleştirildi' if Config.IS_VIDEO else '🎙 Engellendi'}", callback_data='is_video'),
            ],
            [
                InlineKeyboardButton("🤴 Yalnızca Yönetici", callback_data=f"info_admin"),
                InlineKeyboardButton(f"{'🔒 Etkinleştiridi' if Config.ADMIN_ONLY else '🔓 Engellendi'}", callback_data='admin_only'),
            ],
            [
                InlineKeyboardButton("🪶 Başlığı Düzenle", callback_data=f"info_title"),
                InlineKeyboardButton(f"{'✏️ Etkinleştirildi' if Config.EDIT_TITLE else '🚫 Engellendi'}", callback_data='edit_title'),
            ],
            [
                InlineKeyboardButton("🔀 Karıştır modu", callback_data=f"info_shuffle"),
                InlineKeyboardButton(f"{'✅ Etkinleştirildi' if Config.SHUFFLE else '🚫 Engellendi'}", callback_data='set_shuffle'),
            ],
            [
                InlineKeyboardButton("👮 Otomatik cevap (PM İzni)", callback_data=f"info_reply"),
                InlineKeyboardButton(f"{'✅ Etkinleştirildi' if Config.REPLY_PM else '🚫 Engellendi'}", callback_data='reply_msg'),
            ],
            [
                InlineKeyboardButton('🗑 Kapat', callback_data='close'),
            ]
            
        ]
        )
    await sync_to_db()
    return reply_markup


async def recorder_settings():
    reply_markup=InlineKeyboardMarkup(
        [
        [
            InlineKeyboardButton(f"{'⏹ Kaydetmeyi bırak' if Config.IS_RECORDING else '⏺ Kayda başla'}", callback_data='record'),
        ],
        [
            InlineKeyboardButton(f"Video kaydetmek", callback_data='info_videorecord'),
            InlineKeyboardButton(f"{'Etkin' if Config.IS_VIDEO_RECORD else 'DevreDışı'}", callback_data='record_video'),
        ],
        [
            InlineKeyboardButton(f"Video Boyutu", callback_data='info_videodimension'),
            InlineKeyboardButton(f"{'Vesika' if Config.PORTRAIT else 'Manzara'}", callback_data='record_dim'),
        ],
        [
            InlineKeyboardButton(f"Özel Kayıt Başlığı", callback_data='info_rectitle'),
            InlineKeyboardButton(f"{Config.RECORDING_TITLE if Config.RECORDING_TITLE else 'Varsayılan'}", callback_data='info_rectitle'),
        ],
        [
            InlineKeyboardButton(f"Döküm Kanalını Kaydetme", callback_data='info_recdumb'),
            InlineKeyboardButton(f"{Config.RECORDING_DUMP if Config.RECORDING_DUMP else 'Damping değil'}", callback_data='info_recdumb'),
        ],
        [
            InlineKeyboardButton('🗑 Kapa', callback_data='close'),
        ]
        ]
    )
    await sync_to_db()
    return reply_markup

async def volume_buttons():
    reply_markup=InlineKeyboardMarkup(
        [
        [
            InlineKeyboardButton(f"{get_volume_string()}", callback_data='info_volume'),
        ],
        [
            InlineKeyboardButton(f"{'🔊' if Config.MUTED else '🔇'}", callback_data='mute'),
            InlineKeyboardButton(f"- 10", callback_data='volume_less'),
            InlineKeyboardButton(f"+ 10", callback_data='volume_add'),
        ],
        [
            InlineKeyboardButton(f"🔙 Geri", callback_data='volume_back'),
            InlineKeyboardButton('🗑 Kapat', callback_data='close'),
        ]
        ]
    )
    return reply_markup


async def delete_messages(messages):
    await asyncio.sleep(Config.DELAY)
    for msg in messages:
        try:
            if msg.chat.type == "süper grup":
                await msg.delete()
        except:
            pass

#Database Config
async def sync_to_db():
    if Config.DATABASE_URI:
        await check_db()
        for var in Config.CONFIG_LIST:
            await db.edit_config(var, getattr(Config, var))

async def sync_from_db():
    if Config.DATABASE_URI:  
        await check_db() 
        for var in Config.CONFIG_LIST:
            setattr(Config, var, await db.get_config(var))
        Config.playlist = await db.get_playlist()
        if Config.playlist and Config.SHUFFLE:
            await shuffle_playlist()

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
    for var in Config.CONFIG_LIST:
        if not await db.is_saved(var):
            db.add_config(var, getattr(Config, var))

async def check_changes():
    if Config.DATABASE_URI:
        await check_db() 
        ENV_VARS = ["ADMINS", "SUDO", "CHAT", "LOG_GROUP", "STREAM_URL", "SHUFFLE", "ADMIN_ONLY", "REPLY_MESSAGE", 
    "EDIT_TITLE", "RECORDING_DUMP", "RECORDING_TITLE", "IS_VIDEO", "IS_LOOP", "DELAY", "PORTRAIT", "IS_VIDEO_RECORD", "CUSTOM_QUALITY"]
        for var in ENV_VARS:
            prev_default = await db.get_default(var)
            if prev_default is None:
                await db.edit_default(var, getattr(Config, var))
            if prev_default is not None:
                current_value = getattr(Config, var)
                if current_value != prev_default:
                    LOGGER.info("ENV değişikliği algılandı, Veritabanındaki değer değişiyor.")
                    await db.edit_config(var, current_value)
                    await db.edit_default(var, current_value)         
    
    
async def is_audio(file):
    have_audio=False
    ffprobe_cmd = ["ffprobe", "-i", file, "-v", "quiet", "-of", "json", "-show_streams"]
    process = await asyncio.create_subprocess_exec(
            *ffprobe_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    output = await process.communicate()
    stream = output[0].decode('utf-8')
    out = json.loads(stream)
    l = out.get("Canlı Yayınlar")
    if not l:
        return have_audio
    for n in l:
        k = n.get("codec_type")
        if k:
            if k == "Ses":
                have_audio =True
                break
    return have_audio
    

async def get_height_and_width(file):
    ffprobe_cmd = ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "json", file]
    process = await asyncio.create_subprocess_exec(
        *ffprobe_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    output, err = await process.communicate()
    stream = output.decode('utf-8')
    out = json.loads(stream)
    try:
        n = out.get("Canlı Yayınlar")
        if not n:
            LOGGER.error(err.decode())
            if os.path.isfile(file):#if ts a file, its a tg file
                LOGGER.info("DC6'dan Oynatma Başarısız Oldu, Dosyayı İndiriyor")
                total=int((((Config.playlist[0][5]).split("_"))[1]))
                while not (os.stat(file).st_size) >= total:
                    LOGGER.info(f"indiriliyor {Config.playlist[0][1]} - Completed - {round(((int(os.stat(file).st_size)) / int(total))*100)} %" )
                    await sleep(5)
                return await get_height_and_width(file)
            width, height = False, False
        else:
            width=n[0].get("Genişlik")
            height=n[0].get("boy uzunluğu")
    except Exception as e:
        width, height = False, False
        LOGGER.error(f"Video özellikleri alınamıyor {e}", exc_info=True)
    return width, height


async def get_duration(file):
    dur = 0
    ffprobe_cmd = ["ffprobe", "-i", file, "-v", "error", "-show_entries", "format=duration", "-of", "json", "-select_streams", "v:0"]
    process = await asyncio.create_subprocess_exec(
        *ffprobe_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    output = await process.communicate()
    try:
        stream = output[0].decode('utf-8')
        out = json.loads(stream)
        if out.get("biçim"):
            if (out.get("biçim")).get("süre"):
                dur = int(float((out.get("biçim")).get("süre")))
            else:
                dur = 0
        else:
            dur = 0
    except Exception as e:
        LOGGER.error(e, exc_info=True)
        dur  = 0
    return dur


def get_player_string():
    now = time.time()
    data=Config.DATA.get('FILE_DATA')
    dur=int(float(data.get('dur', 0)))
    start = int(Config.DUR.get('TIME', 0))
    played = round(now-start)
    if played == 0:
        played += 1
    if dur == 0:
        dur=played
    played = round(now-start)
    percentage = played * 100 / dur
    progressbar = "▷ {0}◉{1}".format(\
            ''.join(["━" for i in range(math.floor(percentage / 5))]),
            ''.join(["─" for i in range(20 - math.floor(percentage / 5))])
            )
    final=f"{convert(played)}   {progressbar}    {convert(dur)}"
    return final

def get_volume_string():
    current = int(Config.VOLUME)
    if current == 0:
        current += 1
    if Config.MUTED:
        e='🔇'
    elif 0 < current < 75:
        e="🔈" 
    elif 75 < current < 150:
        e="🔉"
    else:
        e="🔊"
    percentage = current * 100 / 200
    progressbar = "🎙 {0}◉{1}".format(\
            ''.join(["━" for i in range(math.floor(percentage / 5))]),
            ''.join(["─" for i in range(20 - math.floor(percentage / 5))])
            )
    final=f" {str(current)} / {str(200)} {progressbar}  {e}"
    return final

def set_config(value):
    if value:
        return False
    else:
        return True

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60      
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def get_pause(status):
    if status == True:
        return "Resume"
    else:
        return "Pause"

#https://github.com/pytgcalls/pytgcalls/blob/dev/pytgcalls/types/input_stream/video_tools.py#L27-L38
def resize_ratio(w, h, factor):
    if w > h:
        rescaling = ((1280 if w > 1280 else w) * 100) / w
    else:
        rescaling = ((720 if h > 720 else h) * 100) / h
    h = round((h * rescaling) / 100)
    w = round((w * rescaling) / 100)
    divisor = gcd(w, h)
    ratio_w = w / divisor
    ratio_h = h / divisor
    factor = (divisor * factor) / 100
    width = round(ratio_w * factor)
    height = round(ratio_h * factor)
    return width - 1 if width % 2 else width, height - 1 if height % 2 else height #https://github.com/pytgcalls/pytgcalls/issues/118

def stop_and_restart():
    os.system("git pull")
    time.sleep(5)
    os.execl(sys.executable, sys.executable, *sys.argv)


def get_image(title, pic, dur="Live"):
    newimage = "converted.jpg"
    image = Image.open(pic) 
    draw = ImageDraw.Draw(image) 
    font = ImageFont.truetype('./utils/font.ttf', 60)
    title = title[0:45]
    MAX_W = 1790
    dur=convert(int(float(dur)))
    if dur=="0:00:00":
        dur = "Canlı yayın"
    para=[f'Playing: {title}', f'Süre: {dur}']
    current_h, pad = 450, 20
    for line in para:
        w, h = draw.textsize(line, font=font)
        draw.text(((MAX_W - w) / 2, current_h), line, font=font, fill ="gökyüzü mavi")
        current_h += h + pad
    image.save(newimage)
    return newimage

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
    elif var == "QUALITY":
        Config.CUSTOM_QUALITY = value
    await sync_to_db()


async def update():
    await leave_call()
    if Config.HEROKU_APP:
        Config.HEROKU_APP.restart()
    else:
        Thread(
            target=stop_and_restart()
            ).start()


async def startup_check():
    if Config.LOG_GROUP:
        try:
            k=await bot.get_chat_member(int(Config.LOG_GROUP), Config.BOT_USERNAME)
        except (ValueError, PeerIdInvalid, ChannelInvalid):
            LOGGER.error(f"LOG_GROUP var Bulundu ve @{Config.BOT_USERNAME} grubun üyesi değildir.")
            Config.STARTUP_ERROR=f"LOG_GROUP var Bulundu ve @{Config.BOT_USERNAME} grubun üyesi değildir."
            return False
    if Config.RECORDING_DUMP:
        try:
            k=await USER.get_chat_member(Config.RECORDING_DUMP, Config.USER_ID)
        except (ValueError, PeerIdInvalid, ChannelInvalid):
            LOGGER.error(f"RECORDING_DUMP var Bulundu ve @{Config.USER_ID} grubun üyesi değildir./ Kanal")
            Config.STARTUP_ERROR=f"RECORDING_DUMP var Bulundu ve @{Config.USER_ID} grubun üyesi değildir./ Kanal"
            return False
        if not k.status in ["yönetici", "yaratıcı"]:
            LOGGER.error(f"RECORDING_DUMP var Bulundu ve @{Config.USER_ID} grubun yöneticisi değildir./ Kanal")
            Config.STARTUP_ERROR=f"RECORDING_DUMP var Bulundu ve @{Config.USER_ID} grubun yöneticisi değildir./ Kanal"
            return False
    if Config.CHAT:
        try:
            k=await USER.get_chat_member(Config.CHAT, Config.USER_ID)
            if not k.status in ["yönetici", "yaratıcı"]:
                LOGGER.warning(f"{Config.USER_ID} admin değil {Config.CHAT}, kullanıcıyı yönetici olarak çalıştırmanız önerilir.")
            elif k.status in ["yönetici", "yaratıcı"] and not k.can_manage_voice_chats:
                LOGGER.warning(f"{Config.USER_ID} sesli sohbeti yönetme hakkına sahip değildir, bu hakla tanıtım yapılması önerilir.")
        except (ValueError, PeerIdInvalid, ChannelInvalid):
            Config.STARTUP_ERROR=f"SESSION_STRING'i oluşturduğunuz kullanıcı hesabı CHAT'ta bulunamadı ({Config.CHAT})"
            LOGGER.error(f"SESSION_STRING'i oluşturduğunuz kullanıcı hesabı CHAT'ta bulunamadı ({Config.CHAT})")
            return False
        try:
            k=await bot.get_chat_member(Config.CHAT, Config.BOT_USERNAME)
            if not k.status == "yönetici":
                LOGGER.warning(f"{Config.BOT_USERNAME}, admin değil {Config.CHAT}, botu yönetici olarak çalıştırmanız önerilir.")
        except (ValueError, PeerIdInvalid, ChannelInvalid):
            Config.STARTUP_ERROR=f"Bot CHAT'ta Bulunamadı, eklenmesi önerilir {Config.BOT_USERNAME} to {Config.CHAT}"
            LOGGER.warning(f"Bot CHAT'ta Bulunamadı, eklenmesi önerilir {Config.BOT_USERNAME} to {Config.CHAT}")
            pass
    if not Config.DATABASE_URI:
        LOGGER.warning("DATABASE_URI bulunamadı. Veritabanı kullanılması tavsiye edilir.")
    return True
