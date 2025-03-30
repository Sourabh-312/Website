import os
import uuid
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from supabase import create_client, Client
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# Supabase Configuration (Using Anon Key)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

@app.route("/")
def index():
    """Render the main page"""
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    """Handle media uploads (photo, video, and location)"""

    # Generate unique user ID (UUID)
    user_id = f"user_{uuid.uuid4().hex[:6]}"  
    cloudinary_folder = f"SUS CAPTURE/{user_id}"  # Store in 'SUS CAPTURE' folder

    # Process Image Upload
    image_url = None
    image_file = request.files.get("image")
    if image_file:
        image_upload = cloudinary.uploader.upload(image_file, folder=cloudinary_folder)
        image_url = image_upload["secure_url"]
        
        # Upload to Supabase Storage
        supabase_client.storage.from_("uploads").upload(f"{user_id}/photo.jpg", image_file.read())

    # Process Video Upload
    video_url = None
    video_file = request.files.get("video")
    if video_file:
        video_upload = cloudinary.uploader.upload(video_file, folder=cloudinary_folder, resource_type="video")
        video_url = video_upload["secure_url"]

        # Upload to Supabase Storage
        supabase_client.storage.from_("uploads").upload(f"{user_id}/video.webm", video_file.read())

    # Process Location Data
    location_url = None
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    
    if latitude and longitude:
        location_data = f"Latitude: {latitude}\nLongitude: {longitude}"
        location_filename = f"{user_id}_location.txt"

        # Upload to Cloudinary as Text File
        encoded_location = base64.b64encode(location_data.encode()).decode()
        location_upload = cloudinary.uploader.upload(
            f"data:text/plain;base64,{encoded_location}",
            folder=cloudinary_folder,
            public_id=location_filename,
            resource_type="raw"
        )
        location_url = location_upload["secure_url"]

        # Upload to Supabase Storage
        supabase_client.storage.from_("uploads").upload(f"{user_id}/location.txt", location_data.encode())

    # Store Data in Supabase Table
    data = {
        "user_id": user_id,
        "photo_url": image_url,
        "video_url": video_url,
        "latitude": latitude,
        "longitude": longitude,
    }
    
    supabase_client.table("user_data").insert(data).execute()

    return jsonify({
        "user_id": user_id,
        "image_url": image_url,
        "video_url": video_url,
        "location_url": location_url
    })

if __name__ == "__main__":
    app.run(debug=True)
