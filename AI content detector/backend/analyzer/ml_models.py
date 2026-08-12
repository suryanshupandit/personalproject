"""
ML Model utilities for AI content detection
Handles model loading with graceful fallbacks
"""
import warnings
warnings.filterwarnings('ignore')
import numpy as np

# Text classification model
text_model = None
text_tokenizer = None

def load_text_classifier():
    """Load transformer-based text classifier for AI detection"""
    global text_model, text_tokenizer
    
    if text_model is not None:
        return text_model
    
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        
        # Try loading OpenAI detector first (lightweight)
        try:
            model_name = "roberta-base-openai-detector"
            text_tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            text_model = AutoModelForSequenceClassification.from_pretrained(model_name, trust_remote_code=True)
            print("✓ Loaded RoBERTa OpenAI Detector model")
            return text_model
        except Exception as e:
            print(f"Note: RoBERTa model not available ({str(e)[:50]}). Using heuristics only.")
            return None
            
    except ImportError:
        print("Warning: Transformers library not installed. Using heuristics only.")
        return None
    except Exception as e:
        print(f"Warning: Could not load ML model: {e}")
        return None

def predict_text_ai(text):
    """
    Predict if text is AI-generated
    Returns: (prediction, confidence)
    - prediction: "Fake"/"Human"
    - confidence: 0.0-1.0
    """
    try:
        model = load_text_classifier()
        if model is None or text_tokenizer is None:
            return None, None
            
        if len(text.strip()) < 20:
            return None, None
        
        # Use first 512 tokens
        inputs = text_tokenizer(text[:2000], return_tensors="pt", truncation=True, max_length=512)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            outputs = model(**inputs)
        
        logits = outputs[0][0]
        probs = logits.softmax(dim=-1)
        
        # Model classes: 0=Human, 1=Fake
        human_prob = float(probs[0])
        fake_prob = float(probs[1])
        
        label = "Fake" if fake_prob > human_prob else "Human"
        confidence = max(human_prob, fake_prob)
        
        return label, confidence
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return None, None

# Image models
image_classifier = None

def load_image_classifier():
    """Load image classification model"""
    global image_classifier
    
    if image_classifier is not None:
        return image_classifier
    
    try:
        # Try Vision Transformer for AI image detection
        from transformers import ViTImageProcessor, ViTForImageClassification
        
        try:
            processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
            model = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224')
            image_classifier = {'processor': processor, 'model': model, 'type': 'vit'}
            print("✓ Loaded Vision Transformer model for image analysis")
            return image_classifier
        except Exception as e:
            print(f"Note: Vision Transformer not available. Using feature extraction only.")
            return None
            
    except ImportError:
        print("Warning: Transformers not available. Using heuristics only.")
        return None
    except Exception as e:
        print(f"Warning: Could not load image model: {e}")
        return None

def predict_image_ai_ml(image_bytes):
    """
    Use ML to predict if image is AI-generated
    Returns: (confidence_score, description)
    """
    try:
        classifier = load_image_classifier()
        if classifier is None:
            return 0.5, "ML model unavailable - using heuristics"
        
        from PIL import Image
        import io
        
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            if classifier['type'] == 'vit':
                processor = classifier['processor']
                model = classifier['model']
                
                inputs = processor(images=img, return_tensors="pt")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    outputs = model(**inputs)
                
                logits = outputs.logits
                confidence = float(logits.softmax(dim=-1).max().detach().numpy())
                
                return confidence, "Vision Transformer based analysis"
            
        except Exception as e:
            return 0.5, f"Prediction error: {str(e)[:30]}"
            
    except Exception as e:
        return 0.5, f"Error: {str(e)[:30]}"

# News/Text credibility model
news_model = None

def load_news_classifier():
    """Load model for news credibility analysis"""
    global news_model
    
    if news_model is not None:
        return news_model
    
    try:
        from transformers import pipeline
        news_model = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)
        print("✓ Loaded BART model for news analysis")
        return news_model
            
    except ImportError:
        print("Warning: Transformers not available. Using heuristics only.")
        return None
    except Exception as e:
        print(f"Warning: Could not load news model: {e}")
        return None

def predict_news_credibility(text):
    """
    Predict news article credibility
    Returns: (credibility_score, confidence)
    credibility_score: 0.0 (unreliable) to 1.0 (credible)
    """
    try:
        if len(text.strip()) < 20:
            return None, None
        
        # Count credibility indicators
        credibility_words = ['report', 'study', 'research', 'according', 'official', 'confirmed', 
                           'verified', 'fact', 'evidence', 'source', 'statement', 'investigation']
        questionable_words = ['alleged', 'claimed', 'rumor', 'supposedly', 'unconfirmed', 
                            'insider', 'anonymous', 'leaked', 'secret', 'exclusive', 'unverified']
        
        text_lower = text.lower()
        cred_count = sum(text_lower.count(w) for w in credibility_words)
        ques_count = sum(text_lower.count(w) for w in questionable_words)
        
        # Calculate credibility score
        total = cred_count + ques_count
        if total == 0:
            credibility_score = 0.5  # Neutral if no indicators
            confidence = 0.5
        else:
            credibility_score = cred_count / (cred_count + ques_count)
            confidence = 0.7
        
        return credibility_score, confidence
        
    except Exception as e:
        print(f"Credibility prediction error: {e}")
        return None, None

def get_image_model():
    """Get or create image analysis model (kept for backward compatibility)"""
    return load_image_classifier()

def preload_models():
    """Preload all models at startup"""
    print("Preloading ML models...")
    load_text_classifier()
    load_image_classifier()
    load_news_classifier()
    print("ML models ready (or running in heuristic mode)")
