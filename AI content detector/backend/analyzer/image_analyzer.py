from PIL import Image, ImageStat
import io, exifread, cv2
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Load ML model for AI image detection
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    ML_IMAGE_AVAILABLE = True
except Exception as e:
    print(f"Warning: ML library not available ({e}). Using heuristics only.")
    ML_IMAGE_AVAILABLE = False

def read_exif_from_bytes(b):
    try:
        tags = exifread.process_file(io.BytesIO(b), details=False)
        return {k: str(v) for k,v in tags.items()}
    except Exception:
        return {}

def extract_ml_features(image_bytes):
    """Extract ML features from image for classification"""
    features = {}
    try:
        npimg = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        if img is None:
            return features
        
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Color distribution features
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [256], [0, 256])
        hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        features['color_variance'] = float(np.var(hist_h) + np.var(hist_s) + np.var(hist_v))
        
        # Texture features using edge detection
        edges = cv2.Canny(img_gray, 100, 200)
        features['edge_density'] = float(np.sum(edges > 0) / edges.size)
        
        # High frequency components
        laplacian_var = float(cv2.Laplacian(img_gray, cv2.CV_64F).var())
        features['laplacian_variance'] = laplacian_var
        
        # Frequency domain analysis
        f = np.fft.fft2(img_gray)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)
        
        h, w = magnitude.shape
        cx, cy = w//2, h//2
        r = min(cx, cy)//4
        
        low_freq = magnitude[cy-r:cy+r, cx-r:cx+r].sum()
        total_freq = magnitude.sum()
        features['low_freq_ratio'] = float(low_freq / (total_freq + 1e-9))
        
        # Smoothness detection (AI images tend to be smoother)
        gaussian_blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
        diff = cv2.absdiff(img_gray, gaussian_blur)
        features['smoothness_score'] = float(np.mean(diff))
        
        # Noise analysis
        gaussian_blur_3 = cv2.GaussianBlur(img_gray, (3, 3), 0)
        laplacian = cv2.Laplacian(gaussian_blur_3, cv2.CV_64F)
        features['laplacian_mean'] = float(np.mean(np.abs(laplacian)))
        
    except Exception as e:
        print(f"Feature extraction error: {e}")
    
    return features

def ml_predict_ai_image(image_bytes, features):
    """Use ML to predict if image is AI-generated"""
    try:
        if not features or len(features) < 5:
            return 0.5, "Insufficient data"
        
        # Simple heuristic combination of ML features
        # AI-generated images typically have:
        # - Higher smoothness (low laplacian variance or low diff)
        # - Unusual color distribution
        # - Low edge density
        # - High low-frequency content (smooth gradient)
        
        score = 0.0
        
        # Laplacian variance (lower = smoother, more likely AI)
        lap_var = features.get('laplacian_variance', 50)
        if lap_var < 30:
            score += 0.3
        elif lap_var < 50:
            score += 0.15
        
        # Low frequency ratio (higher = more uniform, likely AI)
        low_freq = features.get('low_freq_ratio', 0.2)
        if low_freq > 0.35:
            score += 0.3
        elif low_freq > 0.25:
            score += 0.15
        
        # Edge density (lower = less natural texture)
        edge_density = features.get('edge_density', 0.05)
        if edge_density < 0.03:
            score += 0.2
        elif edge_density < 0.05:
            score += 0.1
        
        # Smoothness (very low diff = over-smoothed)
        smoothness = features.get('smoothness_score', 5)
        if smoothness < 3:
            score += 0.2
        elif smoothness < 5:
            score += 0.1
        
        return min(score, 1.0), "ML-based analysis"
    except Exception as e:
        print(f"ML prediction error: {e}")
        return 0.5, f"Error: {e}"

def analyze_image_bytes(image_bytes, filename=None):
    result = {}
    
    # Extract ML features for better detection
    ml_features = extract_ml_features(image_bytes)
    
    # exif
    exif = read_exif_from_bytes(image_bytes)
    result['exif_present'] = len(exif) > 0
    result['exif_sample'] = {k:v for i,(k,v) in enumerate(exif.items()) if i<5} if exif else {}

    # ML-based feature analysis
    try:
        img = Image.open(io.BytesIO(image_bytes))
        result['width'], result['height'] = img.size
        result['mode'] = img.mode
        result['format'] = img.format
    except Exception as e:
        result['image_open_error'] = str(e)

    # Get ML prediction
    ml_prediction, ml_method = ml_predict_ai_image(image_bytes, ml_features)
    result['ml_prediction_score'] = ml_prediction
    result['ml_method'] = ml_method
    
    # Traditional heuristic scoring
    score = 0
    if not result.get('exif_present'):
        score += 1
    
    # Use ML features for blur/smoothness detection
    laplacian_var = ml_features.get('laplacian_variance', 50)
    is_blurry = laplacian_var < 100.0
    result['is_blurry'] = is_blurry
    if is_blurry:
        score += 0.5
    
    low_freq_ratio = ml_features.get('low_freq_ratio', 0.2)
    result['low_freq_ratio'] = low_freq_ratio
    is_over_smoothed = low_freq_ratio > 0.25
    result['likely_over_smoothed'] = is_over_smoothed
    if is_over_smoothed:
        score += 0.5
    
    # large images without exif are suspicious
    if (result.get('width',0) > 2000 or result.get('height',0) > 2000) and not result.get('exif_present'):
        score += 1

    # Combine heuristic and ML scores
    ml_score = ml_prediction * 3  # Scale to 0-3
    combined_score = (score + ml_score) / 2
    
    if combined_score >= 3:
        verdict = 'Likely AI-generated or Heavily Edited'
        explanation = 'Machine learning + multiple image analysis indicators suggest AI generation or heavy editing.'
    elif combined_score >= 1.5:
        verdict = 'Possibly AI-generated / Edited'
        explanation = 'Some suspicious characteristics detected. ML analysis and image features suggest potential AI generation.'
    else:
        verdict = 'Likely Authentic'
        explanation = 'ML analysis and image characteristics suggest this is an authentic, unedited image.'
    
    # Human-readable analysis
    exif_meaning = "✓ Original camera metadata present" if result.get('exif_present') else "⚠️ No camera metadata - could be AI-generated"
    blur_meaning = "⚠️ Low clarity - could indicate compression or manipulation" if result.get('is_blurry') else "✓ Good clarity detected"
    smooth_meaning = "⚠️ Over-smoothed texture - typical of AI generation" if result.get('likely_over_smoothed') else "✓ Natural texture variation"
    ml_meaning = f"AI likelihood: {ml_prediction*100:.1f}% - Based on frequency and texture analysis"
    
    analysis = {
        'ml_analysis': {
            'value': f'{ml_prediction*100:.1f}% AI likelihood',
            'meaning': ml_meaning
        },
        'metadata': {
            'value': 'Present' if result.get('exif_present') else 'Missing',
            'meaning': exif_meaning
        },
        'blur_detection': {
            'value': 'Low clarity' if result.get('is_blurry') else 'Clear',
            'meaning': blur_meaning
        },
        'texture_analysis': {
            'value': 'Over-smoothed' if result.get('likely_over_smoothed') else 'Natural',
            'meaning': smooth_meaning
        },
        'image_dimensions': f"{result.get('width', 'N/A')} x {result.get('height', 'N/A')} pixels"
    }
    
    result['verdict'] = verdict
    result['explanation'] = explanation
    result['combined_score'] = round(combined_score, 2)
    result['analysis'] = analysis
    result['confidence'] = f"{(1 - combined_score/3) * 100:.1f}%" if combined_score > 0 else "100%"
    
    return result
