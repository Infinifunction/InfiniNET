# InfiniNET

> **Gateway tabanlı ağ yapılandırma, erişim kontrolü, trafik izleme ve ağ yönetim sistemi.**

InfiniNET, yerel bir ağ üzerinde **Gateway** olarak çalışmak üzere tasarlanmış Python tabanlı bir ağ yönetim sistemidir. Gateway cihazı DHCP, DNS, proxy ve WPAD gibi ağ servislerini üstlenirken aynı zamanda ağa bağlı cihazların izlenmesi ve yönetilmesi için web tabanlı bir yönetim paneli sunar.

Proje **yetkili ağ yönetimi, test, geliştirme ve eğitim amaçlarıyla** kullanılmak üzere tasarlanmıştır.

---

## ✨ Özellikler

InfiniNET merkezi bir ağ yönetimi yapısı içerisinde çeşitli yönetim ve izleme özellikleri sunar.

### Ağ Yönetimi

- Gateway tabanlı ağ yönetimi
- DHCP sunucusu işlevi
- Otomatik IP adresi dağıtımı
- DNS sunucusu / DNS proxy işlevi
- DNS tabanlı site/domain engelleme
- HTTP/HTTPS proxy işlevi
- WPAD / PAC yapılandırması dağıtımı
- Statik Gateway IP gereksinimi
- Aktif oturum yönetimi

### Captive Portal

- Captive Portal kimlik doğrulama akışı
- Yönetici tarafından belirlenen kullanıcı adı ve şifre
- Ağa bağlanan cihazların erişim kontrolü
- Yetkisiz istemcilerin erişim akışının yönetilmesi
- Giriş/erişim olaylarının kaydedilmesi

### Canlı Trafik İzleme

- Canlı trafik izleme
- Canlı trafik logları
- HTTP isteklerinin izlenmesi
- HTTPS CONNECT bağlantılarında SNI bilgilerinin engelleme kurallarıyla karşılaştırılması
- Download / upload hareket göstergeleri
- Gerçek zamanlı ağ durum bilgileri

### Hız Limitleme

- Cihaza özel bant genişliği limiti
- Genel ağ bant genişliği limiti
- Yönetim panelinden dinamik hız limiti yönetimi
- Cihaza özel hız limitini kaldırabilme

### Cihaz Yönetimi

- Aktif cihaz tespiti
- IP adresi bilgisi
- Hostname bilgisi
- User-Agent bilgisi
- Cihaz türü bilgisi
- Cihaz fingerprint bilgileri
- Fingerprint hash
- İlk görülme bilgisi
- Cihaz ping/durum bilgisi
- Download / upload yön göstergeleri
- Cihaz oturumunu kapatma
- Cihaz envanteri
- Cihaz detay ekranı

### Veritabanı

InfiniNET, `InfiniDB.py` üzerinden SQLite tabanlı bir veritabanı katmanı kullanır.

Veritabanı sistemi aşağıdaki gibi proje durumlarını saklamak ve yeniden yüklemek için kullanılır:

- Aktif oturumlar
- Yasaklama/engelleme kuralları
- Erişim logları
- Cihaz ve oturum ile ilişkili kayıtlar

Ayrıca web yönetim paneli üzerinden SQLite tablolarını görüntülemek için bir veritabanı tarayıcısı bulunmaktadır.

### Yönetim Paneli

Flask tabanlı yönetim paneli üzerinden:

- Dashboard istatistikleri
- Aktif oturumlar
- Engelleme kuralları
- Genel ve cihaza özel hız limitleri
- Canlı trafik bilgileri
- Cihaz envanteri
- Cihaz detayları
- Fingerprint bilgileri
- Veritabanı görüntüleme
- Oturum kapatma
- Hot-reload tetikleme

işlemleri gerçekleştirilebilir.

---

## 🏗️ Sistem Mimarisi

Projenin ana başlatıcısı:

```text
InfiniDHCP.py
```

