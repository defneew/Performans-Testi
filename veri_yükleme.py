import psycopg2

#sunucuA bilgileri
server_A = {
    "host": "192.168.235.133",
    "port": 5432,
    "database": "db_person",
    "user": "postgres",
    "password": "123"
}

#sunucuB bilgileri
server_B = {
    "host": "192.168.235.134",
    "port": 5432,
    "database": "db_person",
    "user": "postgres",
    "password": "123"
}

#Tablo oluşturma sorgusu
create_table = """
DROP TABLE IF EXISTS kullanicilar;
CREATE TABLE kullanicilar (
    id SERIAL PRIMARY KEY,
    name TEXT,
    surname TEXT,
    eposta TEXT,
    dogum_tarihi DATE,
    olusturma_zamani TIMESTAMP
);
"""
#Dummy data ekleme sorgusu
insert_data = """
INSERT INTO kullanicilar (name, surname, eposta, dogum_tarihi, olusturma_zamani)
SELECT 
    'Name_' || substr(md5(random()::text), 1, 5), 
    'Surname_' || substr(md5(random()::text), 1, 5), 
    'user_' || substr(md5(random()::text), 1, 8) || '@example.com', 
    (CURRENT_DATE - (floor(random() * 365)) * INTERVAL '1 day')::date, 
    (now() - (floor(random() * 1000)) * INTERVAL '1 minute')::timestamp 
FROM generate_series(1, 10000000); 
"""
#Database ler için tablo oluşturma ve veri yükleme işlemleri için ortak fonksiyon
def setup_database(conn_info):
    try:
        conn = psycopg2.connect(**conn_info)
        cur = conn.cursor()
        print(f"{conn_info['host']} sunucusuna bağlandı.")

        cur.execute(create_table) #Tablo oluşturma sorgusu çalıştır
        conn.commit()
        print("Tablo oluşturuldu.")

        cur.execute(insert_data) #Veri ekleme sorgusu çalıştır
        conn.commit()
        print("Veri başarıyla eklendi.")

        cur.close()
        conn.close()
        print(f"{conn_info['host']} sunucusuyla işlem tamamlandı.\n")
    except Exception as e:
        print(f"Hata oluştu: {e}")

#Her iki sunucu için fonksiyonu çağır.
for server in [server_A, server_B]:
    setup_database(server)
