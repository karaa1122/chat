import cv2
import torch
import face_recognition
import os
from playsound import playsound
from multiprocessing import Process, Queue

# Load known faces and their corresponding names
knife_objects = ["knife", "blade", "dagger", "cutlery"]
known_faces = {}
known_faces_dir = "known_faces"

for person_name in os.listdir(known_faces_dir):
    person_images = [os.path.join(known_faces_dir, person_name, img) for img in os.listdir(os.path.join(known_faces_dir, person_name))]
    encodings = [face_recognition.face_encodings(face_recognition.load_image_file(image))[0] for image in person_images]
    known_faces[person_name] = encodings

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5:v6.0', 'yolov5m', pretrained=True)
model = model.autoshape()  # Autoshape adjusts input size for better performance

def play_alarm_sound():
    # Play alarm sound in a non-blocking way
    playsound("alarm.mp3", block=False)

def capture_frames(video_source, frame_queue):
    if video_source.isdigit():
        video_capture = cv2.VideoCapture(int(video_source))
    else:
        video_capture = cv2.VideoCapture(video_source)

    while True:
        ret, frame = video_capture.read()
        if frame is not None:
            frame_queue.put(frame)

def process_frames(frame_queue, process_every_n_frames=5):
    frame_count = 0
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            frame_count += 1

            if frame_count % process_every_n_frames == 0:
                # Resize the frame to the lower resolution
                frame = cv2.resize(frame, (640, 480))

                # Run YOLOv5 model and face recognition on the frame
                results = model(frame, size=640)

                # Detect if a knife is present in the frame
                knife_detected = any(result[0] in knife_objects for result in results.xyxy[0])

                if knife_detected:
                    play_alarm_sound()

                # Find all face locations in the frame for face recognition
                face_locations = face_recognition.face_locations(frame)
                face_encodings = face_recognition.face_encodings(frame, face_locations)

                face_names = []

                for face_encoding in face_encodings:
                    # Check if the face matches any known person
                    recognized_name = "Unknown"
                    for name, known_encodings in known_faces.items():
                        matches = face_recognition.compare_faces(known_encodings, face_encoding)
                        if any(matches):
                            recognized_name = name
                            break

                    face_names.append(recognized_name)

                # Display the results
                for row in results.xyxy[0].cpu().numpy():
                    x1, y1, x2, y2, conf, label = map(int, row[:6])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
                    cv2.putText(frame, f'{model.names[int(label)]} {conf:.2f}', (x1, y1), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)

                for (top, right, bottom, left), name in zip(face_locations, face_names):
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

                cv2.imshow('Object Detection and Face Recognition', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

if __name__ == "__main__":
    video_source = input("Enter '0' for webcam or provide the path to the video file: ")
    frame_queue = Queue(maxsize=5)
    capture_process = Process(target=capture_frames, args=(video_source, frame_queue))
    process_process = Process(target=process_frames)
