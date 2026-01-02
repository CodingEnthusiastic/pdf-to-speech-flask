from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
import pdfplumber
import pyttsx3
import io
import threading
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Store current session data (captions and audio)
current_session = {
    'captions': [],
    'audio_data': None,
    'processing': False
}

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None

def text_to_speech_with_captions(text):
    """Convert text to speech and generate captions"""
    try:
        engine = pyttsx3.init()
        
        # Store audio in memory
        audio_buffer = io.BytesIO()
        engine.save_to_file(text, 'temp_audio.mp3')
        engine.runAndWait()
        
        # Read the temporary audio file into buffer
        with open('temp_audio.mp3', 'rb') as f:
            audio_buffer = io.BytesIO(f.read())
        
        # Generate captions by splitting text into sentences
        sentences = text.split('.')
        captions = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                captions.append({
                    'id': i,
                    'text': sentence + '.',
                    'timestamp': i * 2  # Approximate 2 seconds per sentence
                })
        
        current_session['captions'] = captions
        current_session['audio_data'] = audio_buffer.getvalue()
        
        return True
    except Exception as e:
        print(f"Error converting to speech: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF upload and conversion"""
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400
    
    pdf_file = request.files['pdf_file']
    
    if pdf_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_file)
        
        if not text:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        # Convert to speech and generate captions
        current_session['processing'] = True
        success = text_to_speech_with_captions(text)
        current_session['processing'] = False
        
        if success:
            return jsonify({
                'success': True,
                'message': 'PDF processed successfully',
                'captions': current_session['captions']
            })
        else:
            return jsonify({'error': 'Failed to convert text to speech'}), 500
            
    except Exception as e:
        current_session['processing'] = False
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-audio')
def get_audio():
    """Stream audio file"""
    if current_session['audio_data'] is None:
        return jsonify({'error': 'No audio available'}), 404
    
    audio_buffer = io.BytesIO(current_session['audio_data'])
    return send_file(
        audio_buffer,
        mimetype='audio/mpeg',
        as_attachment=False,
        download_name='output.mp3'
    )

@app.route('/api/get-captions')
def get_captions():
    """Get captions for current session"""
    return jsonify({'captions': current_session['captions']})

@app.route('/api/end-session', methods=['POST'])
def end_session():
    """Clear session data (delete audio and captions)"""
    current_session['captions'] = []
    current_session['audio_data'] = None
    current_session['processing'] = False
    
    # Clean up temporary files
    import os
    if os.path.exists('temp_audio.mp3'):
        os.remove('temp_audio.mp3')
    
    return jsonify({'success': True, 'message': 'Session ended, all data cleared'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
