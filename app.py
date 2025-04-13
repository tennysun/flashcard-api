from flask import Flask, request, send_file
from google.cloud import texttospeech
import os, json

app = Flask(__name__)

# Setup credentials from environment variable
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
    with open("service-account.json", "w") as f:
        f.write(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"

tts_client = texttospeech.TextToSpeechClient()
audio_dir = "audio"
os.makedirs(audio_dir, exist_ok=True)

@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json()
    text = data.get("text")
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
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
