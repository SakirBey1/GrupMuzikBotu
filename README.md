## Developer [Sahibim](https://t.me/SakirBey1)
Telegram botu, hem gruplar hem de kanallar için telegram sesli sohbetinde video akışı sağlar. Canlı akışları, YouTube videolarını ve telgraf medyasını destekler. Kayıt akışı desteği, Zamanlama akışları ve çok daha fazlası ile.

## Yapılandırma Değişkenleri:
### Zorunlu Değişkenler
1. "API_ID" : [API_ID al](https://t.me/OtoMyTelegramBot)
2. "API_HASH" : [API_HASH al](https://t.me/OtoMyTelegramBot) adresinden alın
3. "BOT_TOKEN" : [@Botfather](https://telegram.dog/BotFather)
4. `SESSION_STRING` : Buradan Oluştur [string oluştur](https://t.me/stringsessionbuzz_bot)
5. `CHAT` : Botun Müzik çaldığı Kanalın/Grubun kimliği.

## Önerilen İsteğe Bağlı Değişkenler

1. `DATABASE_URI`: MongoDB veritabanı URL'si, [mongodb](https://cloud.mongodb.com) adresinden alın. Bu isteğe bağlı bir değişkendir, ancak tüm özellikleri deneyimlemek için bunu kullanmanız önerilir.
2. `HEROKU_API_KEY`: Heroku API anahtarınız. [Buradan](https://dashboard.heroku.com/account/applications/authorizations/new) bir tane edinin
3. `HEROKU_APP_NAME`: Heroku uygulamalarınızın adı.
4. `FİLTRELER`: Kanal oynatma aramasını filtreleyin. Kanal oynatma, /cplay komutunu kullanarak özel bir kanaldaki tüm dosyaları oynatabileceğiniz anlamına gelir. Geçerli filtreler "video belgesi" dir. Ses dosyalarını aramak için `video belgesi sesi`ni kullanın. yalnızca video araması için 'video'yu vb. kullanın.

### İsteğe Bağlı Değişkenler
1. `LOG_GROUP` : CHAT bir Grup ise, Çalma Listesi gönderilecek grup()
2. `YÖNETİCİLER` : Yönetici komutlarını kullanabilen kullanıcıların kimliği.
3. `STARTUP_STREAM` : Bu, botun yeniden başlatılmasında ve yeniden başlatılmasında yayınlanacaktır. Herhangi bir STREAM_URL'yi veya herhangi bir videonun doğrudan bağlantısını veya bir Youtube Canlı bağlantısını kullanabilirsiniz. Ayrıca YouTube Oynatma Listesini de kullanabilirsiniz. adresinden oynatma listeniz için bir Telegram Bağlantısı bulabilir veya . Oynatma Listesi bağlantısı "" biçiminde olmalıdır.
4. `REPLY_MESSAGE` : KULLANICI hesabına PM ile mesaj atanlara cevap. Bu özelliğe ihtiyacınız yoksa boş bırakın. (Mongodb eklendiyse bot aracılığıyla yapılandırılabilir.)
5. `ADMIN_ONLY` : `True`yu Geçir Eğer sadece `CHAT` yöneticileri için /play komutu yapmak istiyorsanız. Varsayılan olarak /play herkes için mevcuttur.(Mongodb eklendiyse bot aracılığıyla yapılandırılabilir.)
6. `DATABASE_NAME`: mongodb veritabanınız için veritabanı adı.
7. `SHUFFLE` : Çalma listelerini karıştırmak istemiyorsanız `False` yapın. (Mongodb eklendiyse bot aracılığıyla yapılandırılabilir.)
8. 'EDIT_TITLE' : Botun çalan şarkıya göre görüntülü sohbet başlığını düzenlemesini istemiyorsanız 'Yanlış' yapın. (Mongodb eklendiyse bot aracılığıyla yapılandırılabilir.)
9. `RECORDING_DUMP` : Görüntülü sohbet kayıtlarını boşaltmak için yönetici olarak KULLANICI hesabı olan bir Kanal Kimliği.
10. `RECORDING_TITLE`: Görüntülü sohbet kayıtlarınız için özel bir başlık.
11. `TIME_ZONE` : Ülkenizin Saat Dilimi, varsayılan olarak IST
12. `IS_VIDEO_RECORD` : Video kaydetmek istemiyorsanız `False` yapın ve sadece ses kaydedilecektir.(Mongodb eklendiyse bot ile yapılandırılabilir.)
13. "IS_LOOP"; 7/24 Görüntülü Sohbet istemiyorsanız 'Yanlış' yapın. (Mongodb eklendiyse bot aracılığıyla yapılandırılabilir.)
14. `IS_VIDEO` : Oynatıcıyı videosuz bir müzik çalar olarak kullanmak istiyorsanız `Yanlış` yapın. (Mongodb eklendiyse bot aracılığıyla yapılandırılabilir.)
15. 'PORTRE': Video kaydını portre modunda istiyorsanız 'Doğru' yapın. (Mongodb eklendiyse bot aracılığıyla yapılandırılabilir.)
16. `DELAY` : Komutların silinmesi için zaman sınırını seçin. Varsayılan olarak 10 sn.
18. "KALİTE" : Görüntülü sohbetin kalitesini özelleştirin, "yüksek", "orta", "düşük" seçeneklerinden birini kullanın.
19. `BITRATE` : Ses bit hızı (Değiştirilmesi önerilmez).
20. `FPS` : Oynatılacak videonun Fps'si (Değiştirilmesi tavsiye edilmez.)



## Requirements
- Python 3.8 or Higher.



## Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/SakirBey1/GrupMuzikBotu)


 


## Özellikleri

- Çalma listesi, sıra.
- Oynarken sıfır kesinti.
- Video Kaydı destekler.
- Zamanlama sesli sohbetleri destekler.
- Oyuncuyu kontrol etmek için harika kullanıcı arayüzü.
- Ses veya videoya göre özelleştirin.
- Görüntülü sohbetler için özel kalite.
- Youtube Oynatma Listesinden Oynatmayı destekler.
- VoiceChat başlığını mevcut çalmakta olan şarkı adına değiştirin.
- youtube'dan Canlı akışı destekler
- Desteklenen telgraf dosyasından oynatın.
- Çalma listesinde şarkı yoksa Radyo'yu başlatır.
- Heroku yeniden başlasa bile otomatik yeniden başlatma. (Yapılandırılabilir)
- Çalma listesini dışa aktarma ve içe aktarma desteği.

Bu kodların çalınması yada çatallanması sizi bir cooder veya developer yapmaz ama lazım ise bi kaç değişiklik yapa bilirsiniz bu proje açık kaynaklı kodlanmıştır kod sahibi ile iletişim için [telegram](https://t.me/SakirBey1) 'dan ulaşa bilirsiniz ...!

## LICENSE

- [GNU General Public License](./LICENSE)


## iletişim

- [İnstagram](https://www.instagram.com/sakir_hack81.21/) veya [Telegram](https://t.me/Sakirbey1)


