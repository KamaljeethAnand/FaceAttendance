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
if 'sl' not in st.session_state:
    st.session_state.sl = stud_list

cnt=0
absent_list=[]
if 'al' not in st.session_state:
    st.session_state.al = absent_list
local_tz = pytz.timezone('Asia/Kolkata')
now = datetime.datetime.now(local_tz)           
def main():
    # st.title("Student Attendance System")
    menu = ["Home","Take Attendance","Manual Attendance"]
    choice = st.sidebar.selectbox("Select Option", menu)

    if choice == "Home":

        st.title("Welcome to the Attendance System")
        st.write(
            """
            This attendance system uses facial recognition to mark attendance for students.
            It allows the teacher to upload images of the classroom in order to get the list of students present in the class. 

            """
        )
        st.write(str(now.strftime("%a:%d/%b/%Y"))) 
    if choice == "Take Attendance":
        take_attendance()
    if choice == "Manual Attendance":
        st.title("Here, you can take Manual Attendance of students!!!")    
        manualattendance()

# Load existing encodings and student IDs

# New one with enhanced options
import dlib
# if "clkd" not in st.session_state:
#     st.session_state.clkd=False
# def callback():
#     st.session_state.clkd=True
def manualattendance():
    stud_list=st.session_state.sl
    absent_list=st.session_state.al
    ma_list = {
        "name": [],
        "usn":[]
    }   
    if len(stud_list)>0:
        st.subheader("Students detected are:")
        st.dataframe(pd.DataFrame(stud_list))
        st.subheader("Absentee List:")
        st.dataframe(pd.DataFrame(absent_list))    
        st.write("Since there are "+ str(cnt) + " unknown faces.")
        opt = st.radio("Do you want to add more students:", ("Select","Yes", "No"))
        if opt=="Select":
            input()
        elif opt == "Yes":
            st.subheader("Manual Attendance")
            manual_attdn=st.multiselect("Choose the students to be included:",absent_list)
            if len(manual_attdn)>0:
                for ma in manual_attdn:
                    a,b=ma.split("_")
                    if a not in ma_list["name"]:
                        ma_list["name"].append(a)
                        ma_list["usn"].append(b)
                st.subheader("Selected Students:")
                st.dataframe(pd.DataFrame(ma_list))   
                r=st.button("Confirm")
                if r:
                    for a in ma_list["name"]:
                        if a not in stud_list["name"]:   
                            stud_list["name"].append(a)
                            stud_list["usn"].append(ma_list["usn"][ma_list["name"].index(a)])
                    
                    st.dataframe(pd.DataFrame(stud_list))
                    st.write("Attendance marked for "+ str(len(stud_list["name"])-1) + ".")     
        elif opt=="No":
            st.subheader("Final List of Students:")
            st.dataframe(pd.DataFrame(stud_list))
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
        if uploaded_file is not None and len(uploaded_file) !=0:
            for i in uploaded_file:
                file_bytes = i.getvalue()
                nparr = np.frombuffer(file_bytes, np.uint8)
                img.append(Image.open(i))
                #img = [x.convert("RGB") for x in img]   
                img = [x.resize((1920,1080)) for x in img]
            st.subheader("Uploaded Image: ")
            st.image(img,channels="RGB")
            for k,v in people.items():
                absent_list.append(k)    
            option = st.radio("Select Option", ("Select","DeHazing", "No Dehazing"))
            if option == "Select":
                input()
            elif option =="No Dehazing":
                for i in img:
                    img_np.append(np.array(i))
            elif option == "DeHazing":
                st.write("""Please wait for image to be dehazed.""")
                for i in img:
                    img_np.append(np.array(i))
                final_images=[]
                dehaze_img=[]
                dehaze_imgnp=[]    
                for i in img_np:
                    HazeCorrectedImg, HazeMap = image_dehazer.remove_haze(i,boundaryConstraint_windowSze=3,showHazeTransmissionMap=False)
                    dehaze_img.append(Image.fromarray(HazeCorrectedImg))
                for i in dehaze_img:
                    dehaze_imgnp.append(np.array(i)) 
                st.subheader("DeHazed Image:")
                st.image(dehaze_img,channels="RGB")
            st.write("""Face Detection and Tagging in progress....""")
            #Face Detection
            cnt=0    
            for x in dehaze_imgnp:
                img_loc = face_recognition.face_locations(x,number_of_times_to_upsample=3,model="hog")
                img_enc = face_recognition.face_encodings(x,known_face_locations=img_loc)
                face_img = PIL.Image.fromarray(x)
            #Face Tagging
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
                    if best_match_name != "unknown":
                        a,b=best_match_name.split("_")
                        if a not in stud_list["name"]:
                            stud_list["name"].append(a)
                            stud_list["usn"].append(b)
                        elif best_match_name in absent_list:
                            absent_list.remove(best_match_name)
                    else:
                        cnt=cnt+1
                # Draw and write on photo
                    top,right,bottom,left = img_loc[i]
                    draw = PIL.ImageDraw.Draw(face_img)
                    font = PIL.ImageFont.load_default()
                    draw.rectangle([left,top,right,bottom], outline="red", width=3)
                    draw.rectangle((left, bottom, left + font.getsize(best_match_name)[0] , bottom +  font.getsize(best_match_name)[1]*1.2), fill='black')
                    draw.text((left,bottom), best_match_name, font=font)
                final_images.append(face_img)
            st.write("""Face Detection and Tagging completed!!""")
            st.image(final_images)
            stud_list["name"].append("Unknown Faces")
            stud_list["usn"].append(cnt)
            st.subheader("Students detected from Uploaded Images are:")
            st.dataframe(pd.DataFrame(stud_list))
            st.subheader("Absentees:")
            st.dataframe(pd.DataFrame(absent_list))    
            st.write("Since there are "+ str(cnt) + " unknown faces. It is suggested the professor must take Manual Attendance also")
            st.write("Go to Manual Attendance tab for adding more students!!!")  
            st.session_state.sl = stud_list
            st.session_state.al = absent_list
            # with st.form("manattdn"):
            #     manattdn=st.form_submit_button("Manual Attendance")
            # if manattdn:
            #     st.subheader("Manual Attendance")
            #     with st.form("abslist"):
            #         manual_attdn=st.multiselect("Choose the students to be included:",absent_list)
            #         conf=st.form_submit_button("Confirm")
            #     if conf: 
            #         for ma in manual_attdn:
            #             a,b=ma.split("_")
            #         if a not in stud_list["name"]:
            #             stud_list["name"].append(a)
            #             stud_list["usn"].append(b)
            #         st.subheader("List of Students after Manual Attendance:")
            #         st.dataframe(pd.DataFrame(stud_list))
            

if __name__ == '__main__':
    main()
