# Passwd Parser

Bu script, belirtilen URL'den `/etc/passwd` dosyasını çeker ve düzenli bir formatta gösterir.

## Özellikler

- 🔍 URL'den JSON formatında passwd verilerini çeker
- 📋 Kullanıcı bilgilerini tablo formatında gösterir
- 📊 Shell dağılımı ve kullanıcı kategorileri özeti
- 🔑 Giriş yapabilen kullanıcıları listeler
- ⚡ Hata yönetimi ve güvenli veri işleme

## Kurulum

1. Virtual environment oluşturun:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

## Kullanım

```bash
source venv/bin/activate
python passwd_parser.py
```

## Çıktı Formatı

Script şu bilgileri gösterir:
- Kullanıcı adı
- Şifre alanı (genellikle 'x')
- UID (User ID)
- GID (Group ID)
- Açıklama
- Ana dizin
- Shell

## Özet Bilgiler

- Shell dağılımı
- Sistem vs normal kullanıcı sayıları
- Giriş yapabilen kullanıcıların listesi

## Güvenlik Notu

Bu script sadece eğitim amaçlıdır. Gerçek sistemlerde `/etc/passwd` dosyasına erişim güvenlik riski oluşturabilir.
