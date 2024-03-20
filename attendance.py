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
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from firebase_config import initialize_firebase
from utils import load_known_encodings_and_ids
from webcam_capture import webcam_capture
import pytz
from PIL import Image

# Load your logo image
logo = Image.open("e:\FINAL_PROJECT\FDP-main\cmr.png")

# Display the logo and navigation bar
st.image(logo, width=150)
# Add a welcome message and a description of the attendance system
bucket, ref, encodings_ref = initialize_firebase()

local_tz = pytz.timezone('Asia/Kolkata')
            
def main():
    # st.title("Student Attendance System")
    menu = ["Home","Store Student Details","Store Student Image","Store Encodings" ,"Take Attendance", "Check Attendance"]
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

    elif choice == "Store Student Details":
        store_student_details()

    elif choice == "Store Student Image":
        store_image()
    elif choice == "Store Encodings":
        store_encodings()

    elif choice == "Take Attendance":
        take_attendance()

    elif choice == "Check Attendance":
        check_attendance()

def store_student_details():
    st.subheader("Store Student Details")
    student_id = st.text_input("Student ID")
    name = st.text_input("Name")
    department = st.text_input("Department")
    joined = st.text_input("Year of Joining")
    semester = st.text_input("Semester")
    section = st.text_input("Section")
    now = datetime.datetime.now(local_tz)
    if st.button('Submit'):
        # Store the data in Firebase
        data = {
            'name': name,
            'department': department,
            'joined': joined,
            'total_attendance': 0,
            'semester': semester,
            'section': section,
            'last_attendance': str(now.strftime("%Y-%m-%d %H:%M:%S"))
        }
        ref.child(student_id).set(data)

        st.success('Success! Data submitted for ' + name)
#  Original one
# def store_image():
#     st.subheader("Store Image")
#     usn = st.text_input("Enter the USN of the student:")
#     if st.button('Take Photo'):
#         # Create the "Images" folder if it does not exist
#         if not os.path.exists("Images"):
#             os.makedirs("Images")
#         # Initialize the webcam
#         cap = cv2.VideoCapture(0)

#         # Take a single photo
#         while True:
#             # Capture a frame from the webcam
#             ret, frame = cap.read()

#             # Display the frame
#             cv2.imshow("Webcam", frame)

#             # Check if the user pressed 'q' to quit
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break

#             # Check if the user clicked the left mouse button
#             if cv2.waitKey(1) & 0xFF == ord(' '):  # Space bar is ASCII 32
#                 # Save the photo as "USN.jpg" in the "Images" folder
#                 file_name = f"Images/{usn}.jpg"
#                 cv2.imwrite(file_name, frame)
#                 st.write(f"Saved photo as {file_name}")

#                 # Upload the image to Firebase Storage
#                 blob = bucket.blob("Images/" + f"{usn}.jpg")

#                 blob.upload_from_filename(file_name)

#                 st.write(f"Saved photo to Firebase Storage with URL {blob.public_url}")

#                 break

#         # Release the webcam
#         cap.release()

#         # Destroy all windows
#         cv2.destroyAllWindows()

## Encodings IDEA
# Load existing encodings and student IDs
with open("e:\FINAL_PROJECT\FDP-main\EncodeFile.p", "rb") as f:
    encodeKnown, studId = pickle.load(f)




#
# '''
#     Add class for store_image and return the object then in the main driver function call like this

#         image = storeImage()
#         image.get_encoding()

#     or  

#         storeimage().get_encoding()
# '''

