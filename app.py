import os
import uuid
from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import supabase
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
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

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

    # Create the user's folder inside "SUS CAPTURE"
    cloudinary_folder = f"SUS CAPTURE/{user_folder}"

    # Process image
    image_file = request.files.get("image")
    if image_file:
        image_upload = cloudinary.uploader.upload(image_file, folder=cloudinary_folder)
        image_url = image_upload["secure_url"]
    else:
        image_url = None

    # Process video
    video_file = request.files.get("video")
    if video_file:
        video_upload = cloudinary.uploader.upload(video_file, folder=cloudinary_folder, resource_type="video")
        video_url = video_upload["secure_url"]
    else:
        video_url = None

    # Process location data
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    if latitude and longitude:
        location_data = f"Latitude: {latitude}\nLongitude: {longitude}"
        location_filename = f"{user_folder}_location.txt"

        # Upload location to Cloudinary (as a text file)
        encoded_location = base64.b64encode(location_data.encode()).decode()
        location_upload = cloudinary.uploader.upload(
            f"data:text/plain;base64,{encoded_location}",
            folder=cloudinary_folder,
            public_id=location_filename,
            resource_type="raw"
        )
        location_url = location_upload["secure_url"]
    else:
        location_url = None

    return jsonify({
        "image_url": image_url,
        "video_url": video_url,
        "location_url": location_url
    })

if __name__ == "__main__":
    app.run(debug=True)
