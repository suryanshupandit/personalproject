from flask import Flask, render_template, request, send_from_directory, abort, jsonify
import sys
import warnings
warnings.filterwarnings('ignore')

# Make NLTK optional
try:
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

# Ensure NLTK sentence tokenizer data is available
def ensure_nltk():
    if not NLTK_AVAILABLE:
        print("Note: NLTK not installed. Using regex fallback for text analysis.")
        return
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print('NLTK resource "punkt" not found. Downloading...')
        try:
            nltk.download('punkt', quiet=True)
        except:
            pass
    # some nltk versions look for punkt_tab; attempt to ensure that too
    try:
        nltk.data.find('tokenizers/punkt_tab/english')
    except LookupError:
        try:
            print('NLTK resource "punkt_tab" not found. Attempting download...')
            nltk.download('punkt_tab', quiet=True)
        except Exception:
            # not all NLTK distributions provide punkt_tab; ignore if download fails
            pass

# Preload ML models for faster predictions
def init_ml_models():
    """Initialize machine learning models at startup"""
    try:
        from analyzer.ml_models import preload_models
        print("\n🤖 Initializing ML models for better predictions...")
        preload_models()
        print("✓ ML models initialized - using advanced AI detection\n")
    except Exception as e:
        print(f"\n⚠ ML models not available: {e}")
        print("  Running in heuristic-only mode (less accurate)\n")

import os

# Import detection modules
from analyzer.text_analyzer import analyze_text
from analyzer.image_analyzer import analyze_image_bytes
from analyzer.news_analyzer import analyze_news_url

app = Flask(__name__)

# Initialize lightweight resources on startup.
# ML models load lazily during analysis requests to avoid blocking app startup.
ensure_nltk()

# Frontend directory (project root /frontend)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

# Upload folder configuration
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route("/")
def index():
    # Serve the static frontend index.html
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIR, 'index.html')
    # Fallback: try Flask templates (if present)
    try:
        return render_template('index.html')
    except Exception:
        abort(404)


@app.route('/<path:filename>')
def frontend_files(filename):
    # Do not capture API routes with this generic file route
    if filename.startswith('api/') or filename.startswith('api'):
        abort(404)
    # Serve other frontend static files (main.js, styles, etc.)
    filepath = os.path.join(FRONTEND_DIR, filename)
    if os.path.exists(filepath):
        return send_from_directory(FRONTEND_DIR, filename)
    abort(404)


# --- API endpoints used by frontend/main.js ---
@app.route('/api/analyze/text', methods=['POST'])
def api_analyze_text():
    try:
        data = request.get_json(force=True)
        text = data.get('text','')
    except Exception:
        # fallback to form data
        text = request.form.get('text','')
    if not text:
        return jsonify({'error':'No text provided'}), 400
    res = analyze_text(text)
    return jsonify(res)


@app.route('/api/analyze/image', methods=['POST'])
def api_analyze_image():
    if 'file' not in request.files:
        return jsonify({'error':'No file part'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error':'No selected file'}), 400
    b = f.read()
    res = analyze_image_bytes(b, f.filename)
    return jsonify(res)


@app.route('/api/analyze/news', methods=['POST'])
def api_analyze_news():
    try:
        data = request.get_json(force=True)
        url = data.get('url','')
    except Exception:
        url = request.form.get('url','')
    if not url:
        return jsonify({'error':'No url provided'}), 400
    try:
        res = analyze_news_url(url)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify(res)





@app.route("/detect", methods=["POST"])
def detect():
    result = {}
    detection_type = request.form.get("type")

    # -------- TEXT DETECTION --------
    if detection_type == "text":
        text = request.form.get("input_text")
        res = analyze_text(text)
        result = {
            "type": "Text",
            "verdict": res.get('verdict'),
            "explanation": res.get('explanation'),
            "analysis": res.get('analysis')
        }

    # -------- IMAGE DETECTION --------
    elif detection_type == "image":
        image = request.files.get("image_file")

        if image:
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
            image.save(image_path)

            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            res = analyze_image_bytes(image_bytes, image.filename)
            result = {
                "type": "Image",
                "verdict": res.get('verdict'),
                "explanation": res.get('explanation'),
                "analysis": res.get('analysis')
            }

    # -------- NEWS DETECTION --------
    elif detection_type == "news":
        news_text = request.form.get("news_text")
        res = analyze_news_url(news_text) if news_text.startswith('http') else analyze_text(news_text)
        result = {
            "type": "News",
            "verdict": res.get('verdict'),
            "explanation": res.get('explanation', res.get('analysis', {})),
            "analysis": res.get('analysis', res.get('details', {}))
        }

    # Return JSON result instead of rendering a missing template
    return jsonify(result)


@app.route("/about")
def about():
    # Serve an about page if frontend/about.html exists, otherwise simple text
    about_path = os.path.join(FRONTEND_DIR, 'about.html')
    if os.path.exists(about_path):
        return send_from_directory(FRONTEND_DIR, 'about.html')
    return '<h1>About</h1><p>AI Content Detector backend</p>'


if __name__ == "__main__":
    app.run(debug=True)
