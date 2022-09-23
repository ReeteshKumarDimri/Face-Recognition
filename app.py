from ctypes import sizeof
from flask import Flask, render_template, request,Response
import tweepy
import wget
import face_recognition
import cv2
import numpy as np
import os

video_capture = cv2.VideoCapture(0)
videoOn = False

known_face_encodings = []
known_face_names = []
dir = os.path.dirname(__file__)
encdir = os.path.join(dir,'encodings')
for file in os.listdir(encdir):
    denf = os.path.join(encdir, file)
    denc = np.loadtxt(denf)
    known_face_encodings.append(denc)
    known_face_names.append(file)

unknownDir = os.path.join(dir,'static','Unknown')

def Process_frame(frame):
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]
    if process_this_frame:
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
            face_names.append(name)
    process_this_frame = not process_this_frame
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)





def addEncoding(imageurl,name):
    image = face_recognition.load_image_file(imageurl)
    pathName = os.path.join(encdir,name)
    f = open(pathName, "w")
    face_locations = face_recognition.face_locations(image)
    face_encoding = face_recognition.face_encodings(image)[0]
    known_face_encodings.append(face_encoding)
    known_face_names.append(name)
    for x in face_encoding:
        f.write(str(x) + '\n')
    f.close


def process_Images():
    list = []
    for file in os.listdir(unknownDir):
        img = os.path.join(unknownDir,file)
        print()
        list.append(processImg(img,file))
    return list

def processImg(img,file):
    arr = []
    image = face_recognition.load_image_file(img)
    face_locations = face_recognition.face_locations(image)
    face_encoding = face_recognition.face_encodings(image)[0]
    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
    name = "Unknown"
    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
    best_match_index = np.argmin(face_distances)
    if matches[best_match_index]:
        name = known_face_names[best_match_index]
    arr.append(file)
    arr.append(name)
    return arr

def gen_frames():  
    while True:

        success, frame = video_capture.read()  # read the camera frame
        
        if not success:
            break
        else:
            Process_frame(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

app=Flask(__name__)

#First Page.
@app.route("/")
def home_page():
    return render_template("form.html",isvideo = False,
    isphotos = False, isform = False)

@app.route("/Fetch_Data",methods=['POST','GET'])
def Fetch_data():
    global videoOn
    global video_capture
    v = False
    p = False
    f = False
    if request.method == 'POST':
        if request.form.get('a') == 'Add Encoding':
            videoOn = False
            v = False
            p = False
            f = True
        elif  request.form.get('r') == 'Recognize':
            videoOn = not videoOn
            v = True
            p = False
            f = False
        elif request.form.get('u') == 'Upload':
            videoOn = False
            v = False
            p = True
            f = False
    if(videoOn):
        video_capture = cv2.VideoCapture(0)
    else:
        video_capture.release()
    return render_template("form.html",isvideo = v,
        isphotos = p, isform = f) 

@app.route("/Add",methods=['POST','GET'])
def Add():
    global unknownDir
    if request.method=="POST":   
        name = request.form["q"]
        if(name == ""):
            return render_template("form.html",isvideo = False,
            isphotos = False, isform = True,warning = "Enter the Name!")
        image = request.files["img"]
        
        if not request.files.get('img', None):
            pass
        imgurl = os.path.join(unknownDir,image.filename)
        image.save(imgurl)
        addEncoding(imgurl,name)
        for f in os.listdir(unknownDir):
            os.remove(os.path.join(unknownDir, f))
        return render_template("form.html",isvideo = False,
    isphotos = False, isform = True,warning = "Encoding Added SuccessFully!")

@app.route("/imgs",methods=['POST','GET'])
def imgs():
    for f in os.listdir(unknownDir):
        os.remove(os.path.join(unknownDir, f))
    if request.method=="POST":
        uploaded_imgs = request.files.getlist("img")
        print(len(uploaded_imgs))
        for img in uploaded_imgs:
            if(img.filename == ""):
                return render_template("form.html",isvideo = False,
                isphotos = True, isform = False)
            imgurl = os.path.join(unknownDir,img.filename)
            img.save(imgurl)
        list = process_Images()
        print(list)
        return render_template("form.html",isvideo = False,
    isphotos = True, isform = False,images = list)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ =="__main__":
    app.run(debug= True)

            