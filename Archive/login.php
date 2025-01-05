<?php
session_start();
include 'config.php';

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST['username'];
    $password = $_POST['password'];

    $stmt = $conn->prepare("SELECT id, password FROM users WHERE username = ?");
    $stmt->bind_param("s", $username);
    $stmt->execute();
    $stmt->store_result();

    if ($stmt->num_rows > 0) {
        $stmt->bind_result($id, $hashed_password);
        $stmt->fetch();

        if (password_verify($password, $hashed_password)) {
            // Simpan ID pengguna di session
            $_SESSION['user_id'] = $id;
            $_SESSION['username'] = $username;
            header("Location: index.html");
            exit();
        } else {
            echo "<p style='color: red;'>Password salah!</p>";
        }
    } else {
        echo "<p style='color: red;'>Username tidak ditemukan!</p>";
    }
    $stmt->close();
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
<img src="images/Sentri2.png" style="width: 150px; position: absolute; top: 28px; left: 600px;">
<img src="images/p.png" style="width: 150px; position: absolute; top: 36px; left: 500px;">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        /* Tambahan styling untuk ikon mata */
        .password-container {
            position: relative;
            display: flex;
            align-items: center;
        }
        .password-container input {
            width: 100%;
            padding-right: 40px; /* Space for the eye icon */
        }
        .toggle-password {
            position: absolute;
            right: 10px;
            cursor: pointer;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-container">
            <h2>Login</h2>
            <form method="post">
                <label>Username</label>
                <input type="text" name="username" required>
                <label>Password</label>
                <div class="password-container">
                    <input type="password" name="password" id="password" required>
                    <i class="fas fa-eye toggle-password" id="togglePassword" onclick="togglePasswordVisibility()"></i>
                </div>
                <button type="submit" class="button">Login</button>
            </form>
            <p>Belum punya akun? <a href="register.php">Register di sini</a></p>
            <p><a href="forgot_password.php">Lupa password?</a></p> 
        </div>
    </div>

    <script>
        // Tambahkan fungsi untuk toggle password
        function togglePasswordVisibility() {
            const passwordField = document.getElementById('password');
            const togglePasswordIcon = document.getElementById('togglePassword');
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                togglePasswordIcon.classList.remove('fa-eye');
                togglePasswordIcon.classList.add('fa-eye-slash');
            } else {
                passwordField.type = 'password';
                togglePasswordIcon.classList.remove('fa-eye-slash');
                togglePasswordIcon.classList.add('fa-eye');
            }
        }
    </script>



</body>
</html>