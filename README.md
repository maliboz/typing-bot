# 10FastFingers Typing Bot

10FastFingers icin Selenium ve Playwright tabanli hizli typing bot ornegi.

Bu projenin amaci sahte bir "typing coach" yapmak degil; gercek bir web
otomasyonu ornegi uzerinden, selector takibi, browser automation, hiz
optimizasyonu ve Selenium/Playwright farkini gostermektir.

Eski 10FastFingers arayuzunde site `#inputfield` ve `span[wordnr]` kullaniyordu.
Yeni arayuzde ayri input yok; aktif kelime `.word-box-active-word` sinifindan
okunuyor ve tuslar dogrudan sayfaya gonderiliyor. Kod iki yapinin ikisini de
destekler.

## Verified 60-Second Results

These runs were executed against the real Turkish 10FastFingers test page on
2026-05-28.

| Engine | Command profile | Site result | Accuracy | Screenshot |
| --- | --- | ---: | ---: | --- |
| Selenium | `--strategy turbo --max-words 10000 --duration 60` | 400 dks | 100% | [view](docs/assets/selenium-turbo-400wpm-100acc.png) |
| Playwright stable | `--strategy active --delay 0.005 --duration 60` | 362 wpm | 100% | [view](docs/assets/playwright-stable-362wpm-100acc.png) |
| Playwright aggressive | `--strategy turbo --duration 60` | 353 wpm | 95% | [view](docs/assets/playwright-aggressive-353wpm-95acc.png) |

![Selenium 400 dks 100% result](docs/assets/selenium-turbo-400wpm-100acc.png)

Full benchmark notes are in [BENCHMARKS.md](BENCHMARKS.md).

## En Hizli Kullanim

Selenium:

```bash
python -m pip install selenium
python selenium_bot.py --headless --strategy turbo --max-words 400 --duration 60 --settle 10
```

Gorunur tarayici ile izlemek icin:

```bash
python selenium_bot.py --headful --strategy turbo --max-words 400 --duration 60
```

Playwright:

```bash
python -m pip install playwright
playwright install chromium
python playwright_bot.py --headless --strategy active --delay 0.005 --max-words 10000 --duration 60 --settle 12
```

## Stratejiler

- `--strategy turbo`: en hizli calisan mod. Yeni sitede aktif kelimeyi okuyup
  sifir beklemeyle basar. Eski input tabanli sitede kelime listesini bulk
  gonderebilir.
- `--strategy active`: derste gostermek ve debug yapmak icin daha okunur mod.
  Kelime kelime gider, `--delay` ile yavaslatilabilir.

Playwright icin en iyi dogruluk/hiz dengesi su ana kadar:

```bash
python playwright_bot.py --headless --strategy active --delay 0.005 --duration 60 --settle 12
```

Ornek:

```bash
python selenium_bot.py --headful --strategy active --delay 0.03
```

## Parametreler

```bash
python selenium_bot.py --strategy turbo --max-words 400 --duration 60 --screenshot final_result.png
```

- `--headful`: gorunur tarayici penceresi acar
- `--headless`: arka planda calistirir
- `--strategy turbo`: hiz odakli mod
- `--strategy active`: kelime kelime takip modu
- `--max-words 400`: yazilacak maksimum kelime sayisi
- `--duration 60`: maksimum calisma suresi
- `--delay 0.02`: sadece `active` modda kelimeler arasi bekleme
- `--settle 10`: ekran goruntusunden once bekleme suresi
- `--screenshot final_result.png`: sonuc ekran goruntusu
- `--target 10fastfingers-tr`: varsayilan gercek site hedefi
- `--target demo`: internetsiz yerel demo sayfasi

## Neden Iki Bot Var?

Selenium, derslerde anlatmasi kolay olan klasik WebDriver ornegidir.

Playwright ise hiz denemeleri icin daha uygundur; browser ile daha dusuk
overhead'li bir automation protokolu uzerinden konusur ve klavye eventlerini
cok daha seri gonderebilir. Bu yuzden proje ikisini de icerir.

## Guncel Site Desteği

Kod once eski arayuzu kontrol eder:

```text
#inputfield
span[wordnr="0"]
span[wordnr="1"]
```

Bulamazsa yeni arayuze gecer:

```text
.word-box-active-word
div[class*="word-box"]
```

Bu sayede eski kodun kirildigi ana problem, yani 10FastFingers'in DOM yapisini
degistirmesi, giderilmis olur.

## Yerel Demo

Internet yoksa veya derste kontrollu gosterim yapmak istersen:

```bash
python selenium_bot.py --headful --target demo
```

Ana hedef yine gercek 10FastFingers sitesidir; demo sadece fallback icindir.

## Test

```bash
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

macOS/Linux:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Not

Bu proje Selenium ve Playwright otomasyon mantigini ogretmek icin hazirlanmistir.
Ucuncu taraf sitelerde kullanirken ilgili sitenin kurallarina ve aldigin
izinlere uygun hareket et.

## License

MIT. See [LICENSE](LICENSE).
