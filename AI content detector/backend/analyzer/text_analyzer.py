import re
from collections import Counter
import math
import warnings
warnings.filterwarnings('ignore')

# Make NLTK optional
try:
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("Warning: NLTK not installed. Using regex fallback for text analysis.")

# Import ML utilities
try:
    from .ml_models import predict_text_ai
    ML_AVAILABLE = True
except Exception as e:
    print(f"Warning: ML module not available ({e}). Using heuristics only.")
    ML_AVAILABLE = False
    def predict_text_ai(text):
        return None, None

SENSATIONAL_KEYWORDS = set([
    'shocking','breaking','must read','urgent','exclusive','miracle','secret','unbelievable'
])

TRANSITION_WORDS = set([
    'moreover','however','therefore','in conclusion','furthermore','consequently','additionally','overall'
])

def sentence_stats(text):
    # Prefer NLTK sentence tokenizer if available; otherwise fall back to regex splitting.
    try:
        if NLTK_AVAILABLE:
            sentences = nltk.tokenize.sent_tokenize(text)
        else:
            # Fallback: split on sentence-ending punctuation and newlines
            sentences = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
            sentences = [s.strip() for s in sentences if s and s.strip()]
    except Exception:
        # Fallback: split on sentence-ending punctuation and newlines
        sentences = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
        sentences = [s.strip() for s in sentences if s and s.strip()]

    sent_lengths = [len(s.split()) for s in sentences if len(s.split())>0]
    if not sent_lengths:
        return {'avg_len':0,'var_len':0,'num_sent':0}
    avg = sum(sent_lengths)/len(sent_lengths)
    var = sum((x-avg)**2 for x in sent_lengths)/len(sent_lengths)
    return {'avg_len':avg,'var_len':var,'num_sent':len(sent_lengths)}

def spelling_check_simple(text):
    # simple heuristic: count non-word tokens that look like misspellings
    tokens = re.findall(r"[A-Za-z']+", text)
    # treat tokens of single char or weird long sequences as suspect
    suspect = [t for t in tokens if len(t)<=1 or len(t)>25]
    return len(suspect)