Sistemin genel çalışma modeli aşağıdaki gibidir:

```text
                    ┌─────────────────────────┐
                    │       Yönetici          │
                    │    Web Yönetim Paneli   │
                    └────────────┬────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                      InfiniNET Gateway                       │
│                                                              │
│  DHCP        DNS        Proxy        WPAD       Captive      │
│  Sunucusu    Sunucusu   Katmanı      Servisi     Portal      │
│                                                              │
│                InfiniDB / Çalışma Durumu                     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │
                 ┌─────────────┴─────────────┐
                 │         Yerel Ağ           │
                 └─────────────┬─────────────┘
                               │
               ┌───────────────┼────────────────┐
               │               │                │
            Cihaz A          Cihaz B          Cihaz C
```

### Çalışma Mantığı

1. Gateway olarak kullanılacak cihaz üzerinde `InfiniDHCP.py` başlatılır.
2. Gateway cihazı DHCP servisini çalıştırır.
3. Ağa bağlanan istemcilere yapılandırılmış IP aralığından adres dağıtılır.
4. DHCP üzerinden istemcilere Gateway, DNS ve WPAD bilgileri iletilir.
5. DNS istekleri projenin DNS katmanı tarafından işlenir.
6. HTTP/HTTPS trafiği proxy katmanı üzerinden işlenir.
7. İstemciler, aktif yapılandırmaya göre Captive Portal kimlik doğrulama akışına yönlendirilir.
8. Yetkilendirilmiş kullanıcılar belirlenen ağ kuralları dahilinde erişim sağlayabilir.
9. Yönetim paneli üzerinden sistem ve istemciler canlı olarak izlenebilir ve yönetilebilir.

---

## 📦 Gereksinimler

### Yazılım Gereksinimleri

- Python **3.10**
- Npcap
- SQLite
- JavaScript destekli web tarayıcısı

### Python Kütüphaneleri

Mevcut `requirements.txt` dosyasında:

```text
Flask==3.1.3
scapy==2.7.0
```

bulunmaktadır.

Kütüphaneler her zaman depodaki `requirements.txt` dosyası üzerinden kurulmalıdır.

---

## 🚀 Kurulum

### 1. Python 3.10 Kurulumu

Gateway olarak kullanılacak bilgisayara **Python 3.10** kurulmalıdır.

Kontrol etmek için:

```bash
python --version
```

Beklenen sürüm:

```text
Python 3.10.x
```

### 2. Npcap Kurulumu

Paket yakalama desteği gereken sistemlerde **Npcap** kurulmalıdır.

### 3. Python Gereksinimlerinin Kurulması

Projenin ana dizininde:

```bash
pip install -r requirements.txt
```

komutu çalıştırılmalıdır.

### 4. Gateway IP Adresinin Ayarlanması

Gateway olarak kullanılacak cihazın **statik IP adresine** sahip olması gerekir.

Proje için gerekli Gateway IP adresi:

```text
192.168.1.101
```

Bu IP adresinin ağ içerisinde başka bir cihaz tarafından kullanılmadığından emin olunmalıdır.

### 5. InfiniNET'i Başlatma

Ana başlatıcı:

```bash
python InfiniDHCP.py
```

komutu ile çalıştırılır.

Ana başlatıcı; veritabanını ve kayıtlı durumu yükledikten sonra gerekli sistem bileşenlerini başlatır.

---

## 📁 Klasör ve Dosya Yapısı

```text
InfiniNET/
│
├── auto_reloader.py
├── config.py
├── dhcp_module.py
├── dns_module.py
├── InfiniDB.py
├── InfiniDHCP.py
├── proxy_module.py
├── requirements.txt
├── templates.py
├── wpad_module.py
│
└── admin/
    ├── app.py
    │
    ├── routes/
    │   ├── api_bans.py
    │   ├── api_db.py
    │   ├── api_speed.py
    │   └── api_system.py
    │
    ├── static/
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── dashboard.js
    │
    └── templates/
        ├── dashboard.html
        ├── db_browser.html
        └── devices.html
```

