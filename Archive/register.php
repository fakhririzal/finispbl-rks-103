<?php
    include 'config.php';

    if ($_SERVER["REQUEST_METHOD"] == "POST") {
        $username = $_POST['username'];
        $email = $_POST['email'];
        $password = password_hash($_POST['password'], PASSWORD_DEFAULT);

        // Cek apakah username atau email sudah ada
        $checkStmt = $conn->prepare("SELECT id FROM users WHERE username = ? OR email = ?");
        $checkStmt->bind_param("ss", $username, $email);
        $checkStmt->execute();
        $checkStmt->store_result();

        if ($checkStmt->num_rows > 0) {
            // Jika username atau email sudah terdaftar
            $error = "Username atau email sudah terdaftar. Gunakan yang lain.";
        } else {
            // Jika tidak ada duplikasi, simpan data pengguna baru
            $stmt = $conn->prepare("INSERT INTO users (username, email, password) VALUES (?, ?, ?)");
            $stmt->bind_param("sss", $username, $email, $password);

            if ($stmt->execute()) {
                header("Location: login.php");
                exit();
            } else {
                $error = "Terjadi kesalahan saat mendaftar. Coba lagi.";
            }
            $stmt->close();
        }
        $checkStmt->close();
    }
    ?>

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Register</title>
        <link rel="stylesheet" href="style.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        <style>
            .password-container {
                position: relative;
                display: flex;
                align-items: center;
            }

            .password-container input {
                flex: 1;
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
    <img src="images/Sentri2.png" style="width: 150px; position: absolute; top: 18px; left: 600px;">
<img src="images/p.png" style="width: 150px; position: absolute; top: 26px; left: 500px;">
    <body>
        <div class="container">
            <div class="form-container">
                <h2>Register</h2>
                <?php if (isset($error)) { echo "<p style='color: red;'>$error</p>"; } ?>
                <form method="post">
                    <label>Username</label>
                    <input type="text" name="username" required>
                    <label>Email</label>
                    <input type="email" name="email" required>
                    <label>Password</label>
                    <div class="password-container">
                        <input type="password" name="password" id="password" required>
                        <i class="fas fa-eye toggle-password" id="togglePassword" onclick="togglePasswordVisibility()"></i>
                    </div>
                    <button type="submit" class="button">Register</button>
                </form>
                <p>Sudah punya akun? <a href="login.php">Login di sini</a></p>
            </div>
        </div>

        <script>
            function togglePasswordVisibility() {
                var passwordInput = document.getElementById("password");
                var togglePasswordIcon = document.getElementById("togglePassword");

                if (passwordInput.type === "password") {
                    passwordInput.type = "text";
                    togglePasswordIcon.classList.remove("fa-eye");
                    togglePasswordIcon.classList.add("fa-eye-slash");
                } else {
                    passwordInput.type = "password";
                    togglePasswordIcon.classList.remove("fa-eye-slash");
                    togglePasswordIcon.classList.add("fa-eye");
                }
            }
        </script>
    </body>
    </html>