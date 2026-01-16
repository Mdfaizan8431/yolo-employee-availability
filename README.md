# YOLO Employee Availability Monitoring System

## 📌 Project Overview

This project is a **real-time employee availability monitoring system** built using
Computer Vision and Backend APIs.

It automatically checks whether an employee is **present or absent** at their desk
using a camera feed. If the employee is not present for more than **5 minutes**, the
system marks them as **NOT AVAILABLE** and triggers an alert.

This project is suitable for:
- Office reception desks
- Help desks
- Employee presence monitoring
- Internship / Fresher-level projects

---

## 🎯 What This Project Does

- Detects people using **YOLOv8**
- Defines a fixed **ROI (Region of Interest)** as the employee seating area
- If a person is inside the ROI → **Employee Available**
- If no person is inside the ROI for **5 minutes** → **Employee Not Available**
- Streams live annotated video to:
  - Web browser
  - Mobile phone
- Saves entry/exit events in **PostgreSQL database**

---

## ⚙️ How the Project Works (Step-by-Step)

### 1️⃣ Video Input
- A camera or sample video is converted to an **RTSP stream** using FFmpeg
- **MediaMTX** works as the RTSP server



#Camera / Video → RTSP Server
---

### 2️⃣ Person Detection
- YOLOv8 detects persons in each frame
- ByteTrack assigns a **tracking ID** to each detected person
  

#RTSP → YOLO Detection → Tracking
---

### 3️⃣ ROI (Employee Area)
- A fixed rectangular ROI is defined in code
- This ROI represents the employee desk/seat


#Person inside ROI → Available
#Person outside ROI → Absence timer starts
---

### 4️⃣ Availability Logic
- If ROI remains empty:
  - Timer starts
- If empty for **5 minutes**:
  - Employee marked NOT AVAILABLE
  - Alert generated
  - Event sent to backend API

---

### 5️⃣ Backend (FastAPI + PostgreSQL)
- FastAPI receives events such as:
  - ENTRY
  - EXIT
  - NOT_AVAILABLE
- All events are stored in PostgreSQL database

#YOLO → FastAPI → PostgreSQL
---

### 6️⃣ Web Streaming
- Annotated video is sent back as an RTSP stream
- Web app converts RTSP → MJPEG
- Live stream accessible on browser and mobile


#RTSP → Web Page → Phone / Browser
---

## 🔁 Complete Pipeline
Camera
↓
RTSP Stream
↓
YOLO Person Detection
↓
ROI Check
↓
Availability Logic (5 min rule)
↓
RTSP Annotated Output
↓
Web Page / Mobile


---

## 🚀 How to Run the Project

### ✅ Requirements
- Python 3.9+
- FFmpeg
- PostgreSQL
- MediaMTX
- Ubuntu / Linux (recommended)

---

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt

2️⃣ Start RTSP Streaming

chmod +x video_to_rtsp.sh
./video_to_rtsp.sh

3️⃣ Start Backend API
uvicorn main:app --host 0.0.0.0 --port 8000

4️⃣ Start YOLO Processing
python yolo_rtsp_roi.py

5️⃣ Start Web Application
uvicorn webapp:app --host 0.0.0.0 --port 8001

6️⃣ Open Live Stream

On Laptop

http://127.0.0.1:8001

On Mobile (same Wi-Fi)

http://<your-laptop-ip>:8001

Example:

http://192.168.0.148:8001


🧠 Technologies Used

Python

YOLOv8

OpenCV

FastAPI

PostgreSQL

FFmpeg

MediaMTX

RTSP Streaming

