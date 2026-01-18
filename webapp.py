from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
import cv2

app = FastAPI()

RTSP_URL = "rtsp://127.0.0.1:8554/annotated"

def generate_frames():
    cap = cv2.VideoCapture(RTSP_URL)

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Convert frame to JPEG
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        # MJPEG format
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame_bytes +
            b"\r\n"
        )

@app.get("/")
def index():
    return HTMLResponse("""
    <html>
        <head>
            <title>YOLO Live Stream</title>
        </head>
        <body style="text-align:center;">
            <h1>YOLO Real-Time Person Detection</h1>
            <img src="/video" width="900">
        </body>
    </html>
    """)

@app.get("/video")
def video():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
