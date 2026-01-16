import subprocess
import time
import signal
import os

processes = []

def start_process(cmd, name):
    print(f"🚀 Starting {name}...")
    p = subprocess.Popen(cmd, shell=True)
    processes.append(p)
    time.sleep(2)

try:
    # 1. Start MediaMTX
    start_process("~/mediamtx ~/mediamtx.yml", "MediaMTX (RTSP server)")

    # 2. Start FFmpeg (video → RTSP)
    start_process(
        "cd ~/Desktop/yolo_project && ./video_to_rtsp.sh",
        "FFmpeg (Video → RTSP)"
    )

    # 3. Web video stream (FIXED)
    start_process(
        "cd ~/Desktop/yolo_project && uvicorn webapp:app --host 0.0.0.0 --port 8001",
        "WebApp"
    )

    # 4. FastAPI backend (FIXED)
    start_process(
        "cd ~/Desktop/yolo_project && uvicorn main:app --host 0.0.0.0 --port 8000",
        "FastAPI"
    )

    # 5. YOLO + ROI
    start_process(
        "cd ~/Desktop/yolo_project && python yolo_rtsp_roi.py",
        "YOLO + RTSP + ROI"
    )

    print("\n✅ ALL SERVICES STARTED")
    print("Press CTRL+C to stop everything")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Stopping all services...")
    for p in processes:
        p.send_signal(signal.SIGINT)
    print("✅ All services stopped")
