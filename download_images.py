import csv
import logging
import os
import pickle
import requests
import sys

from datetime import datetime
from io import BytesIO
from PIL import Image
from pillow_heif import register_heif_opener

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

log = logging.getLogger()
logging.basicConfig(level=logging.INFO)

register_heif_opener()


class DownloadImages:

    credentials: Credentials
    csv_output: list = list()

    # Select the column where the data is
    # A->0, B->1, C->2, D->3, E->4,
    # F->5, G->6, H->7 I->8, K->9
    NAME_IDX = 1
    NATIONALITY_IDX = 2
    DATEOFBIRTH_IDX = 3
    PHOTOURL_IDX = 4

    def __init__(self, csv_file):
        self.authenticate()
        self.parse_input_csv(csv_file)
        self.save_csv_output()

    def authenticate(self, token_path: str = "token.pickle", client_secret_path: str = "client_secret.json"):
        SCOPES = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive.metadata'
        ]

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                credentials = pickle.load(token)
        else:
            credentials = None

        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret_path, SCOPES)
                credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'wb') as token:
                pickle.dump(credentials, token)

        self.credentials = credentials

    def download_file(self, file_id: str, destination: str):
        response = requests.get(
            "https://www.googleapis.com/drive/v3/files/{}?alt=media".format(
                file_id),
            params={'id': id},
            stream=True,
            headers={'Authorization': 'Bearer {}'.format(
                self.credentials.token)},
            timeout=10
        )

        # Handle problems with download
        if response.status_code != 200:
            log.error(
                f"Downloading file ID {file_id} failed! The picture wont be saved!")
            log.error(response.text)
            return

        if "image" not in response.headers["Content-Type"]:
            log.info(response.headers["Content-Type"])
            log.error(
                f"""File ID {file_id} is not a picture! 
                They probably uploaded the wrong thing, like PDF or something. 
                You will nedd to get it from them and save it to the picture folder 
                under '{destination}'""")

        # This conversion is needed in case users upload HEIF or other format photos.
        # The face detector can only take JPEG files
        datatype = response.headers.get("Content-Type")
        if datatype == "image/jpeg":
            with open(destination, "wb") as f:
                f.write(response.content)
        else:
            log.warning(
                f"The user is using weird photo format [{datatype}]. Attempting covnersion.")
            buf = BytesIO(response.content)
            img = Image.open(buf)
            img.convert("RGB").save(destination, "JPEG")

        log.debug(f"Saved {destination}")

    def get_file_id(self, file_url: str) -> str:
        # Example https://drive.google.com/open?id=1REKpuL5TUKwNvupg9_f5EzAIrcFPGt
        # So only return stuff after "="
        return file_url.split("=")[1]

    def parse_date_of_birth(self, raw_date: str) -> datetime:
        try:
            dt = datetime.strptime(raw_date, "%m/%d/%Y").date()
            return dt.strftime("%d  %m  %y")
        except ValueError:
            log.error(
                f"Value '{raw_date}' does not match the mm/dd/yyyy date format!")
            exit()

    def save_csv_output(self, filename: str = "students.csv"):
        with open(filename, "w+") as f:
            csv_writer = csv.writer(f)
            for row in self.csv_output:
                csv_writer.writerow(row)

    def process_line(self, line: str):
        name = line[self.NAME_IDX].strip()
        date_of_birth = self.parse_date_of_birth(line[self.DATEOFBIRTH_IDX])
        nationality = line[self.NATIONALITY_IDX].strip().capitalize()
        file_id = self.get_file_id(line[self.PHOTOURL_IDX])
        today = datetime.now().strftime("%d  %m  %y")

        log.info(f"Processing: {name}")

        img_destination = os.path.join(os.getcwd(), "pictures", f"{name}.jpg")
        if not os.path.exists(img_destination):
            self.download_file(file_id, img_destination)

        self.csv_output.append(
            [name, date_of_birth, nationality, today, img_destination])

    def parse_input_csv(self, csv_path):
        """Opens the file exported from google sheets, processes the input data
        and downloads all images from drive and aves them to folder for generation."""
        with open(csv_path, "r") as f:
            csv_reader = csv.reader(f)
            next(csv_reader)
            for line in csv_reader:
                log.debug(f"Processing {line}")
                self.process_line(line)


if __name__ == "__main__":
    DownloadImages(sys.argv[1])
