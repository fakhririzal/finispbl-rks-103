from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import re
import smtplib
from email.mime.text import MIMEText
from itsdangerous import URLSafeTimedSerializer
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Ganti dengan secret key Anda
socketio = SocketIO(app, cors_allowed_origins="*")

# Dictionary untuk menyimpan room dan user
rooms = {}

# Halaman utama
@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Koneksi ke database
        connection = get_db_connection()
        if connection is None:
            return render_template('login.html', error="Gagal terhubung ke database!")

        cursor = connection.cursor()
        
        try:
            # Query untuk mengambil data pengguna berdasarkan username
            cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()  # Ambil satu hasil (username yang cocok)
            
            if result:
                stored_password = result[0]
                # Memverifikasi password dengan hash yang ada di database
                if check_password_hash(stored_password, password):  # Gunakan check_password_hash
                    session['username'] = username
                    return redirect(url_for('dashboard'))
                else:
                    return render_template('login.html', error="Password salah!")
            else:
                return render_template('login.html', error="Username tidak ditemukan!")
        except Exception as e:
            return render_template('login.html', error=f"Terjadi kesalahan: {e}")
        finally:
            cursor.close()
            connection.close()

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    print("Dashboard function called")
    return render_template('dashboard.html')

# Halaman chat
@app.route('/templates')
def chat():
    return render_template('chat.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Validasi password
        password_regex = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(password_regex, password):
            return render_template(
                'register.html',
                error="Password harus memiliki minimal 8 karakter, termasuk huruf besar, huruf kecil, angka, dan simbol."
            )

        # Koneksi ke database
        connection = get_db_connection()
        if connection is None:
            return render_template(
                'register.html',
                error="Gagal terhubung ke database!"
            )

        cursor = connection.cursor()

        try:
            # Hash password sebelum menyimpan
            hashed_password = generate_password_hash(password)

            # Query untuk memasukkan data pengguna baru
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            connection.commit()

            # Jika berhasil, arahkan ke form login dengan pesan sukses
            success_message = "Registrasi berhasil! Silakan login."
            return redirect(url_for('login', success=success_message))
        except mysql.connector.IntegrityError:
            # Jika username/email sudah terdaftar
            return render_template(
                'register.html',
                error="Username atau email sudah terdaftar!"
            )
        except Exception as e:
            return render_template(
                'register.html',
                error=f"Terjadi kesalahan: {e}"
            )
        finally:
            cursor.close()
            connection.close()

    # Render halaman register jika metode GET
    return render_template('register.html')




VALID_CODE = ['Sirius', 'Canopus', 'Alpha', 'Centauri', 'Arcturus', 'Vega', 'Andromeda', 'Aquarius', 'Aquila', 'Capella', 'Rigel', 'Procyon']

# Konfigurasi email
EMAIL_HOST = 'smtp.gmail.com'  # Ganti sesuai dengan server SMTP Anda
EMAIL_PORT = 587
EMAIL_USER = 'your_email@gmail.com'  # Ganti dengan email Anda
EMAIL_PASS = 'your_email_password'  # Ganti dengan password email Anda

# Serializer untuk token
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Forgot Password - Form Input Email
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Koneksi ke database
        connection = get_db_connection()
        if connection is None:
            return render_template('forgot_password.html', error="Gagal terhubung ke database!")

        cursor = connection.cursor()
        try:
            # Periksa apakah email ada di database
            cursor.execute("SELECT username FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()

            if result:
                username = result[0]
                # Buat token untuk reset password
                token = serializer.dumps(email, salt='password-reset-salt')
                reset_url = url_for('reset_password', token=token, _external=True)

                # Kirim email dengan tautan reset password
                subject = "Reset Password Anda"
                body = f"Hello {username},\n\nKlik tautan berikut untuk mengatur ulang password Anda:\n{reset_url}\n\nJika Anda tidak meminta ini, abaikan email ini."
                send_email(email, subject, body)

                return render_template('forgot_password.html', success="Tautan reset password telah dikirim ke email Anda.")
            else:
                return render_template('forgot_password.html', error="Email tidak ditemukan!")
        except Exception as e:
            return render_template('forgot_password.html', error=f"Terjadi kesalahan: {e}")
        finally:
            cursor.close()
            connection.close()

    return render_template('forgot_password.html')

# Reset Password - Form Input Password Baru
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Verifikasi token
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)  # Token berlaku 1 jam
    except Exception as e:
        return render_template('reset_password.html', error="Tautan reset password tidak valid atau sudah kadaluarsa!")

    if request.method == 'POST':
        password = request.form['password']

        # Validasi password
        password_regex = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(password_regex, password):
            return render_template('reset_password.html', error="Password harus memiliki minimal 8 karakter, termasuk huruf besar, huruf kecil, angka, dan simbol!")

        # Koneksi ke database
        connection = get_db_connection()
        if connection is None:
            return render_template('reset_password.html', error="Gagal terhubung ke database!")

        cursor = connection.cursor()
        try:
            # Hash password baru
            hashed_password = generate_password_hash(password)

            # Update password di database
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
            connection.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return render_template('reset_password.html', error=f"Terjadi kesalahan: {e}")
        finally:
            cursor.close()
            connection.close()

    return render_template('reset_password.html')

def send_email(to_email, subject, body):
    try:
        # Membuat koneksi SMTP
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        
        # Membuat email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Kirim email
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        print("Email berhasil dikirim.")
    except Exception as e:
        print(f"Error saat mengirim email: {e}")
    
    return render_template('forgot_password.html', error="Gagal mengirim email. Coba lagi nanti.")

# SocketIO: Membuat room
@socketio.on('create_room')
def handle_create_room(data):
    user_name = data['userName']
    room_code = data['roomCode']

    # Validasi room code
    if room_code not in VALID_CODE:
        socketio.emit('error', {'message': 'Invalid Room Code. Choose a valid code name.'}, room=request.sid)
        return

    # Buat room baru jika belum ada
    if room_code not in rooms:
        rooms[room_code] = {'users': []}
        
    if user_name in rooms[room_code]['users']:
        socketio.emit('error', {'message': f'Username "{user_name}" sudah digunakan di room {room_code}.'}, room=request.sid)
        return

    # Tambahkan user ke room
    rooms[room_code]['users'].append(user_name)
    join_room(room_code)

    print(f"Room {room_code} created by {user_name}")
    socketio.emit('create_room', {'userName': user_name, 'roomCode': room_code}, room=request.sid)

# SocketIO: Bergabung ke room
@socketio.on('join_room')
def handle_join_room(data):
    user_name = data['userName']
    room_code = data['roomCode']

    if room_code not in VALID_CODE:
        socketio.emit('error', {'message': 'Invalid Room Code. Use a valid code room.'}, room=request.sid)
        return

    if room_code in rooms:
        
        if user_name in rooms[room_code]['users']:
            socketio.emit('error', {'message': f'Username "{user_name}" sudah digunakan di dalam room ini !! .'}, room=request.sid)
            return
        
        rooms[room_code]['users'].append(user_name)
        join_room(room_code)
        print(f"{user_name} joined room {room_code}")
        socketio.emit('update_users', {'users': rooms[room_code]['users']}, room=room_code)
        
        #join
        socketio.emit('join_notify', {'message': f"{user_name} Memasuki Room!"}, room=room_code)
        
        socketio.emit('join_berhasil', {'message': 'Berhasil Masuk ke Dalam Room !!'}, room=request.sid)   
    else:
        socketio.emit('error', {'message': 'Invalid Room Code.'}, room=request.sid)

# SocketIO: Mengirim pesan
@socketio.on('message')
def handle_message(data):
    message = data['message']
    user_name = data['userName']
    room_code = data['roomCode']

    print(f"Message in room {room_code} from {user_name}: {message}")
    time = datetime.now().strftime('%H:%M')
    
    # Koneksi Database
    connection = get_db_connection()
    if connection is not None:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO chat (room_code, user_name, message, timestamp) VALUES (%s, %s, %s, %s)",
                (room_code, user_name, message, datetime.now())
            )
            connection.commit()
        except Exception as e:
            print(f"Error saat menyimpan pesan ke database: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        print("Gagal terhubung ke database pada saat menyimpan pesan.")
        
    if room_code not in rooms or user_name not in rooms[room_code]['users']:
        print(f"Pesan dari {user_name} di room {room_code} ditolak.")
        return
    
    socketio.emit('message', {
        'message': message,
        'userName': user_name,
        'socket_id': request.sid,
        'time': time
    }, room=room_code)
    
@app.route('/get_messages/<room_code>', methods=['GET'])
def get_messages(room_code):
    connection = get_db_connection()
    if connection is None:
        return {"Error": "Gegal Terhubung ke database."}, 500
    cursor = connection.cursor(dictionari=True)
    try:
        cursor.execute("SELECT user_name, message, timestamp FROM chat WHERE room_code = %s ORDER BY timestamp ASC", (room_code))
        messages = cursor.fetchall()
        return {"messages": messages}, 200
    except Exception as e:
        return {"error": f"Terjadi Kesalahan: {e}"}, 500
    finally:
        cursor.close()
        connection.close()
        
# SocketIO: Keluar dari room
@socketio.on('leave_room')
def handle_leave_room(data):
    user_name = data['userName']
    room_code = data['roomCode']

    if room_code in rooms:
        if user_name in rooms[room_code]['users']:
            rooms[room_code]['users'].remove(user_name)
        leave_room(room_code)
        print(f"{user_name} left room {room_code}")
        socketio.emit('leave_notify', {'message': f"{user_name} Telah Meninggalkan Room!"}, room=room_code)


        # Hapus room jika kosong
        if not rooms[room_code]['users']:
            del rooms[room_code]

    socketio.emit('leave_room', {'userName': user_name, 'roomCode': room_code}, room=room_code)
    
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',         
            user='root',               
            password='',  
            database='minichat'   
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5555, debug=True)