# Giving options to the users
def store_image():
    st.subheader("Store Image")
    option = st.radio("Enter USN first then Select Option", ("Upload Image", "Take Photo"))
    usn = st.text_input("Enter the USN of the student:")

    def get_encoding(image_path):
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(img)
        if len(face_locations) > 0:
            encode = face_recognition.face_encodings(img, face_locations)[0]
            return encode
        return None
    

    #Use switch statement for options, abstract the details of the code in a seperate class


    if option == "Upload Image":
        uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            # Show a preview of the uploaded image
            st.image(img, caption="Preview of the uploaded image", width = 200)

            # Add an "Upload" button
            if st.button("Upload"):
                file_name = f"Images/{usn}.jpg"
                with open(file_name, "wb") as f:
                    f.write(file_bytes)  # Use file_bytes instead of uploaded_file.read()
                st.write(f"Saved photo as {file_name}")
                # Upload the image to Firebase Storage
                blob = bucket.blob("Images/" + f"{usn}.jpg")
                blob.upload_from_filename(file_name)
                st.write(f"Saved photo to Firebase Storage with URL {blob.public_url}")

                 # Calculate and store the encoding of the new student's image
                new_encoding = get_encoding(file_name)
                if new_encoding is not None:
                    encodeKnown.append(new_encoding)
                    studId.append(usn)

                    # Update the pickle file
                    with open("EncodeFile.p", "wb") as f:
                        pickle.dump([encodeKnown, studId], f)
                    st.success("Encodings updated successfully.")
                else:
                    st.warning("Could not detect a face in the uploaded image.")

    elif option == "Take Photo":
        # Create the "Images" folder if it does not exist
        if not os.path.exists("Images"):
            os.makedirs("Images")
        
        def capture_photo():
            # Initialize the webcam
            cap = cv2.VideoCapture(0)
            st.write("Please look at the camera and come a little closer. The camera will automatically capture your photo once your face is properly detected.")

            # Take a single photo
            while True:
                # Capture a frame from the webcam
                ret, frame = cap.read()

                # Resize image for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

                # Detect faces in the frame
                face_locations = face_recognition.face_locations(small_frame)

                # If a face is detected, capture the photo
                if len(face_locations) == 1:
                    file_name = f"Images/{usn}.jpg"
                    cv2.imwrite(file_name, frame)
                    st.write(f"Saved photo as {file_name}")

                    # Upload the image to Firebase Storage
                    blob = bucket.blob("Images/" + f"{usn}.jpg")
                    blob.upload_from_filename(file_name)
                    st.write(f"Saved photo to Firebase Storage with URL {blob.public_url}")
                    new_encoding = get_encoding(file_name)
                    if new_encoding is not None:
                        encodeKnown.append(new_encoding)
                        studId.append(usn)

                        # Update the pickle file
                        with open("EncodeFile.p", "wb") as f:
                            pickle.dump([encodeKnown, studId], f)
                        st.success("Encodings updated successfully.")
                    else:
                        st.warning("Could not detect a face in the captured photo.")
                    break

                # Check if the user pressed 'q' to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # Release the webcam
            cap.release()

            # Destroy all windows
            cv2.destroyAllWindows()
            
            return file_name

        if st.button("Take Photo"):
            captured_photo = capture_photo()
            st.image(captured_photo, caption=f"Captured photo for USN {usn}", width=200)


def store_encodings():
    st.subheader("Store Encodings")
    if st.button("Click to store encodings"):
        subprocess.run(["python", "encoding.py"])
        st.success('Success! Encodings stored.')  

#  Old one changing it completely
# def take_attendance():
#     st.subheader("Take Attendance")
#     if st.button("Take Attendance"):
#         subprocess.run(["python", "main.py"])
#     # Add code to take attendance using saved images
#         st.success('Success! Attendance marked')

# New one with enhanced options
import dlib
def _css_to_rect(css):
    return dlib.rectangle(css.left(), css.top(), css.right(), css.bottom())

