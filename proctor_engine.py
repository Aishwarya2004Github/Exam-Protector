import cv2
import numpy as np
from ultralytics import YOLO
import time

class ProctorEngine:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.face_timers = {} 
        self.last_seen_time = {} 

    def get_grid_pos(self, x, y, frame_w, frame_h):
        row = int(y // (frame_h / 7)) + 1
        col = int(x // (frame_w / 3)) + 1
        return min(row, 7), min(col, 3)

    def run_detection(self, frame):
        alerts = []
        h, w, _ = frame.shape
        results = self.model(frame, conf=0.3, verbose=False)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 6)
        
        active_cheaters = []
        for r in results:
            for box in r.boxes:
                label = self.model.names[int(box.cls[0])]
                if label in ["cell phone", "laptop"]:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    row, col = self.get_grid_pos(x1+(x2-x1)//2, y1+(y2-y1)//2, w, h)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    alerts.append(f"CHEATING: {label.upper()} at R{row}, C{col}")
                    active_cheaters.append((x1, y1, x2, y2))

        current_time = time.time()
        new_face_timers = {}

        # Agar Face gayab hai (Looking away too much)
        if len(faces) == 0:
            for fid in list(self.face_timers.keys()):
                # Hum check karte hain ki kya ye "looking away" timer pehle se chal raha tha?
                start_t = self.face_timers[fid]
                if current_time - start_t > 5: # 5 second threshold
                    alerts.append("WARNING: Face not visible / Looking away too long")
                # Timer ko barkaraar rakhte hain
                new_face_timers[fid] = start_t
        else:
            for i, (x, y, fw, fh) in enumerate(faces):
                face_id = f"person_{i}"
                is_cheating = False
                
                # Proximity Check
                for (cx1, cy1, cx2, cy2) in active_cheaters:
                    if x < cx2 and (x + fw) > cx1:
                        is_cheating = True

                # --- ADVANCED HEAD TURN LOGIC ---
                face_center_x = x + fw // 2
                face_center_y = y + fh // 2
                
                # Check 1: Left/Right (Center 1/3 area)
                is_off_center_x = face_center_x < (w // 3) or face_center_x > (2 * w // 3)
                # Check 2: Up/Down (Center 1/2 area)
                is_off_center_y = face_center_y < (h // 4) or face_center_y > (3 * h // 4)
                
                if is_off_center_x or is_off_center_y:
                    start_time = self.face_timers.get(face_id, current_time)
                    new_face_timers[face_id] = start_time
                    
                    if current_time - start_time > 120: # 5 seconds for test
                        is_cheating = True
                        msg = "Looking SIDEWAYS" if is_off_center_x else "Looking UP/DOWN"
                        alerts.append(f"WARNING: ID {i+1} {msg}")
                else:
                    # Agar center mein dekh raha hai, toh timer reset
                    new_face_timers[face_id] = current_time

                color = (0, 0, 255) if is_cheating else (0, 255, 0)
                cv2.rectangle(frame, (x, y), (x + fw, y + fh), color, 3)
                cv2.putText(frame, f"ID:{i+1}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        self.face_timers = new_face_timers
        return frame, list(set(alerts))