---

## 🧩 Ana Modüller

### `InfiniDHCP.py`

Projenin ana başlatıcısı ve orchestrator modülüdür.

Veritabanını ve kayıtlı durumu yükler; ardından hot-reload, DNS, WPAD, DHCP, konsol ve yönetim paneli bileşenlerini başlatır. Daha sonra proxy sunucusunu çalıştırır.

### `dhcp_module.py`

Projenin DHCP sunucusu/modülüdür.

Başlıca görevleri:

- UDP 67 üzerinden DHCP isteklerini dinlemek
- `192.168.1.105` – `192.168.1.200` aralığından IP dağıtmak
- DHCP OFFER ve ACK paketleri oluşturmak
- İstemci IP bilgilerini kaydetmek
- Gateway, DNS ve WPAD bilgilerini istemcilere iletmek

### `dns_module.py`

Projenin DNS sunucusu / proxy katmanıdır.

Başlıca görevleri:

- UDP üzerinden DNS isteklerini almak
- İstemcinin IP'sine göre domain engelleme kurallarını kontrol etmek
- Engellenen domainler için yerel IP içeren DNS yanıtı oluşturmak
- Engellenmeyen istekleri DNS-over-HTTPS üzerinden çözümlemek
- DoH başarısız olduğunda TCP/53 üzerinden yapılandırılmış DNS sunucusuna fallback yapmak
- DNS isteklerini eşzamanlı olarak işlemek

### `proxy_module.py`

Projenin HTTP/HTTPS proxy katmanıdır.

Başlıca görevleri:

- İstemci bağlantılarını kabul etmek
- HTTP isteklerini analiz etmek
- Yetkisiz istemcilerin erişim/giriş akışını yönetmek
- Site engelleme kurallarını kontrol etmek
- Yetkili bağlantılarda trafik aktarımı yapmak
- HTTPS CONNECT bağlantılarında SNI bilgisini incelemek
- Trafik aktarımı sırasında yapılandırılmış hız limitlerini uygulamak

### `InfiniDB.py`

Projenin SQLite veritabanı katmanıdır.

Aşağıdakiler gibi verilerin saklanmasını ve yüklenmesini yönetir:

- Aktif oturumlar
- Yasaklı site kuralları
- Erişim logları

Ayrıca sistem başlarken kayıtlı bilgilerin çalışma belleğine yüklenmesini sağlar.

### `config.py`

Uygulamanın merkezi yapılandırma ve çalışma zamanı durumunu yönetir.

Şunlarla ilişkili yapılandırmaları ve durumları içerir/yönetir:

- IP ayarları
- DNS ayarları
- Proxy ayarları
- Oturumlar
- Site hedefleri
- Hız limitleri
- Canlı loglar
- Cihaz fingerprint bilgileri

### `wpad_module.py`

WPAD servisidir.

TCP 80 portunda küçük bir HTTP sunucusu çalıştırır ve istemcilere `FindProxyForURL` içeren PAC yapılandırması gönderir.

Proxy IP adresi ve port bilgisi proje yapılandırmasından dinamik olarak alınır.

### `templates.py`

Erişim/giriş arayüzünde kullanılan dinamik HTML çıktısını oluşturur.

### `auto_reloader.py`

Proje içerisindeki `.py`, `.js`, `.html` ve `.css` dosyalarını izler. Değişiklik olduğunda ilgili Python modüllerinin yeniden yüklenmesini sağlayarak hot-reload işlevi sunar.

---

## 🖥️ Yönetim Paneli

Yönetim paneli Flask tabanlıdır.

### `admin/app.py`

Yönetim panelinin giriş noktasıdır.

Görevleri:

