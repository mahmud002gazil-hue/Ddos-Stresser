Stresser Layer 7
💻 Kullanım Senaryoları (Terminal Komutları)
​1. Standart GET Stress Testi
​Hedef sayfaya 2000 isteği, aynı anda 200 farklı hattan (worker) göndererek L7 yükü oluşturur

2. Veri Tabanını Zorlayacak POST Stress Testi (Login/Search Yoğunluklu)
​Özellikle veri tabanı sorgusu tetikleyen uç noktaları (endpoint) yormak için POST isteği ve body verisi gönderebilirsiniz

pip install aiohttp

python l7_stresser.py -url https://example.com/ -n 2000 -c 200

python l7_stresser.py -url https://example.com/login -m POST -d "user=admin&pass=123" -n 1000 -c 100
