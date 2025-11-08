import os
from flask import Flask, request, jsonify
import requests
import uuid
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import json

# Load environment variables from .env
load_dotenv()

# ----------------- CONFIG -----------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in environment variable")

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Folder to store temporary uploaded images
UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)

# ---------- helper function: upload image to Cloudinary ----------
def upload_to_cloudinary(file_path):
    result = cloudinary.uploader.upload(file_path)
    return result["secure_url"]

# ---------- helper function: classify image using GPT-4o ----------
def classify_image_with_gpt(image_url):
    api_url = "https://api.openai.com/v1/chat/completions"

    fixed_prompt = (
        "Classify the uploaded image into one of these categories: "
        "Environmental, Infrastructure, Community, Safety, Health. "
        "Return only JSON: {\"category\": \"...\"}."
    )

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": fixed_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        "max_tokens": 200
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        try:
            return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            return {"error": "unexpected response format", "raw": resp.json()}
    else:
        return {"error": f"openai error {resp.status_code}", "detail": resp.text}

# ---------- Flask route: image input ----------
@app.route("/image_input", methods=["POST"])
def image_input():
    if 'image' not in request.files:
        return jsonify({"error": "No file part named 'image'"}), 400

    # Save temporary file
    image_file = request.files['image']
    temp_filename = f"{uuid.uuid4().hex}_{image_file.filename}"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
    image_file.save(temp_path)

    try:
        # Upload image to Cloudinary
        public_url = upload_to_cloudinary(temp_path)
    except Exception as e:
        try:
            os.remove(temp_path)
        except:
            pass
        return jsonify({"error": "image upload failed", "detail": str(e)}), 500

    # Classify image using GPT-4o
    gpt_result = classify_image_with_gpt(public_url)

    # Remove temporary file
    try:
        os.remove(temp_path)
    except:
        pass

    return jsonify({"image_url": public_url, "classification": json.loads(gpt_result)}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)