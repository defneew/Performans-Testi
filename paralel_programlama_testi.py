import psycopg2
from concurrent.futures import ThreadPoolExecutor
import time
import psutil
import matplotlib.pyplot as plt
from tabulate import tabulate

# Sunucu bilgileri
DB_CONFIGS = {
    'server_A': {
        "host": "192.168.235.133",
        "port": 5432,
        "database": "db_person",
        "user": "postgres",
        "password": "123"
    },
    'server_B': {
        "host": "192.168.235.134",
        "port": 5432,
        "database": "db_person",
        "user": "postgres",
        "password": "123"
    }
}

# Sorgu boyunca kaynak kullanımı
def measure_cpu_ram():
    return psutil.cpu_percent(1), psutil.virtual_memory().percent

# Belirli sunucuda belirli id ye göre sorgu çalıştırma fonksiyonu
def run_query(user_id, db_config):
    try:
        conn = psycopg2.connect(**db_config) #Database bağlantısı 
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM kullanicilar WHERE id = {user_id}") #Sorguyu çalıştır
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result
    except Exception as e:
        return f"Hata: {e}"

# Sıralı veya paralel çalışma için sorgu çalıştırma
def run_test(test_type, ids, db_config):
    start_time = time.time() # Başlangıç zamanı 
    cpu_usages = []
    ram_usages = []

    if test_type == "sequential": # Sıralı çalışma için kod bloğu
        for user_id in ids:
            run_query(user_id, db_config) # Sorgu çalışma fonksiyonunu çağır
            cpu, ram = measure_cpu_ram() # Kaynak kullanımını ölç
            cpu_usages.append(cpu) # Listeye cpu değerini ekle
            ram_usages.append(ram) # Listeye ram değerini ekle
    elif test_type == "parallel": # Paralel çalışma için kod bloğu
        with ThreadPoolExecutor(max_workers=len(ids)) as executor:
            results = list(executor.map(lambda user_id: run_query(user_id, db_config), ids)) # Paralel programlama için sorgu çalışma fonksiyonunu çağır
            for _ in results:
                cpu, ram = measure_cpu_ram() # Kaynak kullanımını ölç
                cpu_usages.append(cpu) # Listeye cpu değerini ekle
                ram_usages.append(ram) # Listeye ram değerini ekle

    # Sorgu sonunda zamanı ölç ve toplam zamanı hesapla
    total_time = time.time() - start_time
    return total_time, cpu_usages, ram_usages 

# cpu ve ram karşılaştırmaları için grafik oluşturma fonksiyonu
def plot_line_chart(data1, data2, label1, label2, title, ylabel, filename):
    plt.figure(figsize=(10, 6))
    plt.plot(data1, label=label1, marker='o')
    plt.plot(data2, label=label2, marker='x')

    for i, val in enumerate(data1):
        plt.text(i, val, f"{val:.1f}", ha='center', va='bottom', fontsize=8, rotation=45)
    for i, val in enumerate(data2):
        plt.text(i, val, f"{val:.1f}", ha='center', va='bottom', fontsize=8, rotation=45)

    plt.title(title)
    plt.xlabel("İşlem Adımı")
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# Süre karşılaştırmaları için grafik oluşturma fonksiyonu
def plot_bar_chart(val1, val2, label1, label2, title, ylabel, filename):
    plt.figure(figsize=(6, 6))
    bars = plt.bar([0, 1], [val1, val2], tick_label=[label1, label2], color=['skyblue', 'salmon'])

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, f'{height:.2f}', ha='center', va='bottom', fontsize=10, rotation=0)

    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# Sorgulanmak istenen id değerleri listesi
ids = [11,15,18,165,172,286,765,342,124,7] 
metrics = {}

# Her sunucu için sıralı ve paralel programlama testlerini yap.
for server_name, config in DB_CONFIGS.items():
    print(f"{server_name} - Sıralı test başlıyor...")
    seq_time, cpu_seq, ram_seq = run_test("sequential", ids, config)

    print(f"{server_name} - Paralel test başlıyor...")
    par_time, cpu_par, ram_par = run_test("parallel", ids, config)

    # Her server için bilgileri dictionary de tut.
    metrics[server_name] = {
        'seq_time': seq_time,
        'par_time': par_time,
        'cpu_seq': cpu_seq,
        'cpu_par': cpu_par,
        'ram_seq': ram_seq,
        'ram_par': ram_par
    }

