import os
import io
import random
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.credentials import Credentials

# ==============================
# GOOGLE DRIVE FOLDER IDS
# ==============================

PENDING_FOLDER_ID = "1TnjfCVkuLeYmPNJ2L8e1C2T-ZaX0Y5mU"
UPLOADED_FOLDER_ID = "1RjtlPgm9NM3r5-6nJK5nRjfTE2d9RKQz"

# ==============================
# TITLE ROTATION
# ==============================

TITLES = [
    "Baby Products That Your Child Will Love #shorts",
    "🛁 Perfect For Your New Born Child #shorts",
    "Must-Have Baby Essentials Every Parent Needs 👶✨ #shorts"
]

# ==============================
# DESCRIPTION ROTATION
# ==============================

DESCRIPTIONS = [
    "Discover must-have baby products every parent is loving right now 💛 Safe, useful, and perfect for your little one. #babyproducts #parenting #shorts",
    "Looking for baby essentials that actually make life easier? Here are smart picks for modern parents 👶✨ #newborn #babycare #shorts",
    "Top trending baby items parents swear by 🍼 Safe, practical, and loved by kids! #babylife #parentingtips #shorts"
]

# ==============================
# TAGS
# ==============================

TAGS = [
    "baby products",
    "baby essentials",
    "newborn baby",
    "baby care",
    "parenting tips",
    "baby must haves",
    "infant products",
    "mom life",
    "parent hacks",
    "shorts"
]

# ==============================
# AUTHENTICATION
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
# GET MP4 FILES FROM DRIVE
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

print("Downloading:", file_name)

# ==============================
# DOWNLOAD FILE LOCALLY
# ==============================

request = drive.files().get_media(fileId=file_id)
fh = io.FileIO(file_name, "wb")
downloader = MediaIoBaseDownload(fh, request)

done = False
while not done:
    status, done = downloader.next_chunk()

# ==============================
# PICK RANDOM TITLE + DESCRIPTION
# ==============================

selected_title = random.choice(TITLES)
selected_description = random.choice(DESCRIPTIONS)

# ==============================
# UPLOAD TO YOUTUBE
# ==============================

media = MediaFileUpload(file_name, mimetype="video/mp4", resumable=True)

request = youtube.videos().insert(
    part="snippet,status,recordingDetails",
    body={
        "snippet": {
            "title": selected_title,
            "description": selected_description,
            "tags": TAGS,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "license": "youtube"
        },
        "recordingDetails": {
            "location": {
                "latitude": 19.0760,
                "longitude": 72.8777
            },
            "recordingDate": datetime.utcnow().isoformat("T") + "Z"
        }
    },
    media_body=media
)

response = request.execute()

video_id = response.get("id")
print("Uploaded:", video_id)

# ==============================
# MOVE FILE TO UPLOADED FOLDER
# ==============================

drive.files().update(
    fileId=file_id,
    addParents=UPLOADED_FOLDER_ID,
    removeParents=PENDING_FOLDER_ID
).execute()

# ==============================
# DELETE LOCAL COPY
# ==============================

os.remove(file_name)

print("Moved and cleaned:", file_name)
