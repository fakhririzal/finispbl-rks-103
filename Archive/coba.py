from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import re

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
    return render_template('index.html')

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
        
        #Validasi
        
        password_regex = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(password_regex, password):
            return {"success": False, "error": "Password harus memiliki minimal 8 karakter, termasuk huruf besar, huruf kecil, angka, dan simbol."}, 400

        connection = get_db_connection()
        if connection is None:
            return {"success": False, "error": "Gagal terhubung ke database!"}, 500

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
            return {"success": True}, 201
        except mysql.connector.IntegrityError as e:
            return {"success": False, "error": "Username atau email sudah terdaftar!"}, 400
        except Exception as e:
            return {"success": False, "error": f"Terjadi kesalahan: {e}"}, 500
        finally:
            cursor.close()
            connection.close()

    return render_template('register.html')



VALID_ANIMALS = ['joni', 'yono', 'siti', 'hawa', 'yanto', 'yanti', 'suna', 'nami']

# SocketIO: Membuat room
@socketio.on('create_room')
def handle_create_room(data):
    user_name = data['userName']
    room_code = data['roomCode']

    # Validasi room code
    if room_code not in VALID_ANIMALS:
        socketio.emit('error', {'message': 'Invalid Room Code. Choose a valid animal name.'}, room=request.sid)
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

    if room_code not in VALID_ANIMALS:
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
    socketio.emit('message', {
        'message': message,
        'userName': user_name,
        'socket_id': request.sid,
        'time': time
    }, room=room_code)

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