# Sunucu ve programlama türlerine göre süre karşılaştırmaları için grafik fonksyonunun parametrelerini belirle.
bar_charts = [
    (metrics['server_A']['seq_time'], metrics['server_A']['par_time'], "Sıralı", "Paralel", "Doğru Sunucu: Sıralı vs Paralel Zaman", "Süre (saniye)", "dogru_sunucu_time_seq_vs_par.png"),
    (metrics['server_B']['seq_time'], metrics['server_B']['par_time'], "Sıralı", "Paralel", "Yanlış Sunucu: Sıralı vs Paralel Zaman", "Süre (saniye)", "yanlis_sunucu_time_seq_vs_par.png"),
    (metrics['server_A']['seq_time'], metrics['server_B']['seq_time'], "Doğru Sunucu", "Yanlış Sunucu", "Sıralı: Doğru vs Yanlış Sunucu", "Süre (saniye)", "seq_time_dogru_vs_yanlis.png"),
    (metrics['server_A']['par_time'], metrics['server_B']['par_time'], "Doğru Sunucu", "Yanlış Sunucu", "Paralel: Doğru vs Yanlış Sunucu", "Süre (saniye)", "par_time_dogru_vs_yanlis.png")
]

# Sunucu ve programlama türlerine göre ram ve cpu karşılaştırmaları için grafik fonksyonunun parametrelerini belirle.
line_charts = [
    (metrics['server_A']['cpu_seq'], metrics['server_A']['cpu_par'], "Sıralı", "Paralel", "Doğru Sunucu: CPU Kullanımı", "% CPU", "dogru_sunucu_cpu_seq_vs_par.png"),
    (metrics['server_B']['cpu_seq'], metrics['server_B']['cpu_par'], "Sıralı", "Paralel", "Yanlış Sunucu: CPU Kullanımı", "% CPU", "yanlis_sunucu_cpu_seq_vs_par.png"),
    (metrics['server_A']['cpu_seq'], metrics['server_B']['cpu_seq'], "Doğru Sunucu", "Yanlış Sunucu", "Sıralı CPU Karşılaştırması", "% CPU", "cpu_seq_dogru_vs_yanlis.png"),
    (metrics['server_A']['cpu_par'], metrics['server_B']['cpu_par'], "Doğru Sunucu", "Yanlış Sunucu", "Paralel CPU Karşılaştırması", "% CPU", "cpu_par_dogru_vs_yanlis.png"),

    (metrics['server_A']['ram_seq'], metrics['server_A']['ram_par'], "Sıralı", "Paralel", "Doğru Sunucu: RAM Kullanımı", "% RAM", "dogru_sunucu_ram_seq_vs_par.png"),
    (metrics['server_B']['ram_seq'], metrics['server_B']['ram_par'], "Sıralı", "Paralel", "Yanlış Sunucu: RAM Kullanımı", "% RAM", "yanlis_sunucu_ram_seq_vs_par.png"),
    (metrics['server_A']['ram_seq'], metrics['server_B']['ram_seq'], "Doğru Sunucu", "Yanlış Sunucu", "Sıralı RAM Karşılaştırması", "% RAM", "ram_seq_dogru_vs_yanlis.png"),
    (metrics['server_A']['ram_par'], metrics['server_B']['ram_par'], "Doğru Sunucu", "Yanlış Sunucu", "Paralel RAM Karşılaştırması", "% RAM", "ram_par_dogru_vs_yanlis.png")
]

# Grafik fonksiyonlarını parametreler için çağır.
for args in bar_charts:
    plot_bar_chart(*args)

for args in line_charts:
    plot_line_chart(*args)

# Benchmark tablosu oluşturma
headers = ["Metrik", "Sıralı", "Paralel"]
for sunucu, data in metrics.items():
    rows = [
        ["Süre (s)", round(data['seq_time'], 2), round(data['par_time'], 2)],
        ["CPU Kullanımı (%)", round(sum(data['cpu_seq']) / len(data['cpu_seq']), 2), round(sum(data['cpu_par']) / len(data['cpu_par']), 2)],
        ["RAM Kullanımı (%)", round(sum(data['ram_seq']) / len(data['ram_seq']), 2), round(sum(data['ram_par']) / len(data['ram_par']), 2)]
    ]
    print(f"\n{sunucu}")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
