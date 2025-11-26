from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import db

app = Flask(__name__)

# Secret Key
app.config['SECRET_KEY'] = 'Test_Aja_123'

# Flask Login Configure
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
login_manager.login_message = 'Harap login untuk mengakses halaman ini.'
login_manager.login_message_category = 'warning' 

# --- Model User untuk Flask-Login ---
# Class ini memberitahu Flask-Login cara menangani data user
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    @staticmethod
    def get(user_id):
        # Mengambil data user dari DB berdasarkan ID
        user_data = db.get_user_by_id(user_id)
        if not user_data:
            return None
        # (id, username, password_hash)
        return User(user_data[0], user_data[1], user_data[2])
    
    @staticmethod
    def get_by_username(username):
        # Mengambil data user dari DB berdasarkan username
        user_data = db.get_user_by_username(username)
        if not user_data:
            return None
        # (id, username, password_hash)
        return User(user_data[0], user_data[1], user_data[2])

# Callback yang digunakan Flask-Login untuk reload user dari session
@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

# --- Filter Template ---
@app.template_filter('rupiah')
def format_rupiah(value):
    return f"Rp {value:,.2f}".replace(",", ".").replace(".", ",", 1)

# --------------------------
# ROUTE OTENTIKASI (BARU)
# --------------------------

@app.route('/')
def landing():
    # Jika user sudah login, langsung lempar ke halaman obat
    if current_user.is_authenticated:
         return redirect(url_for('daftar_obat'))
    return render_template('landing.html') #

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('daftar_obat'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Cek apakah username sudah ada
        if User.get_by_username(username):
            flash('Username sudah digunakan.', 'danger')
            return redirect(url_for('register'))
            
        # Buat hash password dan simpan user baru
        password_hash = generate_password_hash(password)
        db.create_user(username, password_hash)
        
        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('daftar_obat'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
        
        # Cek apakah username ada dan password cocok
        if not user or not check_password_hash(user.password_hash, password):
            flash('Username atau password salah.', 'danger')
            return redirect(url_for('login'))
            
        # Jika lolos, loginkan user
        login_user(user, remember=True)
        return redirect(url_for('daftar_obat'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required # Hanya bisa diakses jika sudah login
def logout():
    logout_user()
    return redirect(url_for('landing'))


# --------------------------
# ROUTE CRUD OBAT
# --------------------------

# --------------------------
# READ
# --------------------------
@app.route('/obat')
@login_required # <-- DILINDUNGI!
def daftar_obat():
    search_term = request.args.get('search', None)
    kategori_filter = request.args.get('kategori', None)  
    
    obat_list = db.get_all_obat(search_term, kategori_filter)
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
@login_required # <-- DILINDUNGI!
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
    
    db.add_log(current_user.username, 'Tambah Obat', f"Menambahkan obat baru: {nama}")
    
    return redirect(url_for('daftar_obat'))

# --------------------------
# DELETE
# --------------------------
@app.route('/hapus/<int:id>', methods=['POST'])
@login_required 
def hapus_obat(id):
    conn = db.get_connection()
    cur = conn.cursor()
    
    # 1. AMBIL NAMA OBAT 
    cur.execute("SELECT nama FROM obat WHERE id = %s", (id,))
    data_obat = cur.fetchone()
    
    # Jika Obatnya tidak ada
    nama_obat = data_obat[0] if data_obat else "Obat Tidak Dikenal"

    # 2. LAKUKAN HAPUS
    cur.execute("DELETE FROM obat WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    # 3. CATAT KE RIWAYAT
    db.add_log(current_user.username, 'Hapus Obat', f"Menghapus obat: {nama_obat}")

    return redirect(url_for('daftar_obat'))

# --------------------------
# UPDATE (2 langkah)
# --------------------------
@app.route('/edit/<int:id>')
@login_required # <-- DILINDUNGI!
def edit_obat(id):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM obat WHERE id = %s", (id,))
    obat = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('edit.html', obat=obat) #

@app.route('/update/<int:id>', methods=['POST'])
@login_required # <-- DILINDUNGI!
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
    
    db.add_log(current_user.username, 'Edit Obat', f"Mengubah data obat: {nama}")

    return redirect(url_for('daftar_obat'))

# --------------------------
# RIWAYAT
# --------------------------
@app.route('/riwayat')
@login_required
def halaman_riwayat():
    logs = db.get_all_riwayat()
    return render_template('riwayat.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True)