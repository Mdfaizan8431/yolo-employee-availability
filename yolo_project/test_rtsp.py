import cv2

RTSP_URL = "rtsp://127.0.0.1:8554/live"

cap = cv2.VideoCapture(RTSP_URL)

if not cap.isOpened():
    print("❌ Cannot open RTSP stream")
    exit()

print("✅ RTSP stream opened successfully")
print("Press ESC to exit")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to read frame")
        break

    cv2.imshow("RTSP Test", frame)

    # ESC key to exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
