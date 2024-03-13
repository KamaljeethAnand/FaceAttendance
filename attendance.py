import streamlit as st
import cv2
import os
import firebase_admin
import base64
import pickle
import datetime
import subprocess
import pandas as pd
import face_recognition
import numpy as np
import pytz
from PIL import Image
import PIL
import PIL.Image
import PIL.ImageFont
from PIL import ImageOps
import PIL.ImageDraw
import image_dehazer
import math

# Load your logo image
logo = Image.open("e:\FINAL_PROJECT\FDP-main\cmr.png")

# Display the logo and navigation bar
st.image(logo, width=150)
# Add a welcome message and a description of the attendance system
stud_list = {
        "name": [],
        "usn":[]
}
local_tz = pytz.timezone('Asia/Kolkata')
            
def main():
    # st.title("Student Attendance System")
    menu = ["Home","Take Attendance"]
    choice = st.sidebar.selectbox("Select Option", menu)

    if choice == "Home":

        st.title("Welcome to the Attendance System")
        st.write(
            """
            This attendance system uses facial recognition to mark attendance for students.
            It allows you to register new students, take attendance using live video or uploaded images, 
            store images for each student, and view attendance records. 
            """
        )
    elif choice == "Take Attendance":
        take_attendance()
# Load existing encodings and student IDs

# New one with enhanced options
import dlib
def _css_to_rect(css):
    return dlib.rectangle(css.left(), css.top(), css.right(), css.bottom())

def take_attendance():
    with open('encoded_people.pickle', 'rb') as filename:
        people = pickle.load(filename)
    st.subheader("Take Attendance")
    semester = st.selectbox("Select Semester", options=[1, 2, 3, 4, 5, 6, 7, 8])
    section = st.selectbox("Select Section", options=["A", "B", "C", "D"])
    department = st.selectbox("Select department", options = ["CSE", "ISE", "ECE", "EEE", "AI&ML", "DS", "Mech", "Civil"])
    option = st.radio("Select Option", ("Live Video", "Upload Image"))
    if option == "Live Video":
        if st.button("Take Attendance"):
            subprocess.run(["python", "main.py"])
            st.success('Success! Attendance marked')
    elif option == "Upload Image":
        # Read in the uploaded image
        uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            st.image(img)
            option = st.radio("Select Option", ("Select","DeHazing", "No Dehazing"))
            if option == "Select":
                input()
            if option =="No Dehazing":
                img=img
            if option == "DeHazing":
                st.write("""Please wait for image to be dehazed.""")
                HazeCorrectedImg, HazeMap = image_dehazer.remove_haze(img,boundaryConstraint_windowSze=3,showHazeTransmissionMap=False)
                st.image(HazeCorrectedImg)
                img = HazeCorrectedImg 
            print("Face Detection")
            img_loc = face_recognition.face_locations(img,number_of_times_to_upsample=3,model="hog")
            img_enc = face_recognition.face_encodings(img,known_face_locations=img_loc)
            face_img = PIL.Image.fromarray(img)
            print("Face Tagging")
            unknown_faces_location = []
            unknown_faces_enconded = []
            for i in range(0,len(img_enc)):
                best_match_count = 0
                best_match_name = "unknown"
                for k,v in people.items():
                    result = face_recognition.compare_faces(v,img_enc[i],tolerance=0.45)
                    count_true = result.count(True)
                    if  count_true > best_match_count: # To find the best person that matches with the face
                        best_match_count = count_true
                        best_match_name = k
                print(best_match_name)
                # Draw and write on photo
                top,right,bottom,left = img_loc[i]
                draw = PIL.ImageDraw.Draw(face_img)
                font = PIL.ImageFont.truetype("timesbd.ttf",size=max(math.floor((right-left)/6),16))
                draw.rectangle([left,top,right,bottom], outline="red", width=3)
                draw.rectangle((left, bottom, left + font.getbbox(best_match_name)[0] , bottom +  font.getbbox(best_match_name)[1]*1.2), fill='black')
                draw.text((left,bottom), best_match_name, font=font )
            st.image(face_img)
            st.dataframe(pd.DataFrame(stud_list))

if __name__ == '__main__':
    main()
