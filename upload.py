import os
import io
import random
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.credentials import Credentials

# ==============================
# GOOGLE DRIVE FOLDER IDS (CHANGE LATER)
# ==============================

PENDING_FOLDER_ID = "PASTE_PENDING_FOLDER_ID"
UPLOADED_FOLDER_ID = "PASTE_UPLOADED_FOLDER_ID"

# ==============================
# AUTH
# ==============================

creds = Credentials(
    None,
    refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["YOUTUBE_CLIENT_ID"],
    client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
    scopes=[
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/drive"
    ]
)

youtube = build("youtube", "v3", credentials=creds)
drive = build("drive", "v3", credentials=creds)

# ==============================
# GET FILES FROM DRIVE
# ==============================

results = drive.files().list(
    q=f"'{PENDING_FOLDER_ID}' in parents and mimeType='video/mp4'",
    fields="files(id, name)"
).execute()

files = results.get("files", [])

if not files:
    raise Exception("No MP4 videos found in pending folder")

video = random.choice(files)
file_id = video["id"]
file_name = video["name"]

title = file_name.replace(".mp4", "")

print("Downloading:", file_name)

# ==============================
# DOWNLOAD FILE
# ==============================

request = drive.files().get_media(fileId=file_id)
fh = io.FileIO(file_name, "wb")
downloader = MediaIoBaseDownload(fh, request)

done = False
while not done:
    status, done = downloader.next_chunk()

# ==============================
# UPLOAD TO YOUTUBE
# ==============================

media = MediaFileUpload(file_name, mimetype="video/mp4", resumable=True)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": title,
            "description": "#shorts",
            "categoryId": "15"
        },
        "status": {
            "privacyStatus": "public"
        }
    },
    media_body=media
)

response = request.execute()

video_id = response.get("id")
print("Uploaded:", video_id)

# ==============================
# MOVE FILE
# ==============================

drive.files().update(
    fileId=file_id,
    addParents=UPLOADED_FOLDER_ID,
    removeParents=PENDING_FOLDER_ID
).execute()

os.remove(file_name)

print("Moved and cleaned:", file_name)
