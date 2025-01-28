import sqlite3
from datetime import datetime

# Function to retrieve attendance data for all IDs on a specified date
def retrieve_all_attendance(course_name, section, semester, date_input):
    # Sanitize inputs: Replace spaces and other problematic characters with underscores
    sanitized_course_name = course_name.replace(" ", "_")
    sanitized_section = section.replace(" ", "_")
    sanitized_semester = semester.replace(" ", "_")

    # Format the date input as per the table name (should be in YYYY_MM_DD format)
    try:
        date_today = datetime.strptime(date_input, "%Y-%m-%d").strftime("%Y_%m_%d")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return

    # Create the table name using sanitized inputs and the formatted date
    table_name = f"{date_today}_{sanitized_semester}_{sanitized_course_name}_{sanitized_section}"

    # Wrap the table name with square brackets to avoid SQLite syntax issues
    table_name = f"[{table_name}]"

    # Connect to the database
    connection = sqlite3.connect("attendance_system.db")
    cursor = connection.cursor()

    try:
        # Retrieve all attendance records from the specified table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if rows:
            print(f"Attendance records for {course_name} - {section} - {semester} on {date_today}:\n")
            print(f"{'ID':<15} {'Timestamp':<20}")
            print("-" * 35)
            for row in rows:
                id, timestamp = row
                print(f"{id:<15} {timestamp:<20}")
        else:
            print(f"No attendance records found for {course_name} - {section} - {semester} on {date_today}.")
    except sqlite3.Error as e:
        print(f"Error retrieving data: {e}")
    finally:
        connection.close()

# Main function to interact with the user
def main():
    print("Please enter the following details:")

    # Prompt for course name, section, and semester
    course_name = input("Enter the course name (e.g., SE-223): ")
    section = input("Enter the section (e.g., A): ")
    semester = input("Enter the semester (e.g., Spring 2025): ")

    # Prompt for the date (in YYYY-MM-DD format)
    date_input = input("Enter the date (YYYY-MM-DD): ")

    # Retrieve and print all attendance for the given course, section, semester, and date
    retrieve_all_attendance(course_name, section, semester, date_input)

if __name__ == "__main__":
    main()