- API blueprint'lerini kaydetmek
- Statik dosyaları sunmak
- Dashboard, veritabanı tarayıcısı ve cihaz yönetimi route'larını sağlamak
- Yönetim sunucusunu başlatmak

### API Route'ları

#### Yasaklama Yönetimi — `api_bans.py`

```text
POST   /admin/api/bans/add
DELETE /admin/api/bans/remove
```

IP/regex tabanlı engelleme kurallarının eklenmesi ve kaldırılması için kullanılır.

Kurallar önce veritabanına kaydedilir, ardından çalışma belleğindeki aktif yasak listesiyle senkronize edilir.

#### Veritabanı API'si — `api_db.py`

```text
GET /admin/api/db/tables
GET /admin/api/db/query/<table_name>
```

SQLite veritabanındaki tablo bilgilerine JSON üzerinden erişim sağlar.

Tablo sorgulama endpoint'i en fazla 100 kayıt döndürür.

#### Hız Yönetimi — `api_speed.py`

```text
POST /admin/api/speed/ip
POST /admin/api/speed/everyone
```

Cihaza özel ve genel bant genişliği limitlerini yönetmek için kullanılır.

Cihaza özel hız limitinin `0` yapılması özel limiti kaldırır.

#### Sistem ve Cihaz API'si — `api_system.py`

Aşağıdaki bilgileri ve işlemleri sağlar:

- Sistem durumu
- Aktif oturumlar
- Engelleme kuralları
- Özel/genel hız limitleri
- Canlı loglar
- Aktif cihazlar
- Hostname
- User-Agent
- Cihaz türü
- Fingerprint bilgileri
- Ping bilgileri
- Download/upload göstergeleri
- Hot-reload
- Oturum kapatma

---

## 🎨 Frontend

### `dashboard.html`

Yönetim panelinin ana dashboard sayfasıdır.

Şunları gösterir/yönetir:

- Sistem durumu
- Aktif oturumlar
- Engellenen hedefler
- Hız limitleri
- Canlı trafik/SNI bilgileri
- Cihaz envanteri
- InfiniDB tarayıcısı

### `devices.html`

Cihaz envanteri ve cihaz detay yönetimi arayüzüdür.

Cihazlarla ilgili:

- Fingerprint bilgileri
- Cihaz türü
- Fingerprint hash
- İlk görülme zamanı
- User-Agent
- Gerçek zamanlı ping
- Bant genişliği
- Trafik yönü

gibi verileri gösterir.

### `db_browser.html`

SQLite veritabanını web yönetim panelinden görüntülemek için kullanılır.

Backend API'den mevcut tabloları alır ve seçilen tablonun sütunlarını/kayıtlarını dinamik olarak gösterir.

### `dashboard.js`

Yönetim panelinin istemci tarafındaki ana JavaScript dosyasıdır.

Başlıca görevleri:

- Dashboard istatistiklerini güncellemek
- Aktif oturumları göstermek
- Engelleme kurallarını yönetmek
- Hız limitlerini yönetmek
- Canlı trafik verilerini güncellemek
- Cihaz listesini oluşturmak
- Cihaz detay modalını yönetmek
- Cihaz durumlarını periyodik olarak yenilemek
- Oturum kapatma isteklerini göndermek
- Ban işlemlerini göndermek
- Hız limiti işlemlerini göndermek
- Hot-reload işlemini tetiklemek

### `style.css`

Yönetim panelinin ana CSS dosyasıdır.

İçerisinde:

- Genel renk değişkenleri
- Sayfa düzeni
- Sidebar
- Dashboard istatistik kartları
- Grid/bölüm düzenleri
- Tablolar
- Form elemanları
- Butonlar
- Tehlike/başarı butonları
- Cihaz kartları
- Cihaz durum göstergeleri
- Cihaz detay modalı
- Modal sidebar ve sekmeleri

bulunur.

---

## 🔐 Güvenlik ve Etik Kullanım

InfiniNET bir **ağ yönetimi ve ağ yapılandırma aracı** olarak tasarlanmıştır.

