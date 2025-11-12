from flask import Flask, render_template, request, redirect, url_for
from datetime import date, timedelta
import db

app = Flask(__name__)

# template format rupiah
@app.template_filter('rupiah')
def format_rupiah(value):
    return f"Rp {value:,.2f}".replace(",", ".").replace(".", ",", 1)

# untuk landing page-nya
@app.route('/')
def landing():
    return render_template('landing.html')

# --------------------------
# READ
# --------------------------
@app.route('/obat')
def daftar_obat():  
    obat_list = db.get_all_obat()
    now_date = date.today()

    # Cek obat yang kadaluarsa / hampir kadaluarsa (<=7 hari)
    alert_obat = []
    for o in obat_list:
        kadaluarsa = o[5]
        if kadaluarsa:
            selisih = (kadaluarsa - now_date).days
            if selisih < 0:
                alert_obat.append(f"❌ Obat '{o[1]}' sudah kadaluarsa!")
            elif selisih <= 7:
                alert_obat.append(f"⚠ Obat '{o[1]}' akan kadaluarsa dalam {selisih} hari!")
                
    return render_template(
        'index.html',
        obat_list=obat_list,
        now_date=now_date,
        alert_obat=alert_obat
    )


# --------------------------
# CREATE
# --------------------------
@app.route('/tambah', methods=['POST'])
def tambah_obat():
    nama = request.form['nama']
    kategori = request.form['kategori']
    stok = request.form['stok']
    harga = request.form['harga']
    tanggal_kadaluarsa = request.form['tanggal_kadaluarsa']

    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO obat (nama, kategori, stok, harga, tanggal_kadaluarsa)
        VALUES (%s, %s, %s, %s, %s)
    """, (nama, kategori, stok, harga, tanggal_kadaluarsa))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('daftar_obat'))

# --------------------------
# DELETE
# --------------------------
@app.route('/hapus/<int:id>', methods=['POST'])
def hapus_obat(id):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM obat WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('daftar_obat'))

# --------------------------
# UPDATE (2 langkah: tampilkan form edit + simpan hasil)
# --------------------------
@app.route('/edit/<int:id>')
def edit_obat(id):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM obat WHERE id = %s", (id,))
    obat = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit.html', obat=obat)

@app.route('/update/<int:id>', methods=['POST'])
def update_obat(id):
    nama = request.form['nama']
    kategori = request.form['kategori']
    stok = request.form['stok']
    harga = request.form['harga']
    tanggal_kadaluarsa = request.form['tanggal_kadaluarsa']

    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE obat
        SET nama = %s, kategori = %s, stok = %s, harga = %s, tanggal_kadaluarsa = %s
        WHERE id = %s
    """, (nama, kategori, stok, harga, tanggal_kadaluarsa, id))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('daftar_obat'))

if __name__ == '__main__':
    app.run(debug=True)
