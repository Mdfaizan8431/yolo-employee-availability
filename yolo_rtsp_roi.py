import cv2
import time
import subprocess
import requests
from ultralytics import YOLO
from datetime import datetime

# =========================
# CONFIG
# =========================
RTSP_INPUT = "rtsp://127.0.0.1:8554/live"
RTSP_OUTPUT = "rtsp://127.0.0.1:8554/annotated"

API_ENTRY_URL = "http://127.0.0.1:8000/employee/entry"
API_EXIT_URL = "http://127.0.0.1:8000/employee/exit"
API_NOT_AVAILABLE_URL = "http://127.0.0.1:8000/employee/not_available"


FRAME_WIDTH = 1000
FRAME_HEIGHT = 500
FPS = 25

EMPLOYEE_ABSENCE_THRESHOLD = 300  # 5 minutes

# =========================
# FIXED ROI (EMPLOYEE AREA)
# =========================
ROI_X1 = int(FRAME_WIDTH * 0.65)
ROI_Y1 = int(FRAME_HEIGHT * 0.30)
ROI_X2 = int(FRAME_WIDTH * 0.99)
ROI_Y2 = int(FRAME_HEIGHT * 0.99)

# =========================
# STATE
# =========================
employees_previous_roi = set()
roi_empty_since = None
absence_alert_sent = False
active_ids = set()

# =========================
# LOAD YOLO
# =========================
model = YOLO("yolov8n.pt")

# =========================
# OPEN RTSP
# =========================
cap = cv2.VideoCapture(RTSP_INPUT)
while not cap.isOpened():
    print("⏳ Waiting for RTSP...")
    time.sleep(1)
    cap = cv2.VideoCapture(RTSP_INPUT)

# =========================
# FFMPEG OUTPUT
# =========================
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-s", f"{FRAME_WIDTH}x{FRAME_HEIGHT}",
    "-r", str(FPS),
    "-i", "-",
    "-an",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-tune", "zerolatency",
    "-f", "rtsp",
    RTSP_OUTPUT
]
ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

print("✅ YOLO Employee Availability Started")

# =========================
# MAIN LOOP
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        cap.release()
        time.sleep(1)
        cap = cv2.VideoCapture(RTSP_INPUT)
        continue

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False
    )

    # Draw ROI
    cv2.rectangle(frame, (ROI_X1, ROI_Y1), (ROI_X2, ROI_Y2), (255, 0, 0), 2)
    cv2.putText(frame, "EMPLOYEE AREA",
                (ROI_X1, ROI_Y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 0, 0), 2)

    employees_current_roi = set()

    # =========================
    # DETECTION LOOP
    # =========================
    for r in results:
        if r.boxes.id is None:
            continue

        boxes = r.boxes.xyxy.cpu().numpy()
        ids = r.boxes.id.cpu().numpy().astype(int)
        classes = r.boxes.cls.cpu().numpy().astype(int)

        for box, track_id, cls_id in zip(boxes, ids, classes):
            if model.names[cls_id] != "person":
                continue

            x1, y1, x2, y2 = map(int, box)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            inside_roi = ROI_X1 < cx < ROI_X2 and ROI_Y1 < cy < ROI_Y2

            if inside_roi:
                employees_current_roi.add(track_id)
                color = (0, 255, 0)
                label = f"EMPLOYEE ID {track_id}"
            else:
                color = (0, 255, 255)
                label = f"PERSON ID {track_id}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, color, 2)

    current_time = time.time()

        # =========================
    # ENTRY + EXIT LOGIC (FIXED)
    # =========================
    current_ids_in_roi = set()

    for r in results:
        if r.boxes.id is None:
            continue

        boxes = r.boxes.xyxy.cpu().numpy()
        ids = r.boxes.id.cpu().numpy().astype(int)
        classes = r.boxes.cls.cpu().numpy().astype(int)

        for box, track_id, cls_id in zip(boxes, ids, classes):
            if model.names[cls_id] != "person":
                continue

            x1, y1, x2, y2 = map(int, box)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            inside_roi = ROI_X1 < cx < ROI_X2 and ROI_Y1 < cy < ROI_Y2

            if inside_roi:
                current_ids_in_roi.add(track_id)

    # ENTRY
    new_entries = current_ids_in_roi - active_ids
    for track_id in new_entries:
        print(f"🟢 ENTRY: ID {track_id}")
        active_ids.add(track_id)

        try:
            requests.post(
                API_ENTRY_URL,
                json={"tracking_id": int(track_id), "time": str(datetime.now())},
                timeout=0.5
            )
        except:
            pass

    # EXIT
    exits = active_ids - current_ids_in_roi
    for track_id in exits:
        print(f"🔴 EXIT: ID {track_id}")
        active_ids.remove(track_id)

        try:
            requests.post(
                API_EXIT_URL,
                json={"tracking_id": int(track_id), "time": str(datetime.now())},
                timeout=0.5
            )
        except:
            pass
    # =========================
    # 5-MINUTE EMPTY ROI ALERT
    # =========================
    if len(employees_current_roi) == 0:
        if roi_empty_since is None:
            roi_empty_since = current_time

        if (current_time - roi_empty_since > EMPLOYEE_ABSENCE_THRESHOLD
                and not absence_alert_sent):
            absence_alert_sent = True
            print("🚨 EMPLOYEE NOT AVAILABLE")
            requests.post(
                API_NOT_AVAILABLE_URL,
                timeout=0.5
            )

    else:
        roi_empty_since = None
        absence_alert_sent = False

    employees_previous_roi = employees_current_roi.copy()

    # =========================
    # SEND TO RTSP
    # =========================
    try:
        ffmpeg_process.stdin.write(frame.tobytes())
    except:
        ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    cv2.imshow("YOLO ROI", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

# =========================
# CLEANUP
# =========================
cap.release()
ffmpeg_process.stdin.close()
ffmpeg_process.wait()
cv2.destroyAllWindows()
