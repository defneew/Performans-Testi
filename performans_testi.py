import psycopg2
import psutil
import time
import matplotlib.pyplot as plt
import numpy as np

# CPU ve RAM kullanımını sorgu boyunca ölçen fonksiyon
def measure_cpu_ram():
    # 1 saniye boyunca ortalama CPU kullanımı ve RAM kullanım yüzdesi
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    return cpu, ram

# Belirli sunucuda sorgu çalıştırma fonksiyonu
def run_query(query, db_config):
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute(query)
        cur.fetchall()
        cur.close()
        conn.close()
        return None
    except Exception as e:
        return f"Hata: {e}"

# Ortalama performans ölçümü (zaman + cpu% + ram%) 3 kez çalıştırılıp ortalama alınır
def average_query_performance(conn_info, query, runs=3):
    times = []
    cpus = []
    rams = []

    print(f"\n[INFO] Sorgu test ediliyor: {query.strip()}")

    for run in range(1, runs + 1):
        print(f"  → Deneme {run}/{runs}")

        # Cache etkisini azaltmak için ısındırma
        run_query(query, conn_info)
        time.sleep(0.3)

        # Ölçüm başlangıcı
        start_time = time.time()

        # Sorgu çalıştır
        err = run_query(query, conn_info)
        if err:
            print(err)
            return None

        # Ölçüm bitişi
        duration = (time.time() - start_time) * 1000  # ms

        # Kaynak kullanımı ölçümü
        cpu, ram = measure_cpu_ram()

        print(f"    → Süre (ms): {duration:.3f}")
        print(f"    → CPU kullanımı (%): {cpu:.2f}")
        print(f"    → RAM kullanımı (%): {ram:.2f}")

        times.append(duration)
        cpus.append(cpu)
        rams.append(ram)

    result = {
        "sorgu": query,
        "süre_ms": sum(times) / runs,
        "cpu_percent": sum(cpus) / runs,
        "ram_percent": sum(rams) / runs
    }
    print(f"[RESULT] Ortalama: süre={result['süre_ms']:.3f} ms, cpu={result['cpu_percent']:.2f} %, ram={result['ram_percent']:.2f} %")
    return result

# Sunucu bağlantıları
server_A = {
    "host": "192.168.235.133",
    "port": 5432,
    "database": "db_person",
    "user": "postgres",
    "password": "123"
}

server_B = {
    "host": "192.168.235.134",
    "port": 5432,
    "database": "db_person",
    "user": "postgres",
    "password": "123"
}

# Sadece tek bir sorgu için test yapacak fonksiyon
def test_single_query(query, servers):
    results = []
    for server_info, server_name in servers:
        result = average_query_performance(server_info, query)
        if result:
            result["sunucu"] = server_name
            results.append(result)
    return results

# Grafik çizim fonksiyonu
def plot_results(results):
    unique_queries = list(set(result["sorgu"] for result in results if result))
    unique_queries.sort()

    for query in unique_queries:
        data = [r for r in results if r and r["sorgu"] == query]
        labels = [d["sunucu"] for d in data]
        duration_values = [d["süre_ms"] for d in data]
        cpu_values = [d["cpu_percent"] for d in data]
        ram_values = [d["ram_percent"] for d in data]

        print(f"\nSorgu: {query.strip()[:60]}...")

        # Bar chart for duration
        plt.figure(figsize=(6, 4))
        plt.bar(labels, duration_values, color=["green", "red"])
        plt.title(f"Süre (ms) - Sorgu: {query[:40]}...")
        plt.ylabel("Süre (ms)")
        plt.xlabel("Sunucu")
        plt.tight_layout()
        plt.show()

        # Line chart for CPU usage
        plt.figure(figsize=(6, 4))
        x = np.arange(len(labels))
        plt.plot(x, cpu_values, marker='o', label="CPU Kullanımı (%)", color='blue')
        plt.xticks(x, labels)
        plt.title(f"CPU Kullanımı (%) - Sorgu: {query[:40]}...")
        plt.ylabel("CPU Kullanımı (%)")
        plt.xlabel("Sunucu")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        # Line chart for RAM usage
        plt.figure(figsize=(6, 4))
        plt.plot(x, ram_values, marker='o', label="RAM Kullanımı (%)", color='orange')
        plt.xticks(x, labels)
        plt.title(f"RAM Kullanımı (%) - Sorgu: {query[:40]}...")
        plt.ylabel("RAM Kullanımı (%)")
        plt.xlabel("Sunucu")
        plt.grid(True)
        plt.tight_layout()
        plt.show()



# Test edilecek sorgular
query1 = "SELECT * FROM kullanicilar WHERE id = 172;"
query2 = "SELECT * FROM kullanicilar WHERE eposta = 'user_b76abc58@example.com';"
query3 = "SELECT * FROM kullanicilar WHERE dogum_tarihi BETWEEN '2001-07-13' AND '2024-07-13';"
query4 = "SELECT surname, COUNT(*) AS kisi_sayisi FROM kullanicilar GROUP BY surname ORDER BY surname DESC;"

# Test edilecek sunucular ve isimleri
servers = [
    (server_A, "Doğru Yapılandırma"),
    (server_B, "Yanlış Yapılandırma")
]

# İstediğin sorguyu çaıştır
test_results = test_single_query(query3, servers)

# Grafik çiz
plot_results(test_results)
