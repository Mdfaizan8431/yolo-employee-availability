import subprocess
import time
import signal
import os

processes = []

HOME = os.path.expanduser("~")
PROJECT_DIR = os.path.join(HOME, "Desktop/yolo-employee-availability")

def start_process(cmd, name):
    print(f"🚀 Starting {name}...")
    p = subprocess.Popen(cmd, shell=True)
    processes.append(p)
    time.sleep(3)

try:
    # 1. MediaMTX
    start_process(
        f"chmod +x {PROJECT_DIR}/mediamtx && {PROJECT_DIR}/mediamtx {PROJECT_DIR}/mediamtx.yml",
        "MediaMTX (RTSP server)"
    )

    # 2. FFmpeg
    start_process(
        f"cd {PROJECT_DIR} && chmod +x video_to_rtsp.sh && ./video_to_rtsp.sh",
        "FFmpeg (Video → RTSP)"
    )

    # 3. WebApp
    start_process(
        f"cd {PROJECT_DIR} && python -m uvicorn webapp:app --host 0.0.0.0 --port 8001",
        "WebApp"
    )

    # 4. FastAPI
    start_process(
        f"cd {PROJECT_DIR} && python -m uvicorn main:app --host 0.0.0.0 --port 8000",
        "FastAPI"
    )

    # 5. YOLO
    start_process(
        f"cd {PROJECT_DIR} && python yolo_rtsp_roi.py",
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