Sistem yalnızca yöneticinin uygun yetkiye sahip olduğu ağlarda, sistemlerde ve cihazlarda kullanılmalıdır.

Bu yazılım; üçüncü kişilerin ağ trafiğini izleme, analiz etme, engelleme, yavaşlatma veya başka şekilde müdahale etme konusunda tek başına herhangi bir yasal yetki sağlamaz. Yazılımın kullanılmasından önce ilgili ağın sahibi veya yetkili yöneticisinden gerekli izinlerin alınması ve yürürlükteki mevzuata uyulması kullanıcının sorumluluğundadır.

### Önemli Uyarı

InfiniFunction ve katkıda bulunan geliştiriciler, yazılımın hukuka aykırı, yetkisiz veya kötüye kullanımını desteklemez veya teşvik etmez.

Yazılımın yetkisiz kullanımı sonucunda oluşabilecek:

- Yetkisiz erişim
- Gizlilik ihlali
- Kişisel/veri güvenliği ihlalleri
- Yetkisiz trafik izleme
- Hizmet kesintileri
- Ağda oluşabilecek zararlar
- Verilerin kötüye kullanılması
- Diğer hukuki, idari veya teknik sonuçlar

için InfiniFunction ve katkıda bulunanlar sorumluluk kabul etmez.

**InfiniNET yalnızca yetkili olduğunuz ve yönetim hakkına sahip olduğunuz ağlarda kullanılmalıdır.**

---

## 🔒 Gizlilik ve Veri Koruma / Aydınlatma Metni

InfiniNET içerisinde bulunan veritabanı ve izleme bileşenleri, Gateway olarak kullanılan cihaz üzerinde çalışır.

Yapılandırmaya bağlı olarak sistem aşağıdaki türde ağ yönetim verilerini işleyebilir:

- IP adresleri
- Oturum bilgileri
- Erişim zamanları
- Hostname bilgileri
- User-Agent bilgileri
- Cihaz/fingerprint bilgileri
- Domain veya trafik ile ilişkili kayıtlar
- Yönetim logları

Sistem yöneticisi; hangi verilerin toplandığından, hangi amaçla işlendiğinden, ne kadar süre saklandığından, kimlerin erişebildiğinden ve gerekli durumlarda kullanıcıların bilgilendirilmesi/izin süreçlerinden sorumludur.

Veritabanı yetkisiz erişime karşı korunmalı ve gerekli güvenlik önlemleri olmadan internet gibi güvenilmeyen ortamlara açılmamalıdır.

InfiniFunction ve katkıda bulunan geliştiriciler; verilerin sızması, veritabanına yetkisiz erişim, toplanan bilgilerin kötüye kullanılması veya sistemin mevzuata aykırı şekilde yapılandırılmasından kaynaklanan sonuçlardan sorumlu değildir.

**Gerçek bir ortamda kullanmadan önce bulunduğunuz ülke, kurum ve ağ ortamı için geçerli gizlilik, veri koruma ve ağ izleme yükümlülüklerini inceleyin.**

---

## ⚠️ Bilinen Hatalar ve Sınırlamalar

Proje geliştirme ortamında test edilmiş ve dokümantasyon hazırlanırken bilinen bir işlevsel sorun tespit edilmemiştir.

Bununla birlikte:

- Farklı ağ yapılandırmaları farklı sonuçlara neden olabilir.
- İşletim sistemi ayarları ağ bileşenlerini etkileyebilir.
- Güvenlik duvarı veya paket yakalama ayarları bazı özellikleri etkileyebilir.
- Bağımlılık veya çalışma ortamı değişiklikleri uyumluluk sorunları oluşturabilir.
- Uygulamanın dilinde, HTML dosyalarında, JavaScript dosyalarında, CSS dosyalarında veya başka kaynaklarda yapılan değişiklikler yeni hatalara neden olabilir.

