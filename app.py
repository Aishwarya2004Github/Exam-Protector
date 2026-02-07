from flask import Flask, render_template, Response, jsonify
import cv2
from proctor_engine import ProctorEngine

app = Flask(__name__)
proctor = ProctorEngine()
camera = cv2.VideoCapture(0)

# Alerts store karne ke liye queue
current_alerts = []

def generate_frames():
    global current_alerts
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        # Engine ko frame process karne ke liye bhejte hain
        processed_frame, alerts = proctor.run_detection(frame)
        
        # Naye alerts ko list mein add karte hain
        if alerts:
            current_alerts.extend(alerts)
            # Memory saaf rakhne ke liye sirf latest 15 alerts rakhte hain
            if len(current_alerts) > 15:
                current_alerts = current_alerts[-15:]

        # Web browser ke liye frame encode karein
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_alerts')
def get_alerts():
    global current_alerts
    temp_alerts = list(set(current_alerts)) # Remove duplicates
    current_alerts = [] # Clear the queue
    return jsonify(alerts=temp_alerts)

if __name__ == "__main__":
    # Debug mode on rakhein taaki changes turant dikhein
    app.run(debug=True, port=5000)