def compute_text_score(text):
    text_lower = text.lower()
    stats = sentence_stats(text)
    words = re.findall(r"\w+", text_lower)
    total_words = len(words) or 1
    unique_ratio = len(set(words))/total_words
    transition_count = sum(text_lower.count(w) for w in TRANSITION_WORDS)
    sensational_count = sum(text_lower.count(k) for k in SENSATIONAL_KEYWORDS)
    caps_count = sum(1 for w in re.findall(r"\b[A-Z]{2,}\b", text))  # all-caps words
    punctuation_heavy = text.count('!') + text.count('???')*3

    # scoring heuristic (higher means more likely AI/clickbait)
    score = 0
    # low variance -> AI-like
    if stats['var_len'] < 20:
        score += 2
    if unique_ratio < 0.35:
        score += 1
    if transition_count > max(1, stats['num_sent']//5):
        score += 1
    if sensational_count > 0:
        score += 2
    if caps_count > 2:
        score += 1
    if punctuation_heavy > 2:
        score += 1
    # zero spelling suspects -> suspiciously perfect
    if spelling_check_simple(text) == 0 and total_words>50:
        score += 1

    return {
        'score': score,
        'details': {
            'var_len': stats['var_len'],
            'avg_len': stats['avg_len'],
            'unique_ratio': unique_ratio,
            'transition_count': transition_count,
            'sensational_count': sensational_count,
            'caps_count': caps_count
        }
    }

def analyze_text(text):
    res = compute_text_score(text)
    score = res['score']
    details = res['details']
    
    # Get ML prediction if available
    ml_score = 0
    ml_confidence = 0
    ml_label = 'Unknown'
    
    if ML_AVAILABLE and len(text.strip()) > 20:
        try:
            ml_label, ml_confidence = predict_text_ai(text)
            if ml_label and ml_confidence:
                # Convert to our scoring system (0-6)
                if ml_label == 'Fake':
                    ml_score = 6 if ml_confidence > 0.85 else 4 if ml_confidence > 0.65 else 2
                else:
                    ml_score = 0 if ml_confidence > 0.85 else 1 if ml_confidence > 0.65 else 2
                details['ml_confidence'] = ml_confidence
                details['ml_prediction'] = ml_label
        except Exception as e:
            print(f"ML prediction error: {e}")
            ml_score = 0
    
    # Combine ML and heuristic scores
    if ML_AVAILABLE and ml_confidence > 0:
        final_score = (score + ml_score) / 2
    else:
        final_score = score
    
    if final_score >= 5:
        verdict = 'Highly Likely AI-generated'
        explanation = 'Machine learning analysis + multiple text patterns strongly suggest AI-generated content.'
    elif final_score >= 3.5:
        verdict = 'Likely AI-generated or Highly Template-Based'
        explanation = 'ML model and text analysis indicate probable AI generation or heavy template usage.'
    elif final_score >= 2:
        verdict = 'Possibly AI-generated / Templated'
        explanation = 'Some AI-like patterns detected, but classification is uncertain.'
    else:
        verdict = 'Likely Human-written'
        explanation = 'ML model and text analysis suggest this is naturally human-written content.'
    
    # Detailed human-readable explanations
    avg_len = details['avg_len']
    if avg_len < 10:
        len_explanation = "Very short sentences - feels choppy and unnatural"
    elif avg_len < 15:
        len_explanation = "Short sentences - could be AI-generated for simplicity"
    elif avg_len < 20:
        len_explanation = "Medium-short sentences - somewhat typical"
    elif avg_len < 25:
        len_explanation = "Medium sentences - fairly normal and natural"
    elif avg_len < 35:
        len_explanation = "Medium-long sentences - shows good variety"
    else:
        len_explanation = "Very long sentences - may be complex but natural writing"
    
    var_len = details['var_len']
    if var_len < 10:
        variety_explanation = "⚠️ Very repetitive structure - AI red flag"
    elif var_len < 20:
        variety_explanation = "⚠️ Low variety - sentences follow similar patterns"
    elif var_len < 40:
        variety_explanation = "✓ Moderate variety - reasonably natural"
    else:
        variety_explanation = "✓ High variety - naturally written with diverse structures"
    
    vocab_ratio = details['unique_ratio']
    if vocab_ratio < 0.4:
        vocab_explanation = "Limited word choices - may indicate AI or simple template"
    elif vocab_ratio < 0.6:
        vocab_explanation = "Moderate vocabulary - fairly typical"
    elif vocab_ratio < 0.8:
        vocab_explanation = "Good vocabulary variety - suggests natural writing"
    else:
        vocab_explanation = "Excellent vocabulary - very diverse and natural"
    
    transitions = details['transition_count']
    if transitions == 0:
        trans_explanation = "⚠️ No connecting words - sentences feel disconnected"
    elif transitions < 3:
        trans_explanation = "Few transitions - somewhat abrupt flow"
    else:
        trans_explanation = "✓ Good use of transitions - natural paragraph flow"
    
    sensational = details['sensational_count']
    if sensational > 3:
        sensational_explanation = "Multiple sensational words - clickbait-like"
    elif sensational > 0:
        sensational_explanation = "Some dramatic language - attention-grabbing"
    else:
        sensational_explanation = "✓ No excessive drama - neutral tone"
    
    caps = details['caps_count']
    if caps > 5:
        caps_explanation = "Too many ALL-CAPS words - seems forced or emphatic"
    elif caps > 2:
        caps_explanation = "Some all-caps words - slightly emphatic"
    else:
        caps_explanation = "✓ Natural capitalization - looks normal"
    
    # Add ML analysis if available
    ml_analysis = {}
    if ML_AVAILABLE and ml_confidence > 0:
        ml_analysis['ml_model'] = {
            'value': f'{ml_label} (confidence: {ml_confidence*100:.1f}%)',
            'meaning': f"Advanced ML model classified this as {ml_label} generated"
        }
    
    # Human-readable analysis
    human_readable = {
        'verdict': verdict,
        'explanation': explanation,
        'confidence_score': f"{final_score:.1f}/6",
        'analysis': {
            'average_sentence_length': {
                'value': f"{avg_len:.1f} words",
                'meaning': len_explanation
            },
            'sentence_variety': {
                'value': 'High' if var_len > 20 else 'Low',
                'meaning': variety_explanation
            },
            'vocabulary_diversity': {
                'value': f"{vocab_ratio*100:.1f}%",
                'meaning': vocab_explanation
            },
            'transitions_used': {
                'value': transitions,
                'meaning': trans_explanation
            },
            'sensational_language': {
                'value': 'Yes' if sensational > 0 else 'No',
                'meaning': sensational_explanation
            },
            'excessive_capitals': {
                'value': 'Yes' if caps > 2 else 'No',
                'meaning': caps_explanation
            },
            **ml_analysis
        }
    }
    
    return human_readable
