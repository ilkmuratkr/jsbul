# JS Yükleme Tespit Aracı (Playwright)

Bu araç, verilen URL listelerini gerçek tarayıcı motoru (headless) ile açarak ağ isteklerini dinler ve hedef domain(ler)e ait JavaScript dosyalarının yüklenip yüklenmediğini tespit eder. Varsayılan olarak `alexametrics.com` alan adını ve alt alanlarını kontrol eder.

## Özellikler

- 🔎 Gerçek tarayıcı (Chromium) ile ağ isteklerini dinleme
- 🧩 script, XHR/fetch ile `.js` istekleri ve DOM `script[src]` taraması
- 🎯 Hedef domain eşleşmesi (ana/alt alan adları)
- 📟 Canlı ilerleme logları (`--verbose`)
- 🕒 Ayarlanabilir timeout ve ek bekleme (`--timeout-ms`, `--extra-wait-ms`)
- 💾 Sonuçları sadece eşleşenler olacak şekilde JSON/CSV’ye yazma (`--out`, `--format`)

## Kurulum

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install --with-deps
```

## Girdi Dosyası

- `domain.txt` içinde her satır bir URL olmalı ve `http://` veya `https://` ile başlamalı.
- Örnek:
```
https://example.com
http://foo.bar
https://livesicilia.it
```

## Çalıştırma

Proje kökünde, sanal ortam aktifken:

```bash
python -m scanner.cli domain.txt 5 --out out/found.csv --format csv --verbose
```

Açıklamalar:
- `domain.txt`: URL listesi dosyası (göreli yol desteklenir)
- `5`: eşzamanlı tarama sayısı (concurrency)
- `--out out/found.csv`: sonuçları CSV olarak `out/` klasörüne yazar (klasör yoksa oluşturulur)
- `--format csv|json`: çıktı formatı
- `--verbose`: canlı ilerleme logları
- `--timeout-ms 40000`: sayfa yükleme zaman aşımı (ms)
- `--extra-wait-ms 3000`: `networkidle` sonrası ek bekleme (ms)

Örnek JSON çıktı komutu:
```bash
python -m scanner.cli domain.txt 10 --out out/found.json --format json --verbose
```

## Notlar

- Eşleşme ölçütü: İstek URL’sinin host’u hedef domain ile aynı veya onun alt alanı olmalıdır (örn. `cdn.alexametrics.com`).
- Çıktı dosyasına sadece eşleşme bulunan URL’ler yazılır. Eşleşme yoksa JSON boş dizi, CSV sadece başlık satırı içerir.
- Bazı siteler yavaş/engelleyici olabilir; `--timeout-ms` artırılabilir, `concurrency` düşürülebilir.

## Hedef Domaini Değiştirme

Varsayılan hedef `alexametrics.com`’dur. Değiştirmek için `scanner/cli.py` içindeki `TARGET_DOMAINS` setini düzenleyin:

```python
TARGET_DOMAINS = {"alexametrics.com"}
```

Çoklu domain desteği için set’e birden fazla alan adı ekleyebilirsiniz.
