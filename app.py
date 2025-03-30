import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from supabase import create_client
from flask import Flask, request, jsonify
import base64

# Load environment variables
load_dotenv()

# Flask App
app = Flask(__name__)

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Supabase Configuration
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)

@app.route("/")
def home():
    return jsonify({"message": "Backend is running!"})

# Upload Image/Video + Location to Cloudinary & Supabase
@app.route("/upload", methods=["POST"])
def upload_media():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    # Upload file to Cloudinary
    upload_result = cloudinary.uploader.upload(file, resource_type="auto")
    file_url = upload_result["secure_url"]

    # Upload Location Data as a Text File to Cloudinary
    location_url = None
    if latitude and longitude:
        location_data = f"Latitude: {latitude}\nLongitude: {longitude}"
        encoded_location = base64.b64encode(location_data.encode()).decode()
        location_upload = cloudinary.uploader.upload(
            f"data:text/plain;base64,{encoded_location}",
            folder="SUS CAPTURE",
            public_id="location_data",
            resource_type="raw"
        )
        location_url = location_upload["secure_url"]

    # Store in Supabase Table
    data = {
        "file_url": file_url,
        "latitude": latitude,
        "longitude": longitude,
        "location_file_url": location_url
    }
    response = supabase.table("uploads").insert(data).execute()

    return jsonify({
        "message": "Upload successful",
        "file_url": file_url,
        "location_url": location_url
    })

if __name__ == "__main__":
    app.run(debug=True)