def take_attendance():
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
        uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            # Read in the uploaded image
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            # Resize image for faster processing
            img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
            


            # Detect faces in the image
            face_locations = face_recognition.face_locations(img) # model="cnn"

            face_encodings = face_recognition.face_encodings(img, face_locations)

            # Load known encodings and student IDs
            encodeKnown, studId = load_known_encodings_and_ids()

            # Loop through each face encoding detected in the uploaded image
            marked_students = 0
            for face_encoding in face_encodings:
                # Find the closest matching known encoding
                distances = face_recognition.face_distance(encodeKnown, face_encoding)
                min_distance_index = np.argmin(distances)
                min_distance = distances[min_distance_index]

                # Set a threshold for the minimum distance to consider a match
                threshold = 0.7

                # If the minimum distance is below the threshold, mark attendance
                if min_distance < threshold:
                    id = studId[min_distance_index]
                    studentInfo = db.reference(f'Students/{id}').get()
                    if studentInfo is not None:
                        datetimeObject = datetime.datetime.strptime(studentInfo['last_attendance'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=local_tz)
                        secondsElapsed = (datetime.datetime.now(local_tz) - datetimeObject).total_seconds()

                        if secondsElapsed > 30:
                            ref = db.reference(f'Students/{id}')
                            studentInfo['total_attendance'] += 1
                            ref.child('total_attendance').set(studentInfo['total_attendance'])
                            ref.child('last_attendance').set(datetime.datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S"))
                            marked_students += 1
                        else:
                            st.warning(f"{studentInfo['name']}'s attendance was already marked within the last 30 seconds.")
                    else:
                        st.warning(f"No student found with ID {id}.")

            if marked_students == 0:
                st.warning("No matching faces found in the uploaded image.")
            else:
                st.success(f"Attendance marked for {marked_students} students.")
    st.subheader("Manual Attendance")
    st.write("Mark attendance for students who were not detected:")

    if "load_unmarked_students" not in st.session_state:
        st.session_state.load_unmarked_students = False

    if st.button("Load Unmarked Students"):
        st.session_state.load_unmarked_students = True

    if st.session_state.load_unmarked_students:
        # Get the attendance data from the "Students" node in the Firebase database
        attendance_ref = db.reference('Students')
        attendance_data = attendance_ref.get()
        attendance_df = pd.DataFrame.from_dict(attendance_data, orient='index')
        attendance_df = attendance_df[(attendance_df['semester'] == str(semester)) & (attendance_df['section'] == section) & (attendance_df['department'] == department)]

        # Get the last attendance date and time from the "last_attendance" column
        last_attendance = attendance_df["last_attendance"]

        # Check if the last attendance date matches today's date
        today = datetime.datetime.now(local_tz).strftime("%Y-%m-%d")
        absent_students = []
        for i, date_time in last_attendance.items():
            date = date_time.split(" ")[0]
            if date != today:
                absent_students.append(i)

        # Show the list of students who were not marked present today and use checkboxes
        students_to_mark = {}
        if len(absent_students) > 0:
            st.write("Students not marked present today:")
            for usn in absent_students:
                students_to_mark[usn] = st.checkbox(f"{usn}: {attendance_data[usn]['name']}")

            # Provide an option to mark attendance manually
            if st.button("Mark Attendance"):
                for usn, mark_attendance in students_to_mark.items():
                    if mark_attendance:
                        studentInfo = db.reference(f'Students/{usn}').get()
                        if studentInfo is not None:
                            ref = db.reference(f'Students/{usn}')
                            studentInfo['total_attendance'] += 1
                            ref.child('total_attendance').set(studentInfo['total_attendance'])
                            ref.child('last_attendance').set(datetime.datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S"))
                            st.success(f"Attendance marked for {studentInfo['name']}")
                        else:
                            st.warning(f"No student found with USN {usn}.")
        else:
            st.success("All students are marked present today.")


 
def check_attendance():
    st.subheader("Check Attendance")
    # Get the attendance data from the "Students" node in the Firebase database
    semester = st.selectbox("Select Semester", options=[1, 2, 3, 4, 5, 6, 7, 8])
    section = st.selectbox("Select Section", options=["A", "B", "C", "D"])
    department = st.selectbox("Select department", options = ["CSE", "ISE", "ECE", "EEE", "AI&ML", "DS", "Mech", "Civil"])

    attendance_ref = db.reference('Students')
    attendance_data = attendance_ref.get()

    # Create a pandas dataframe from the attendance data
    # attendance_df = pd.DataFrame.from_dict(attendance_data, orient='index')
    attendance_df = pd.DataFrame.from_dict(attendance_data, orient='index')
    attendance_df = attendance_df[(attendance_df['semester'] == str(semester)) & (attendance_df['section'] == section) & (attendance_df['department']==department)]


    # Get the last attendance date and time from the "last_attendance" column
    last_attendance = attendance_df["last_attendance"]
    present_today = 0

    # Check if the last attendance date matches today's date
    today = datetime.datetime.now(local_tz).strftime("%Y-%m-%d")
    for i, date_time in last_attendance.items():
        date = date_time.split(" ")[0]
        if date == today:
            present_today += 1

    # Display the attendance data in a table
    st.dataframe(attendance_df)

    # Display a message indicating the number of students present today
    if present_today == 0:
        st.warning("No students are present today.")
    else:
        # st.success(f"{present_today} students are present today!")
        st.success(f"{present_today} students are present in section {section} today!")

    # Create a button to download the CSV file
    csv = attendance_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="attendance.csv">Download CSV file</a>'
    # st.markdown(href, unsafe_allow_html=True)
    st.download_button(label="Download CSV file", data=csv, file_name=f"attendance_{today}.csv", mime="text/csv")


if __name__ == '__main__':
    main()
