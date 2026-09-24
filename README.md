# 10FastFingers Typing Bot

Selenium ve Playwright ile yerel klavye olayları gönderen eğitim projesi.
Türkçe karakterleri, eski input arayüzünü ve güncel parçalı kelime arayüzünü destekler.

## Kurulum

Python 3.9+ ve Chrome/Chromium gerekir. Depo dizininde:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[all]"
python -m playwright install chromium
```

Selenium kurulu Chrome'u Selenium Manager ile bulur. Playwright varsayılan olarak
kendi Chromium'unu kullanır. İkisine de `--browser-path` vererek aynı Chrome
sürümünü seçebilirsin.

## Kullanım

Sitenin sunduğu metni beklemesiz yazmak:

```bash
python playwright_bot.py --headless --strategy turbo --settle 0
python selenium_bot.py --headless --strategy turbo --settle 0
```

Güncel standart test **2.000 karaktere kadar metin** hazırlıyor. Bot bu metni
birkaç saniyede bitirebilir; bu, 60 saniyelik sonuç ekranının hazır olduğu anlamına
gelmez. Uzun süre giriş olmazsa sitenin AFK kontrolü testi sıfırlayabilir.
60 saniyeye yayılmış bir çalışma ve sonuç ekranı için:

```bash
python playwright_bot.py --headless --strategy turbo --wpm 400 --duration 60 --settle 3
python selenium_bot.py --headless --strategy turbo --wpm 400 --duration 60 --settle 3
```

`--wpm`, boşluklar dahil beş karakteri bir kelime kabul eden gönderim temposudur;
sitenin hesaplayacağı puanı garanti etmez. `0` (varsayılan) sınırsız hızdır.
Tarayıcıyı görmek için `--headless` yerine `--headful` kullan.

Yerel demo ve normal motor klavye API'si:

```bash
python playwright_bot.py --target demo --headful
python selenium_bot.py --target demo --strategy active --delay 0
```

## Sorun neydi?

- Güncel site `.word-box-active-word` yerine değişken `wb-…-aw` sınıfları ve
  `data-testid="word-box-words"` kullanıyor. Eski kod aktif kelimeyi bulamayınca
  kutunun ilk kelimesine dönüyordu; metin bitince de aynı hatayı yapıyordu.
- Sayaç, kabul edilen kelime yerine gönderme denemelerini sayıyordu. Binlerce
  deneme, binlerce doğru kelime veya WPM anlamına gelmiyordu.
- Playwright `active` modunda her kelimede tekrar tıklıyor; iki motor farklı
  gecikmeler, işlemler ve tarayıcılarla karşılaştırılıyordu.
- `keyboard.type()` US klavye eşlemesinde olmayan karakterler için yalnızca input
  olayı gönderir. Türkçe karakterlerde keydown bilgisi bekleyen sayfalarla bu
  farklılık önemlidir. `insert_text()` de tek başına çözüm değildir.
- WebSocket kullanılması tek başına daha yüksek hız sağlamaz. Mesaj sayısı,
  olayların içeriği ve sayfanın güncellenme hızı belirleyicidir.

Yeni `turbo`, **iki motorda da aynı doğrudan CDP WebSocket hattını** kullanır.
Bir kelimenin native keyDown/keyUp olaylarını sırayla yollar, bütün protokol
cevaplarını kontrol eder ve sonraki kelimeye geçmeden DOM ilerlemesini doğrular.
DOM okumak için JavaScript kullanır; metni DOM'a yazarak veya sayfanın skor/sayaç
verilerini değiştirerek sonuç üretmez. Hazır olmayan sayfayı bekler, ilerlemeyen
kelimeyi tekrar tekrar göndermez ve odağı başta bir kez alır.

`active`, motorların normal klavye yolunu korur. Playwright'ta Türkçe harflerin
native tuş olayları CDP ile tamamlanır. Karşılaştırırken `--delay 0` kullan.

## Sonuç ve seçenekler

```bash
python playwright_bot.py --headless --max-words 100 --settle 0 --json --screenshot outputs/result.png
```

- `--duration 60`: yazma döngüsünün süre sınırı; kurulum ve screenshot beklemesi hariç.
- `--max-words 10000`: kelime sınırı. Süre/limit kelime sınırlarında kontrol edilir;
  gönderilmekte olan en fazla bir kelime süreyi aşabilir.
- `--delay 0.02`: yalnızca `active` modda kelimeler arası ek bekleme.
- `--wpm 0`: opsiyonel karakter temelli tempo; `turbo` dahil iki modda çalışır.
- `--settle 3`: yazma sonrasında ekran görüntüsünden önce bekleme.
- `--browser-path PATH`: karşılaştırma için aynı Chrome çalıştırılabilir dosyası.
- `--target demo`: yerel demo; URL veya HTML dosya yolu da kabul edilir.
- `--json`: otomatik karşılaştırmalar için makinece okunabilir sonuç.

`Confirmed words` / JSON `typed_words`, gözlenen kelime ilerlemeleridir.
`Attempted words` gönderim sayısıdır. İkisi de sitenin doğru kelime sayısı veya
resmî WPM puanı yerine geçmez. `words_exhausted` sunulan metnin bittiğini,
`completed` demodaki gibi açık bir bitiş sinyalini belirtir. `stalled`,
`input_error` ve `unsupported_page` durumlarında süreç hata koduyla çıkar.
Sitenin DOM yapısı değişirse adapter güncellenmelidir; ilk kelimeye sessizce dönmez.

## Doğrulama

Ölçümler ve sınırlamalar: [BENCHMARKS.md](BENCHMARKS.md).

```bash
python -m unittest discover -s tests -v
python scripts/benchmark.py --browser-path "PATH/TO/chrome" --repeats 3
```

Tarayıcı entegrasyon testleri (PowerShell):

```powershell
$env:TYPING_BOT_BROWSER_TESTS = "1"
# İsteğe bağlı: $env:TYPING_BOT_BROWSER = "C:\path\to\chrome.exe"
python -m unittest discover -s tests -v
```

Linux/macOS: `TYPING_BOT_BROWSER_TESTS=1 python -m unittest discover -s tests -v`.
Testler Türkçe harfleri, tekrar eden kelimeleri, satır geri dönüşümünü, gecikmiş
render işlemlerini, metnin tükenmesini ve native olayları doğrular.

## Kaynaklar

- [Playwright Keyboard](https://playwright.dev/python/docs/api/class-keyboard)
- [Chrome DevTools Input](https://chromedevtools.github.io/devtools-protocol/tot/Input/)
- [Selenium Actions](https://www.selenium.dev/documentation/webdriver/actions_api/)
- [Güncel Türkçe test](https://10fastfingers.com/typing-test/turkish)

Eğitim ve izinli otomasyon çalışmaları içindir. MIT lisansı: [LICENSE](LICENSE).
