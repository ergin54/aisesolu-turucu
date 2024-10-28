import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import uuid
import time

bot = telebot.TeleBot(input("Telegram bot tokeni: "))

SAYFA_BASI_SES = 30

def VeriAl():
    try:
        url = "https://ai-voice.nyc3.cdn.digitaloceanspaces.com/data/data.json"
        headers = HeaderOlustur()
        response = requests.get(url, headers=headers)        
        if response.status_code == 200:
            data = response.json()
            return data.get('voices', [])
        else:
            print(f"Sesler alınırken hata oluştu. Durum Kodu: {response.status_code}")
            return []
    except Exception as e:
        print(f"Sesler alınırken hata oluştu: {e}")
        return []

def KimlikOlustur():
    kimlik_1 = uuid.uuid4().hex
    baslangic_zamani = str(int(time.time() * 1000))
    kimlik_9 = uuid.uuid4().hex + ":APA91b"
    return kimlik_1, baslangic_zamani, kimlik_9

def HeaderOlustur():
    return {
        'User-Agent': "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Build/RKQ1.201004.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/129.0.6668.100 Mobile Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Android WebView\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        'sec-ch-ua-mobile': "?1",
        'origin': "http://localhost",
        'x-requested-with': "com.leonfiedler.voiceaj",
        'sec-fetch-site': "cross-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "http://localhost/",
        'accept-language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        'priority': "u=1, i"
    }

@bot.message_handler(commands=['start'])
def Baslat(message):
    bot.reply_to(message, "Merhaba 👋 Başlamak için lütfen bir ses seçin.")
    SesleriGoster(message, sayfa=1)

def SesleriGoster(message, sayfa=1):
    sesler = VeriAl()    
    if not sesler:
        bot.send_message(message.chat.id, "Şu anda kullanılabilir ses bulunmuyor.")
        return
    
    baslangic_idx = (sayfa - 1) * SAYFA_BASI_SES
    bitis_idx = baslangic_idx + SAYFA_BASI_SES
    mevcut_sesler = sesler[baslangic_idx:bitis_idx]    
    
    markup = InlineKeyboardMarkup(row_width=3)  
    butonlar = [InlineKeyboardButton(f"{ses['name']}", callback_data=f"voice_{idx}") for idx, ses in enumerate(mevcut_sesler, start=baslangic_idx)]
    markup.add(*butonlar)
    
    sayfalama_butonlari = []
    if baslangic_idx > 0:
        sayfalama_butonlari.append(InlineKeyboardButton("Önceki ⬅️", callback_data=f"page_{sayfa-1}"))
    if bitis_idx < len(sesler):
        sayfalama_butonlari.append(InlineKeyboardButton("Sonraki ➡️", callback_data=f"page_{sayfa+1}"))    
    
    if sayfalama_butonlari:
        markup.add(*sayfalama_butonlari)
    
    if sayfa == 1:
        bot.send_message(message.chat.id, "Bir ses seçin:", reply_markup=markup)
    else:
        bot.edit_message_text("Bir ses seçin:", chat_id=message.chat.id, message_id=message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("voice_") or call.data.startswith("page_"))
def CallbackIsle(call):
    if call.data.startswith("voice_"):
        SesSeciminiIsle(call)
    elif call.data.startswith("page_"):
        sayfa = int(call.data.split("_")[1])
        SesleriGoster(call.message, sayfa)

def SesSeciminiIsle(call):
    try:
        ses_idx = int(call.data.split("_")[1])
        sesler = VeriAl()
        secilen_ses = sesler[ses_idx]
        
        if ses_idx >= 183:
            bot.send_message(call.message.chat.id, f"Seçtiğiniz: {secilen_ses['name']}\n Görsel yapımcı tarafından engellendi.")
        else:
            gorsel_url = f"https://ai-voice.nyc3.cdn.digitaloceanspaces.com/voice_images/{secilen_ses['image_ios'].split('/')[-1]}"
            gorsel_response = requests.get(gorsel_url)
            if gorsel_response.status_code == 200:
                bot.send_photo(call.message.chat.id, gorsel_response.content, caption=f"Seçtiğiniz: {secilen_ses['name']}")
        
        bot.send_message(call.message.chat.id, "Merhaba, lütfen sese dönüşmesini istediğiniz | (sadece ) metni | girin.")
        bot.register_next_step_handler(call.message, MetniIsle, secilen_ses)
    except Exception as e:
        print(f"SesSeciminiIsle'de hata: {e}")

