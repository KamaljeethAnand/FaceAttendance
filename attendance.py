import streamlit as st
import os
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
logo = Image.open("cmr.png")

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
            It allows the teacher to upload images of the classroom in order to get the list of students present in the class. 

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
    semester = st.selectbox("Select Class", options=[1, 2, 3, 4, 5, 6, 7, 8])
    section = st.selectbox("Select Section", options=["A", "B", "C", "D"])
    department = st.selectbox("Select department", options = ["CSE", "ISE", "ECE", "EEE", "AI&ML", "DS", "Mech", "Civil"])
    option = st.radio("Select Option", ("Select","Upload Image"))
    if option == "Upload Image":
        # Read in the uploaded image
        uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"],accept_multiple_files=True)
        img=[]
        img_np=[]
        if uploaded_file is not None:
            for i in uploaded_file:
                file_bytes = i.getvalue()
                nparr = np.frombuffer(file_bytes, np.uint8)
                img.append(Image.open(uploaded_file))
                #img = [x.convert("RGB") for x in img]   
                img = [x.resize((1920,1080)) for x in img]
            st.subheader("Uploaded Image: ")
            st.image(img,channels="RGB")
            option = st.radio("Select Option", ("Select","DeHazing", "No Dehazing"))
            if option == "Select":
                input()
            if option =="No Dehazing":
                img_np=np.array(img)
            if option == "DeHazing":
                st.write("""Please wait for image to be dehazed.""")
                img_np = np.array(img)
                HazeCorrectedImg, HazeMap = image_dehazer.remove_haze(img_np,boundaryConstraint_windowSze=3,showHazeTransmissionMap=False)
                img = Image.fromarray(HazeCorrectedImg)
                img_np = np.array(img)
                st.subheader("DeHazed Image:")
                st.image(img)
            st.write("""Face Detection and Tagging in progress....""")
            print("Face Detection")
            img_loc = face_recognition.face_locations(img_np,number_of_times_to_upsample=3,model="hog")
            img_enc = face_recognition.face_encodings(img_np,known_face_locations=img_loc)
            face_img = PIL.Image.fromarray(img_np)
            print("Face Tagging")
            unknown_faces_location = []
            unknown_faces_enconded = []
            cnt=0
            for i in range(0,len(img_enc)):
                best_match_count = 0
                best_match_name = "unknown"
                for k,v in people.items():
                    result = face_recognition.compare_faces(v,img_enc[i],tolerance=0.45)
                    count_true = result.count(True)
                    if  count_true > best_match_count: # To find the best person that matches with the face
                        best_match_count = count_true
                        best_match_name = k
                if best_match_name != "unknown":
                    a,b=best_match_name.split("_")
                    stud_list["name"].append(a)
                    stud_list["usn"].append(b)
                else:
                    cnt=cnt+1
                # Draw and write on photo
                top,right,bottom,left = img_loc[i]
                draw = PIL.ImageDraw.Draw(face_img)
                font = PIL.ImageFont.load_default()
                draw.rectangle([left,top,right,bottom], outline="red", width=3)
                draw.rectangle((left, bottom, left + font.getsize(best_match_name)[0] , bottom +  font.getsize(best_match_name)[1]*1.2), fill='black')
                draw.text((left,bottom), best_match_name, font=font )
            st.write("""Face Detection and Tagging completed!!""")
            st.image(face_img)
            stud_list["name"].append("Unknown Faces")
            stud_list["usn"].append(cnt)
            st.subheader("Students detected from Uploaded Images are:")
            st.dataframe(pd.DataFrame(stud_list))
            st.write("Since there are "+ str(cnt) + " unknown faces. It is suggested the professor must take Manual Attendance also")
if __name__ == '__main__':
    main()
