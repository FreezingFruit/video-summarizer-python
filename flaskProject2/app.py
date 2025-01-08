from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from moviepy.editor import VideoFileClip
import whisper
from transformers import pipeline
import torch

app = Flask(__name__)

# Folder to save uploaded videos and extracted audio
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'audio'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Summarization pipeline with specific model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Initialize Whisper model
device = 'cuda' if torch.cuda.is_available() else 'cpu'
whisper_model = whisper.load_model("base", device=device)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        audio_path = extract_audio(filepath)
        if audio_path.startswith("Error:"):
            return jsonify({'error': audio_path})
        transcript = process_audio(audio_path)
        if transcript.startswith("Error:"):
            return jsonify({'error': transcript})
        summary = summarize_text(transcript)
        if summary.startswith("Error:"):
            return jsonify({'error': summary})
        return render_template('result.html', summary=summary)
    return jsonify({'error': 'Failed to upload file'})


def extract_audio(filepath):
    try:
        video = VideoFileClip(filepath)
        audio_filename = os.path.splitext(os.path.basename(filepath))[0] + '.wav'
        audio_path = os.path.join(AUDIO_FOLDER, audio_filename)

        # Extract audio and convert to WAV format with correct settings
        audio = video.audio
        audio.write_audiofile(audio_path, codec='pcm_s16le', ffmpeg_params=['-ar', '16000', '-ac', '1'])

        return audio_path
    except Exception as e:
        return f'Error: {e}'


def process_audio(audio_path):
    try:
        # Check if the audio file exists and is not empty
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            return 'Error: Audio file is empty or does not exist'

        # Transcribe audio using Whisper
        result = whisper_model.transcribe(audio_path)
        transcript = result.get('text', '')
        if not transcript:
            return 'Error: Transcription resulted in empty text'
        return transcript
    except Exception as e:
        return f'Error: {e}'


def summarize_text(text):
    try:
        if not text:
            return 'Error: Text is empty, cannot summarize'

        # Increase the max_length to allow for longer summaries
        summary_list = summarizer(text, max_length=500, min_length=50, do_sample=False)
        summary = summary_list[0]['summary_text']
        return summary
    except Exception as e:
        return f'Error: {e}'


@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True)