def MetniIsle(message, secilen_ses):
    metin = message.text
    bot.send_message(message.chat.id, "Lütfen biraz bekle... hemen hazır olacak.")
    if len(metin) > 200:
        bot.send_message(message.chat.id, "Üzgünüm, ücretsiz sürümdesiniz. 200 karakterden fazla metin giremezsiniz. Puan artırımı için güncellemeyi bekleyin.")
        return
    
    while True:
        try:
            kimlik_1, baslangic_zamani, kimlik_9 = KimlikOlustur()
            token2, kimlik_2, olusturma_zamani = KullaniciOlustur()           
            
            if token2 and kimlik_2 and olusturma_zamani:
                KullaniciyiKaydet(kimlik_2, token2, kimlik_1)
                ses_verisi = SesiOlustur(kimlik_2, token2, olusturma_zamani, kimlik_1, kimlik_9, secilen_ses['voiceId'], metin, secilen_ses['name'])
                bot.send_audio(message.chat.id, ses_verisi, title=f"{secilen_ses['name']} @yusuf_ergin") #Telegram @yusuf_ergin
                break  
        except Exception as e:
            print(f"MetniIsle döngüsünde hata: {e}")

def KullaniciOlustur():
    try:
        kayit_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser"
        parametre = {'key': "AIzaSyDk5Vr0fvGX3AF3mNfMghP6Q-ECoBYT7aE"}
        veri = json.dumps({"clientType": "CLIENT_TYPE_ANDROID"})       
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; Redmi Note 8 Build/RKQ1.201004.002)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/json",
            'X-Android-Package': "com.leonfiedler.voiceaj",
            'X-Android-Cert': "61ED377E85D386A8DFEE6B864BD85B0BFAA5AF81",
            'Accept-Language': "ar-EG, en-US",
            'X-Client-Version': "Android/Fallback/X23000000/FirebaseCore-Android",
            'X-Firebase-GMPID': "1:444011263758:android:acbabc2d1f24666531495f",
            'X-Firebase-Client': "H4sIAAAAAAAAAKtWykhNLCpJSk0sKVayio7VUSpLLSrOzM9TslIyUqoFAFyivEQfAAAA"
        }
        
        while True:
            kayit_response = requests.post(kayit_url, params=parametre, data=veri, headers=headers)
            kayit_data = kayit_response.json()
            token2 = kayit_data['idToken']
            
            bilgi_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo"
            token_data = json.dumps({"idToken": token2})
            bilgi_response = requests.post(bilgi_url, params=parametre, data=token_data, headers=headers)
            kullanici_data = bilgi_response.json()
            
            kimlik_2 = kullanici_data['users'][0]['localId']
            olusturma_zamani = kullanici_data['users'][0]['createdAt']
            return token2, kimlik_2, olusturma_zamani
            
    except Exception as e:
        print(f"KullaniciOlustur'da hata: {e}")
        return None, None, None

def KullaniciyiKaydet(kimlik_2, token2, kimlik_1):
    try:
        url = "https://connect.getvoices.ai/api/v1/user"
        veri = json.dumps({
            "uid": kimlik_2,
            "isNew": True,
            "uuid": f"android_{kimlik_1}",
            "platform": "android",
            "appVersion": "1.9.1"
        })
        headers = HeaderOlustur()
        headers['authorization'] = token2
        requests.post(url, data=veri, headers=headers)
    except Exception as e:
        print(f"KullaniciyiKaydet'te hata: {e}")

def SesiOlustur(kimlik_2, token2, olusturma_zamani, kimlik_1, kimlik_9, ses_id, metin, ses_adi):
    try:
        url = "https://connect.getvoices.ai/api/v1/text2speech/stream"
        veri = json.dumps({
            "voiceId": ses_id,
            "text": metin,
            "deviceId": kimlik_1,
            "uid": kimlik_2,
            "startTime": olusturma_zamani,
            "translate": None,
            "fcmToken": kimlik_9,
            "appVersion": "1.9.1"
        })        
        headers = HeaderOlustur()
        headers['authorization'] = token2
        response = requests.post(url, data=veri, headers=headers)
        return response.content
    except Exception as e:
        print(f"SesiOlustur'da hata: {e}")
        return None

if __name__ == "__main__":
    bot.polling()
