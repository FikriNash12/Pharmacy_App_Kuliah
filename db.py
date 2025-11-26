import psycopg2
from datetime import date, timedelta

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="pharmacy_db",
        user="postgres",
        password="cemong2005"  # ganti dengan password PostgreSQL kamu
    )

def get_all_obat(search_term=None, kategori=None):
    conn = get_connection()
    cur = conn.cursor()
    
    # Query dasar
    base_query = """
        SELECT id, nama, kategori, stok, harga, tanggal_kadaluarsa
        FROM obat
    """
    
    # Kumpulan kondisi WHERE
    where_clauses = []
    params = [] # List untuk menampung parameter (anti SQL Injection)
    
    # 1. Tambahkan kondisi NAMA (search)
    if search_term:
        where_clauses.append("nama ILIKE %s")
        params.append(f"%{search_term}%") # %...% untuk "mengandung"
        # ILIKE = case-insensitive (tidak peduli huruf besar/kecil)
        
    # 2. Tambahkan kondisi KATEGORI (filter)
    if kategori:
        where_clauses.append("kategori = %s")
        params.append(kategori)
        
    # Gabungkan semua kondisi WHERE jika ada
    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
        
    # Tambahkan ORDER BY di akhir
    base_query += " ORDER BY id ASC;"
    
    # Eksekusi query dengan parameter yang aman
    cur.execute(base_query, tuple(params))
    
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def create_user(username, password_hash):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error: {e}")
    finally:
        cur.close()
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    return user_data

def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    return user_data

def add_log(username, aksi, deskripsi):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO riwayat (username, aksi, deskripsi)
            VALUES (%s, %s, %s)
        """, (username, aksi, deskripsi))
        conn.commit()
    except Exception as e:
        print(f"Gagal mencatat log: {e}")
        # Jangan rollback/error fatal cuma gara-gara log gagal, biarkan aplikasi jalan
    finally:
        cur.close()
        conn.close()

def get_all_riwayat():
    conn = get_connection()
    cur = conn.cursor()
    # Ambil data diurutkan dari yang paling baru
    cur.execute("SELECT * FROM riwayat ORDER BY waktu DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data