Dil değişikliği veya başka bir kaynak dosyasına yapılan manuel müdahale sonucunda hata oluşursa, değişikliği yapan kişinin oluşan davranışı doğrulaması ve gerekli düzeltmeyi yapması gerekir.

Sorunun projenin kendisinden kaynaklandığı düşünülüyorsa GitHub üzerinde bir **Issue** açabilirsiniz.

Issue açarken mümkün olduğunca:

- İşletim sistemi
- Python sürümü
- Hata mesajı / terminal çıktısı
- Hatanın oluşma adımları
- Etkilenen dosya veya bileşen
- Paylaşılması güvenli olan ilgili yapılandırma bilgileri

eklenmelidir.

**Issue içerisinde şifre, özel ağ bilgileri, kişisel veriler veya hassas loglar paylaşmayın.**

---

## 🛠️ Geliştirme ve Test

InfiniNET birden fazla ağ servisini ve web tabanlı yönetim bileşenlerini aynı anda kullandığı için bir modüldeki değişiklik başka bir modülü etkileyebilir.

Değişikliklerden sonra en azından aşağıdaki bileşenlerin kontrol edilmesi önerilir:

- DHCP
- DNS
- Proxy
- Captive Portal
- Hız limitleri
- Site engelleme
- Cihaz tespiti
- Veritabanı işlemleri
- Yönetim API'leri
- Frontend güncellemeleri

---

## 📌 Gateway Yapılandırması

Proje için gerekli Gateway IP adresi:

```text
192.168.1.101
```

DHCP istemci IP aralığı:

```text
192.168.1.105 - 192.168.1.200
```

---

## 🤝 Katkıda Bulunma

Hata bildirimleri, geliştirmeler ve katkılar memnuniyetle karşılanır.

Pull Request gönderirken:

1. Değişiklikleri mümkün olduğunca ilgili alanla sınırlı tutun.
2. Alakasız dosyalarda gereksiz değişiklik yapmayın.
3. Etkilenen ağ bileşenlerini test edin.
4. Davranış değiştiren özellikleri belgeleyin.
5. Şifre, özel ağ bilgileri veya hassas log paylaşmayın.

---

## 🐛 Issue / Hata Bildirimi

Tekrarlanabilir hatalar, teknik problemler ve özellik talepleri için GitHub Issues kullanılabilir.

Güvenlik açısından hassas bir konu söz konusuysa, gizli bilgileri herkese açık Issue içerisinde paylaşmayın. Projede özel güvenlik bildirimi için belirlenmiş bir kanal bulunuyorsa onu kullanın.

---

## 📚 Dokümantasyon İçin Önemli Dosyalar

Projeyi anlamak için özellikle aşağıdaki dosyalar önemlidir:

- `InfiniDHCP.py` — ana başlatıcı
- `config.py` — merkezi yapılandırma ve çalışma durumu
- `dhcp_module.py` — DHCP servisi
- `dns_module.py` — DNS servisi
- `proxy_module.py` — HTTP/HTTPS proxy
- `InfiniDB.py` — SQLite veritabanı katmanı
- `wpad_module.py` — WPAD servisi
- `admin/` — yönetim paneli

---

## 🇬🇧 English Documentation

İngilizce dokümantasyon için:

**[README.md](README.md)**

---

## 📜 Sorumluluk Reddi

Bu yazılım; meşru ağ yönetimi, test, geliştirme ve eğitim amaçları için sunulmaktadır.

Geliştiriciler ve katkıda bulunanlar, yazılımın her ortam için uygun olduğunu garanti etmez ve yetkisiz kullanım, hukuka aykırı izleme, veri kötüye kullanımı, gizlilik ihlalleri, ağ kesintileri veya yazılımın kullanımından doğabilecek diğer sonuçlar konusunda sorumluluk kabul etmez.

**Yazılımın yasal, yetkili ve uygun şekilde kullanılmasından tamamen kullanıcı/operatör sorumludur.**
