import os.path
import csv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import pytz
import argparse

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/classroom.coursework.students"
    , "https://www.googleapis.com/auth/classroom.coursework.me"
    , "https://www.googleapis.com/auth/classroom.courses.readonly"
]

def create_classwork(course_id, creds, csv_file_path):

  """
  Creates the coursework the user has access to.
  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  try:
    service = build("classroom", "v1", credentials=creds)

    """
    Parsing the CSV file
    """
    
    with open(csv_file_path, 'r') as csv_file:
      reader = csv.reader(csv_file)
      
      #Skip the first line cause it's just the field names
      next(reader)
      for row in reader:
        print("row: ", row)

        """
        Figuring out timing 
        - Converting PDT to UTC
        """
        due_date = datetime.strptime(row[2], '%m/%d/%Y')
        due_time = datetime.strptime(row[3], '%I:%M %p')

        # Combine date and time into a single datetime object
        due_datetime = datetime.combine(due_date, due_time.time())

        # PDT timezone stuff
        pdt = pytz.timezone('America/Los_Angeles')
        due_datetime_pdt = pdt.localize(due_datetime)

        # Convert to UTC
        due_datetime_utc = due_datetime_pdt.astimezone(pytz.utc)
        
        coursework = {
            "title": row[0],
            "description": row[1],
            "state": "PUBLISHED",
            'dueDate': {
                'year': due_datetime_utc.year,
                'month': due_datetime_utc.month,
                'day': due_datetime_utc.day
            },
            'dueTime': {
                'hours': due_datetime_utc.hour,
                'minutes': due_datetime_utc.minute
            },
            "workType": "ASSIGNMENT",
            "assigneeMode": "ALL_STUDENTS"
        }
        coursework = (
            service.courses()
            .courseWork()
            .create(courseId=course_id, body=coursework)
            .execute()
        )
        print(f"Assignment created with ID {coursework.get('id')}")
      return coursework

  except HttpError as error:
    print(f"An error occurred: {error}")
    return error


def main():
  """

  Take the course ID as an argument. 
  """
  parser = argparse.ArgumentParser(description='Create assignments for a Google Classroom course.')
  parser.add_argument('course_id', type=str, help='The course ID where to create assignments')
  parser.add_argument('csv_file', type=str, help='The path to the CSV file containing assignment details')
  args = parser.parse_args()

  creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  create_classwork(args.course_id, creds, args.csv_file)




if __name__ == "__main__":
  # Put the course_id of course whose coursework needs to be created,
  # the user has access to.
  main()