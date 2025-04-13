print("🚀 Flask server is running with CORS patch")

from flask import Flask, request, send_file
from flask_cors import CORS
from google.cloud import texttospeech
import os, json, logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/speak": {"origins": "*"}}, supports_credentials=True)

# Manually apply CORS headers to all responses
@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# Setup credentials from environment variable
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
    with open("service-account.json", "w") as f:
        f.write(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"

tts_client = texttospeech.TextToSpeechClient()
audio_dir = "audio"
os.makedirs(audio_dir, exist_ok=True)

@app.route("/speak", methods=["POST", "OPTIONS"])
@app.route("/speak/", methods=["POST", "OPTIONS"])
def speak():
    if request.method == "OPTIONS":
        print("✅ OPTIONS preflight received")
        return '', 204

    data = request.get_json()
    text = data.get("text")
    print(f"🔊 POST /speak received with text: {text}")
    if not text:
        return {"error": "Missing 'text'"}, 400

    filename = os.path.join(audio_dir, f"{text}.mp3")
    if os.path.exists(filename):
        return send_file(filename, mimetype="audio/mpeg")

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP", name="ja-JP-Wavenet-B"
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    try:
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        with open(filename, "wb") as out:
            out.write(response.audio_content)
        return send_file(filename, mimetype="audio/mpeg")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": str(e)}, 500

@app.errorhandler(404)
def not_found(e):
    print(f"⚠️  404 Not Found: {request.method} {request.path}")
    return {"error": "Not found"}, 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
