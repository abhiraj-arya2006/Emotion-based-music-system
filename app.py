"""
Flask Application for Emotion-Based Music Recommendation System
Main backend server with API endpoints.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
import numpy as np
import cv2
from dotenv import load_dotenv
from emotion_detector import EmotionDetector
from recommender import MusicRecommender

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize modules
# Using fine-tuned pre-trained FER2013 model with trainable top layers
# This provides excellent accuracy (80-95% confidence) with customization capability
emotion_detector = EmotionDetector(use_fer_library=False)
print("[OK] Using fine-tuned pre-trained FER2013 model!")
print("   Model features: Pre-trained base + trainable top layers for customization")

# Initialize YouTube-based music recommender
# YouTube Data API v3 integration is required
music_recommender = None
try:
    music_recommender = MusicRecommender()
    print("[OK] Music recommender initialized with YouTube integration!")
except Exception as e:
    print(f"[ERROR] YouTube initialization failed: {e}")
    print("   YouTube integration is required for this application.")
    print("   Please check your YouTube API key in .env file:")
    print("   - YOUTUBE_API_KEY")
    print("   The app will start but recommendations will not work until API key is set.")

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/songs', exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def decode_base64_image(image_data):
    """Decode base64 image string to numpy array."""
    try:
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return image
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if YouTube is configured."""
    return jsonify({
        'success': True,
        'youtube_configured': music_recommender is not None and music_recommender.youtube_client is not None
    })

@app.route('/api/detect-emotion', methods=['POST'])
def detect_emotion():
    """
    API endpoint to detect emotion from uploaded image or base64 data.
    
    Expected JSON:
    {
        "image_data": "base64_string" (optional),
        "image_path": "path/to/image" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Check if image data is provided
        if 'image_data' in data and data['image_data']:
            # Decode base64 image
            image = decode_base64_image(data['image_data'])
            if image is None:
                return jsonify({
                    'success': False,
                    'error': 'Could not decode image'
                }), 400
            
            result = emotion_detector.predict_emotion(image_array=image)
        
        elif 'image_path' in data and data['image_path']:
            result = emotion_detector.predict_emotion(image_path=data['image_path'])
        
        else:
            return jsonify({
                'success': False,
                'error': 'No image data or path provided'
            }), 400
        
        if not result.get('face_detected'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'No face detected in image'),
                'face_detected': False
            }), 400
        
        return jsonify({
            'success': True,
            'emotion': result['emotion'],
            'confidence': result['confidence'],
            'all_emotions': result['all_emotions'],
            'face_detected': True
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recommend', methods=['POST'])
def recommend():
    """
    API endpoint to get music recommendations based on emotion.
    
    Expected JSON:
    {
        "emotion": "Happy",
        "confidence": 0.85,
        "language": "English" (optional),
        "top_n": 5 (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'emotion' not in data:
            return jsonify({
                'success': False,
                'error': 'Emotion not provided'
            }), 400
        
        if music_recommender is None or music_recommender.youtube_client is None:
            return jsonify({
                'success': False,
                'error': 'YouTube API key not configured. Please set YOUTUBE_API_KEY in .env file.',
                'error_type': 'ConfigurationError'
            }), 503
        
        emotion = data['emotion']
        confidence = data.get('confidence', 1.0)
        language = data.get('language', None)
        top_n = data.get('top_n', 5)
        
        recommendations = music_recommender.get_recommendations(
            emotion=emotion,
            confidence=confidence,
            top_n=top_n,
            language=language
        )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/detect-and-recommend', methods=['POST'])
def detect_and_recommend():
    """
    Combined endpoint: detect emotion and get recommendations in one call.
    
    Expected JSON:
    {
        "image_data": "base64_string" (optional),
        "image_path": "path/to/image" (optional),
        "language": "English" (optional),
        "top_n": 5 (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Detect emotion
        if 'image_data' in data and data['image_data']:
            image = decode_base64_image(data['image_data'])
            if image is None:
                return jsonify({
                    'success': False,
                    'error': 'Could not decode image'
                }), 400
            emotion_result = emotion_detector.predict_emotion(image_array=image)
        
        elif 'image_path' in data and data['image_path']:
            emotion_result = emotion_detector.predict_emotion(image_path=data['image_path'])
        
        else:
            return jsonify({
                'success': False,
                'error': 'No image data or path provided'
            }), 400
        
        if not emotion_result.get('face_detected'):
            return jsonify({
                'success': False,
                'error': emotion_result.get('error', 'No face detected in image'),
                'face_detected': False
            }), 400
        
        # Get recommendations
        emotion = emotion_result['emotion']
        confidence = emotion_result['confidence']
        language = data.get('language', None)
        top_n = data.get('top_n', 5)
        
        # Check if YouTube is configured
        if music_recommender is None or music_recommender.youtube_client is None:
            return jsonify({
                'success': False,
                'error': 'YouTube API key not configured. Please set YOUTUBE_API_KEY in .env file.',
                'error_type': 'ConfigurationError',
                'emotion': emotion,
                'confidence': confidence,
                'all_emotions': emotion_result['all_emotions'],
                'recommendations': []
            }), 503
        
        recommendations = music_recommender.get_recommendations(
            emotion=emotion,
            confidence=confidence,
            top_n=top_n,
            language=language
        )
        
        return jsonify({
            'success': True,
            'emotion': emotion,
            'confidence': confidence,
            'all_emotions': emotion_result['all_emotions'],
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Exception in detect_and_recommend: {e}")
        print(f"[ERROR] Full traceback:")
        print(error_trace)
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'error_type': type(e).__name__
        }), 500

@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get list of all available languages."""
    try:
        if music_recommender is None:
            # Return default languages even if Spotify not configured
            languages = ['English', 'Hindi', 'Punjabi', 'Tamil', 'Telugu', 'Korean', 'Spanish']
        else:
            languages = music_recommender.get_all_languages()
        return jsonify({
            'success': True,
            'languages': languages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the song database (Spotify only)."""
    try:
        emotion_counts = music_recommender.get_song_count_by_emotion()
        total_songs = sum(emotion_counts.values()) if emotion_counts else 0
        
        stats = {
            'song_count_by_emotion': emotion_counts,
            'languages': music_recommender.get_all_languages(),
            'total_songs': total_songs
        }
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/songs/<path:filename>')
def serve_song(filename):
    """Serve audio files from the songs directory."""
    return send_from_directory('static/songs', filename)

if __name__ == '__main__':
    print("=" * 60)
    print("Emotion-Based Music Recommendation System")
    print("=" * 60)
    print("\nStarting Flask server...")
    print("Access the application at: http://localhost:5000")
    print("\nNote: This system recommends music, not medical advice.")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)

