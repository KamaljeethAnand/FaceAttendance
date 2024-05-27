import streamlit as st
from streamlit_gsheets import GSheetsConnection
from pathlib import Path
import streamlit_authenticator as stauth
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
import dlib

# --- USER AUTHENTICATION ---
names = ["CMRIT_Admin", "CMRIT_Professor"]
usernames = ["cmradmin", "cmrprof"]

# load hashed passwords
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
    "facerec", "abcdef", cookie_expiry_days=100)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:

    # CMRIT LOGO
    logo = Image.open("cmr.png")
    
    # Display the logo and navigation bar
    st.image(logo, width=150)
    #GOOGLE SHEETS
    url = "https://docs.google.com/spreadsheets/d/1lUzHTg-J13V0jxMqcd0_15WbQ7o8zSXFWi-Z03aKzng/"
    conn = st.connection("gsheets", type=GSheetsConnection,ttl=1)

    stud_list = {
            "name": [],
            "usn":[]
    }
    if 'sl' not in st.session_state:
        st.session_state.sl = stud_list

    cnt=-1
    absent_list={
            "name": [],
            "usn":[]
    }
    if 'al' not in st.session_state:
        st.session_state.al = absent_list
    local_tz = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(local_tz)           
    def main():
        # st.title("Student Attendance System")
        authenticator.logout("Logout","sidebar")
        st.sidebar.title(f"Welcome {name}")
        menu = ["Home","Take Attendance","Manual Attendance","Reports"]
        choice = st.sidebar.selectbox("Select Option", menu)

        if choice == "Home":

            st.title("Welcome to the Attendance System")
            st.write(
                """
                This attendance system uses facial recognition to mark attendance for students.
                It allows the teacher to upload images of the classroom in order to get the list of students present in the class. 

                """
            )
                
            st.write("Check [Google Sheets](%s) for updated attendance list!!!" % url)    
            st.write(str(now.strftime("%a|%d/%b/%Y|%H:%M")))
            df = conn.read(spreadsheet=url,worksheet="REPORT CONSOLIDATED",ttl=10)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.index=df.index+1    
            st.write(pd.DataFrame(df))    
            
        if choice == "Take Attendance":
            take_attendance()
        if choice == "Manual Attendance":
            st.title("Manual Attendance")    
            manualattendance()
        if choice == "Reports":
            reports()
    
    # Load existing encodings and student IDs
    def reports():
        df = conn.read(spreadsheet=url,worksheet="REPORT CONSOLIDATED",usecols=[0,1,2],ttl=30)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        manual_attdn=st.multiselect("Select Student:",df["Name"])
        if len(manual_attdn)>0:
            for ma in manual_attdn:
                x=df["Name"]
                st.write(x)
                y=[index(df['Name']) for ma in df["Name"]]
                st.write(y)
                st.write(df.loc[df[0]])
                # absent_list["usn"][absent_list["name"].index(ma)]

        totalp = sum(1 for v in df["Name"] if v=="P")
        percentp=round(totalp * 100 / (len(df["Name"].values) - 1), 2)    

    def manualattendance():
        stud_list=st.session_state.sl
        absent_list=st.session_state.al  
        ma_list = {
            "name": [],
            "usn":[]
        }   
        if len(stud_list["name"])>0:
            st.subheader("Students detected are:")
            st.dataframe(pd.DataFrame(stud_list,index=range(1, len(stud_list["name"])+1)))
            st.subheader("Absentee List:")
            st.dataframe(pd.DataFrame(absent_list,index=range(1, len(absent_list["name"])+1)))    
            st.subheader("Manual Attendance")
            manual_attdn=st.multiselect("Choose the students to be included:",absent_list["name"])
            if len(manual_attdn)>0:
                for ma in manual_attdn:
                    if ma not in ma_list["name"]:
                        ma_list["name"].append(ma)
                        ma_list["usn"].append(absent_list["usn"][absent_list["name"].index(ma)])
                st.subheader("Selected Students:")
                st.dataframe(pd.DataFrame(ma_list,index=range(1, len(ma_list["name"])+1)))   
                r=st.button("Confirm")
                if r:  
                    for a in ma_list["name"]:
                        if a not in stud_list["name"]:   
                            stud_list["name"].append(a)
                    for a in ma_list["usn"]:
                        if a not in stud_list["usn"]:   
                            stud_list["usn"].append(a)     
                    st.dataframe(pd.DataFrame(stud_list,index=range(1, len(stud_list["name"])+1)))

                    shname = st.session_state.shname
                    conn.create(worksheet=shname, data=pd.DataFrame(stud_list,index=range(1, len(stud_list["name"])+1)))
                    # df for Report Consolidated sheet 
                    df = conn.read(spreadsheet=url,worksheet="REPORT CONSOLIDATED",ttl=30)
                    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                    # df2 for newly created attendance sheet 
                    conn2 = st.connection("gsheets", type=GSheetsConnection,ttl=1)    
                    df2 = conn2.read(spreadsheet=url,worksheet=shname)  
                    # Check if each name in df exists in df2
                    df[shname] = df['Name'].isin(df2['name'])
                    df[shname] = df[shname].map({True: 'P', False: 'A'})
                    
                    totalp = sum(1 for v in df[shname] if v=="P")
                    percentp=round(totalp * 100 / (len(df["Name"].values) - 1), 2)     
                    st.subheader("CONSOLIDATED REPORT")
                    st.write("Total Students Present: "+ str(totalp))
                    st.write("% Students Present: "+ str(percentp) + "%") 
                    st.write(pd.DataFrame(df,index=range(1, len(df["Name"]))))
                    # Updating the Google Sheets
                    conn.update(worksheet="REPORT CONSOLIDATED", data=df)
                    st.write("Attendance marked for "+ str(len(stud_list["name"])) + ".Check the updated [Google Sheets](%s)!!!" % url)
                    shname=" "
                    stud_list["name"]=[]
                    stud_list["usn"]=[]    
    def take_attendance():
        with open('encoded_people.pickle', 'rb') as filename:
            people = pickle.load(filename)
        st.subheader("Take Attendance")
        semester = st.selectbox("Select Semester", options=[1, 2, 3, 4, 5, 6, 7, 8])
        section = st.selectbox("Select Section", options=["A", "B", "C", "D"])
        department = st.selectbox("Select department", options = ["CSE", "ISE", "ECE", "EEE", "AI&ML", "DS", "Mech", "Civil"])
        shname= str(semester) + "|"+str(section) +"|"+str(department) +"|"+str(now.strftime("%a|%d/%b/%Y|%H:%M"))
        option = st.radio("Select Option", ("Upload Image","Take Live Image"))
        img=[]
        img_np=[]
        if True:
            if option == "Upload Image":   
            # Read in the uploaded image
                uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"],accept_multiple_files=True)
            # Read in the live image from camera
            if option == "Take Live Image":
                uploaded_file=list()
                pic = st.camera_input("Choose an image file")
                uploaded_file.append(pic)
            if uploaded_file is not None and len(uploaded_file) !=0:
                for i in uploaded_file:
                    file_bytes = i.getvalue()
                    nparr = np.frombuffer(file_bytes, np.uint8)
                    img.append(Image.open(i)) 
                    img = [x.resize((1920,1080)) for x in img]
                st.subheader("Uploaded Image: ")
                st.image(img,channels="RGB")
                for k,v in people.items():
                    x,y=k.split("_")   
                    absent_list["name"].append(x)
                    absent_list["usn"].append(y)
                option = st.radio("Select Option", ("Select Dehazing/No Dehazing","DeHazing", "No Dehazing"))
                if option == "Select Dehazing/No Dehazing":
                    input()
                elif option =="No Dehazing":
                    for i in img:
                        img_np.append(np.array(i))
                    dehaze_img=[]
                    dehaze_imgnp=[]
                    final_images=[]
                    for i in img_np:
                        dehaze_imgnp.append(np.array(i))
                        dehaze_img.append(Image.fromarray(i))
                    for i in dehaze_img:
                        dehaze_imgnp.append(np.array(i)) 
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
                for x in dehaze_imgnp:
                    img_loc = face_recognition.face_locations(x,number_of_times_to_upsample=3,model="hog")
                    img_enc = face_recognition.face_encodings(x,known_face_locations=img_loc,num_jitters=1)
                    face_img = PIL.Image.fromarray(x)
                #Face Tagging
                    unknown_faces_location = []
                    unknown_faces_enconded = []
                    for i in range(0,len(img_enc)):
                        best_match_count = 0
                        best_match_name = "unknown"
                        for k,v in people.items():
                            result = face_recognition.compare_faces(v,img_enc[i],tolerance=0.475)
                            count_true = result.count(True)
                            if  count_true > best_match_count: # To find the best person that matches with the face
                                best_match_count = count_true
                                best_match_name = k
                        if best_match_name != "unknown":
                            a,b=best_match_name.split("_")
                            if a not in stud_list["name"]:
                                stud_list["name"].append(a)
                                stud_list["usn"].append(b)
                        # else:
                            # cnt=cnt+1
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
                for a in stud_list["name"]:
                    if a in absent_list["name"]:   
                            absent_list["usn"].remove(absent_list["usn"][absent_list["name"].index(a)])
                            absent_list["name"].remove(a)
                st.subheader("Students detected from Uploaded Images are:")
                st.dataframe(pd.DataFrame(stud_list,index=range(1, len(stud_list["name"])+1)))
                st.subheader("Absentees:")
                st.dataframe(pd.DataFrame(absent_list,index=range(1, len(absent_list["name"])+1)))    
                st.write("Proceed to Manual Attendance tab for adding more students!!!")  
                st.session_state.sl = stud_list
                st.session_state.al = absent_list
                st.session_state.shname =shname
                
    if __name__ == '__main__':
        main()
