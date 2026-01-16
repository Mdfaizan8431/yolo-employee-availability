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
API_URL = "http://127.0.0.1:8000/employee"

FPS = 25
FRAME_WIDTH = 1000
FRAME_HEIGHT = 500

EMPLOYEE_ABSENCE_THRESHOLD = 300  # 5 minutes

# =========================
# FIXED ROI CONFIG (PRODUCTION STYLE)
# =========================

ROI_X1 = int(FRAME_WIDTH * 0.65)   # start from 65% width
ROI_Y1 = int(FRAME_HEIGHT * 0.30)  # 20% from top

ROI_X2 = int(FRAME_WIDTH * 0.99)   # end at 95% width
ROI_Y2 = int(FRAME_HEIGHT * 0.99)  # 85% from top

# =========================
# STATE VARIABLES
# =========================
last_inside_roi = False      # ENTRY / EXIT logic
roi_empty_since = None       # 5-minute logic
absence_alert_sent = False  # prevent alert spam

# =========================
# LOAD YOLO
# =========================
model = YOLO("yolov8n.pt")

# =========================
# OPEN RTSP INPUT
# =========================
cap = None
while cap is None or not cap.isOpened():
    print("⏳ Waiting for RTSP input...")
    cap = cv2.VideoCapture(RTSP_INPUT)
    time.sleep(1)

# =========================
# START FFMPEG OUTPUT
# =========================
ffmpeg_cmd = [
    "ffmpeg",
    "-y",
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

# =========================
# UI (LOCAL PREVIEW)
# =========================
cv2.namedWindow("YOLO ROI (Local Preview)", cv2.WINDOW_NORMAL)

print("✅ YOLO + ENTRY/EXIT + 5-MIN ALERT STARTED")

# =========================
# MAIN LOOP
# =========================
while True:
    try:
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
        cv2.putText(
            frame,
            "EMPLOYEE AREA",
            (ROI_X1, ROI_Y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2
        )

        any_person_inside_roi = False

        # =========================
        # PERSON DETECTION
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

                inside_roi = (
                    ROI_X1 < cx < ROI_X2 and
                    ROI_Y1 < cy < ROI_Y2
                )

                if inside_roi:
                    any_person_inside_roi = True
                    color = (0, 255, 0)
                    label = f"ID {track_id} (EMPLOYEE)"
                else:
                    color = (0, 255, 255)
                    label = f"ID {track_id}"

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )

        # =========================
        # ENTRY / EXIT DATABASE LOGIC
        # =========================
        if any_person_inside_roi and not last_inside_roi:
            print("🟢 ENTRY")
            try:
                requests.post(
                    API_URL,
                    json={"status": "ENTRY", "time": str(datetime.now())},
                    timeout=0.5
                )
            except:
                pass

        if not any_person_inside_roi and last_inside_roi:
            print("🔴 EXIT")
            try:
                requests.post(
                    API_URL,
                    json={"status": "EXIT", "time": str(datetime.now())},
                    timeout=0.5
                )
            except:
                pass

        last_inside_roi = any_person_inside_roi

        # =========================
        # 5-MINUTE AVAILABILITY LOGIC
        # =========================
        current_time = time.time()

        if any_person_inside_roi:
            roi_empty_since = None
            absence_alert_sent = False

            cv2.putText(
                frame,
                "EMPLOYEE AVAILABLE",
                (40, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                3
            )

        else:
            if roi_empty_since is None:
                roi_empty_since = current_time

            absence_duration = current_time - roi_empty_since

            cv2.putText(
                frame,
                f"EMPLOYEE OUT {int(absence_duration)}s",
                (40, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                3
            )

            if absence_duration > EMPLOYEE_ABSENCE_THRESHOLD:
                cv2.putText(
                    frame,
                    "🚨 EMPLOYEE NOT AVAILABLE",
                    (40, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3
                )

                if not absence_alert_sent:
                    absence_alert_sent = True
                    print("🚨 ABSENCE ALERT")

        # =========================
        # SEND FRAME TO RTSP
        # =========================
        try:
            ffmpeg_process.stdin.write(frame.tobytes())
        except:
            ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        # =========================
        # LOCAL PREVIEW
        # =========================
        cv2.imshow("YOLO ROI (Local Preview)", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    except Exception as e:
        print("⚠️ Error:", e)
        time.sleep(1)

# =========================
# CLEANUP
# =========================
cap.release()
ffmpeg_process.stdin.close()
ffmpeg_process.wait()
cv2.destroyAllWindows()
print("🛑 System stopped")
