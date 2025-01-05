<?php
session_start();
include 'config.php';

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $email = $_POST['email'];

    $stmt = $conn->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $stmt->store_result();

    if ($stmt->num_rows > 0) {
        // Buat token unik
        $token = bin2hex(random_bytes(32));
        $stmt->bind_result($id);
        $stmt->fetch();

        // Simpan token di database
        $stmt_insert = $conn->prepare("INSERT INTO password_resets (user_id, token) VALUES (?, ?)");
        $stmt_insert->bind_param("is", $id, $token);
        $stmt_insert->execute();

        // Kirim email reset password
        $reset_link = "http://yourwebsite.com/reset_password.php?token=$token";
        $subject = "Reset Password Anda";
        $message = "Klik link berikut untuk reset password Anda: $reset_link";
        $headers = "From: no-reply@yourwebsite.com";

        if (mail($email, $subject, $message, $headers)) {
            echo "<p style='color: green;'>Email reset password telah dikirim.</p>";
        } else {
            echo "<p style='color: red;'>Gagal mengirim email. Coba lagi nanti.</p>";
        }
    } else {
        echo "<p style='color: red;'>Email tidak ditemukan.</p>";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lupa Password</title>
    <link rel="stylesheet" href="style.css">
    <style>
        /* Tambahkan styling tombol */
        .button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 10px 0;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .button:hover {
            background-color: #45a049;
        }

        .button-secondary {
            background-color: #f44336;
            color: white;
        }
        .button-secondary:hover {
            background-color: #e53935;
        }
    </style>
</head>
<img src="images/Sentri2.png" style="width: 150px; position: absolute; top: 48px; left: 600px;">
<img src="images/p.png" style="width: 150px; position: absolute; top: 56px; left: 500px;">
<body>
    <div class="container">
        <div class="form-container">
            <h2>Lupa Password</h2>
            <form method="post">
                <label>Email</label>
                <input type="email" name="email" required>
                <button type="submit" class="button">Kirim Email Reset</button>
            </form>
            <!-- Tambahkan tombol Kembali ke Login -->
            <br>
            <a href="login.php" class="button button-secondary">Kembali ke Login</a>
        </div>
    </div>
</body>
</html>
