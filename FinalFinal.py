import cv2
import face_recognition
import os
import sqlite3
from datetime import datetime
from getpass import getpass
import tkinter as tk
from tkinter import messagebox

# Initialize variables
known_face_encodings = []
known_face_ids = []  # Change from known_face_names to known_face_ids
attendance_logged = set()

# Admin password
ADMIN_PASSWORD = "admin123"  # Replace this with your own secure password

# Database connection
DB_NAME = "attendance_system.db"

# Create database connection and table based on date, course name, section, and semester
def create_database(course_name, section, semester):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Sanitize inputs: Replace spaces and other problematic characters with underscores
    sanitized_course_name = course_name.replace(" ", "_")
    sanitized_section = section.replace(" ", "_")
    sanitized_semester = semester.replace(" ", "_")

    # Use the date and sanitized course name, section, and semester to create a dynamic table name
    date_today = datetime.now().strftime("%Y_%m_%d")  # Replacing hyphens with underscores
    table_name = f"{date_today}_{sanitized_semester}_{sanitized_course_name}_{sanitized_section}"

    # Wrap the table name with square brackets to avoid SQLite syntax issues
    table_name = f"[{table_name}]"

    # Create attendance table for that date and course
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL
        )
    ''')
    connection.commit()
    connection.close()
    return table_name

# Mark attendance by inserting into SQLite database
def mark_attendance(table_name, id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if attendance for this ID already exists
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    
    # Check if the ID already exists in the table for the given date
    cursor.execute(f'''SELECT * FROM {table_name} WHERE id = ?''', (id,))
    if cursor.fetchone():
        print(f"Attendance for ID {id} already inserted for today's attendance.")
        attendance_logged.add(id)  # Mark attendance as logged to prevent further printing
    else:
        try:
            cursor.execute(f'''INSERT INTO {table_name} (id, timestamp) VALUES (?, ?)''', (id, timestamp))
            connection.commit()
            print(f"Attendance marked for ID {id} at {timestamp}")
        except sqlite3.IntegrityError:
            print(f"Failed to mark attendance for ID {id} - IntegrityError")
    
    connection.close()

# Authenticate admin
def authenticate_admin():
    print("Admin access required to add a new face.")
    for _ in range(3):  # Allow up to 3 attempts
        password = getpass("Enter Admin Password: ")  # Hides password input
        if password == ADMIN_PASSWORD:
            print("Access granted.")
            return True
        else:
            print("Incorrect password. Try again.")
    print("Access denied.")
    return False

# Save the full frame when adding a new face
def save_new_face_without_box(frame, id, face_location, known_faces_folder):
    """
    Save the image without the bounding box.
    """
    # Extract the face location to save the image
    top, right, bottom, left = face_location
    
    # Crop the image to only include the face
    face_image = frame[top:bottom, left:right]

    # Save the cropped face image to the known_faces folder (without the bounding box)
    file_path = os.path.join(known_faces_folder, f"{id}.jpg")  # Save based on ID
    cv2.imwrite(file_path, face_image)  # Save the image without box

    # Update the known faces data
    image = face_recognition.load_image_file(file_path)
    encoding = face_recognition.face_encodings(image)[0]
    known_face_encodings.append(encoding)
    known_face_ids.append(id)

# Load known faces from the folder
def load_known_faces(folder_path):
    global known_face_encodings, known_face_ids
    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            # Load image
            image_path = os.path.join(folder_path, filename)
            image = face_recognition.load_image_file(image_path)
            
            # Get face encodings
            encodings = face_recognition.face_encodings(image)
            
            if encodings:  # Check if any faces are found
                encoding = encodings[0]  # Get the first encoding
                known_face_encodings.append(encoding)
                # Assuming the filename format is "ID.jpg", we take the ID as the name
                known_face_ids.append(os.path.splitext(filename)[0])
            else:
                print(f"No faces found in {filename}. Skipping.")

# GUI for course, section, and semester selection
def select_course_section_semester():
    root = tk.Tk()
    root.title("Course, Section, and Semester Selection")
    
    # Course, Section, and Semester options
    courses = ["SE_214", "SE_215", "SE_223", "SE_224","SE_221","SE_532"]
    sections = ["A", "B", "C", "D"]
    semesters = ["Spring 2025", "Fall 2025", "Summer 2025"]

    # Variables for selected options
    selected_course = tk.StringVar(root)
    selected_course.set(courses[0])  # Set default value

    selected_section = tk.StringVar(root)
    selected_section.set(sections[0])  # Set default value

    selected_semester = tk.StringVar(root)
    selected_semester.set(semesters[0])  # Set default value

    # Dropdown menus for course, section, and semester
    tk.Label(root, text="Select Course:").pack(pady=5)
    course_menu = tk.OptionMenu(root, selected_course, *courses)
    course_menu.pack(pady=5)

    tk.Label(root, text="Select Section:").pack(pady=5)
    section_menu = tk.OptionMenu(root, selected_section, *sections)
    section_menu.pack(pady=5)

    tk.Label(root, text="Select Semester:").pack(pady=5)
    semester_menu = tk.OptionMenu(root, selected_semester, *semesters)
    semester_menu.pack(pady=5)

    # Button to confirm selection
    def confirm_selection():
        course = selected_course.get()
        section = selected_section.get()
        semester = selected_semester.get()

        if not course or not section or not semester:
            messagebox.showerror("Input Error", "All fields must be selected.")
            return
        root.quit()  # Close the window

        # Proceed with course selection
        start_attendance_system(course, section, semester)

    confirm_button = tk.Button(root, text="Confirm", command=confirm_selection)
    confirm_button.pack(pady=20)

    root.mainloop()

# Start the attendance system with selected course, section, and semester
def start_attendance_system(course_name, section, semester):
    # Get the current working directory
    current_directory = os.getcwd()

    # Sanitize course name for folder and convert it to lowercase
    sanitized_course_name = course_name.replace(" ", "_").lower()

    # Create a folder for known faces based on course name (lowercase)
    folder_name = f"{sanitized_course_name}_{section}_{semester.replace(' ', '_').lower()}"

    # Full path to create the folder in the current directory
    full_folder_path = os.path.join(current_directory, folder_name)

    # Create the folder if it doesn't exist
    if not os.path.exists(full_folder_path):
        os.makedirs(full_folder_path)
        print(f"Created folder: {full_folder_path}")
    else:
        print(f"Folder {full_folder_path} already exists.")

    # Initialize database and load known faces
    table_name = create_database(course_name, section, semester)
    load_known_faces(full_folder_path)
    
    # Initialize video capture
    video_capture = cv2.VideoCapture(0)
    video_capture.set(3, 1280)  # Set width
    video_capture.set(4, 720)   # Set height

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        # Resize and convert color
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Face detection
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        # Process each face
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Scale back up face locations to original frame size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Compare faces
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            id = "Unknown"
            color = (0, 0, 255)  # Red for unknown face

            if True in matches:
                # If a match is found, update the ID
                first_match_index = matches.index(True)
                id = known_face_ids[first_match_index]
                color = (0, 255, 0)  # Green for known face
                
                # If attendance hasn't been marked for this ID yet, mark attendance
                if id not in attendance_logged:
                    mark_attendance(table_name, id)
                    attendance_logged.add(id)  # Add to the set to avoid re-printing the message
                else:
                    print(f"Attendance for ID {id} already marked.")
                      # Only print once

            else:
                # Draw bounding box and text for unknown faces in live feed
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, "Unknown - Press 'n' to save", 
                           (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 0.6, color, 1)

                if cv2.waitKey(1) & 0xFF == ord('n'):
                    if authenticate_admin():  # Verify admin access
                        id = input("Enter the ID of the person: ").strip().lower()  # Convert to lowercase
                        if id:
                            save_new_face_without_box(frame, id, (top, right, bottom, left), full_folder_path)  # Pass the folder path
                            print(f"Saved new face for ID {id}")
                            mark_attendance(table_name, id)

            # Draw bounding box and ID for known faces in live feed
            if id != "Unknown":
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, id, (left + 6, bottom - 6), 
                            cv2.FONT_HERSHEY_DUPLEX, 1.0, color, 1)

        # Display output with bounding boxes in live feed
        cv2.imshow('Attendance System', frame)

        # Exit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    select_course_section_semester()
