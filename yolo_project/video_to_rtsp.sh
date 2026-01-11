ffmpeg -re -stream_loop -1 -i sample.mp4 \
-c:v libx264 -preset veryfast -tune zerolatency \
-f rtsp rtsp://127.0.0.1:8554/live
