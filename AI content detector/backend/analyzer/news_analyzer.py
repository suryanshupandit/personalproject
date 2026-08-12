import requests, validators
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import warnings
warnings.filterwarnings('ignore')

# Import ML utilities
try:
    from .ml_models import predict_news_credibility
    ML_AVAILABLE = True
except Exception as e:
    print(f"Warning: ML module not available ({e}). Using heuristics only.")
    ML_AVAILABLE = False
    def predict_news_credibility(text):
        return None, None

# small whitelist of known domains - expand for production
REPUTABLE_DOMAINS = set([
    'thehindu.com','timesofindia.indiatimes.com','bbc.com','reuters.com','theguardian.com','nytimes.com',
    'apnews.com', 'cbsnews.com', 'foxnews.com', 'msnbc.com', 'cnn.com', 'abcnews.com'
])

SENSATIONAL_WORDS = ['shocking','exclusive','must read','you won\'t believe','urgent','miracle','shocker',
                     'unbelievable','sensational','breaking','bombshell','leaked','insider']

def fetch_article(url):
    r = requests.get(url, timeout=12, headers={'User-Agent':'Mozilla/5.0'})
    r.raise_for_status()
    return r.text

def analyze_news_url(url):
    url = (url or '').strip()
    if url and not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    if not validators.url(url):
        raise ValueError('Invalid URL')

    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.','')
    result = {'domain': domain}
    try:
        article_html = fetch_article(url)
    except requests.RequestException as e:
        raise ValueError(f'Could not fetch article: {e}')

    soup = BeautifulSoup(article_html, 'html.parser')
    # try to extract title, author, date
    title = soup.title.string.strip() if soup.title else ''
    result['title'] = title
    # naive lookups
    author = ''
    for sel in ['meta[name=author]','meta[property="article:author"]','span.author','a[rel=author]']:
        t = soup.select_one(sel)
        if t:
            author = t.get('content') if t.has_attr('content') else t.text.strip()
            break
    result['author'] = author or 'Not found'

    # date find
    date = ''
    date_sel = soup.select_one('meta[property="article:published_time"], meta[name="pubdate"], time')
    if date_sel:
        date = date_sel.get('content') if date_sel.has_attr('content') else date_sel.text.strip()
    result['published_date'] = date or 'Not found'

    # check domain reputation
    result['is_reputable'] = domain in REPUTABLE_DOMAINS

    text = ' '.join(p.get_text(separator=' ') for p in soup.find_all('p'))
    lower = text.lower()
    sensational_count = sum(lower.count(w) for w in SENSATIONAL_WORDS)
    caps_ratio = sum(1 for w in title.split() if w.isupper()) / max(1, len(title.split()))
    result['sensational_count'] = sensational_count
    result['title_caps_ratio'] = caps_ratio

    # verdict heuristics - count red flags
    red_flags = 0
    ml_credibility = 0.5
    ml_confidence = 0
    
    # Missing author is a red flag
    if result['author'] == 'Not found':
        red_flags += 1
    # Missing date is a red flag
    if result['published_date'] == 'Not found':
        red_flags += 1
    # Non-reputable domain is a red flag
    if not result['is_reputable']:
        red_flags += 1
    # Sensational language is a red flag
    if sensational_count > 0:
        red_flags += 1
    # High caps ratio (clickbait) is a red flag
    if caps_ratio > 0.3:
        red_flags += 1
    
    # Get ML credibility prediction if available
    if ML_AVAILABLE and text:
        try:
            ml_credibility, ml_confidence = predict_news_credibility(text)
            if ml_credibility is not None:
                # Convert ML credibility to red flag adjustment
                if ml_credibility < 0.4:
                    red_flags += 2
                elif ml_credibility < 0.6:
                    red_flags += 1
        except Exception as e:
            print(f"ML analysis error: {e}")
    
    # Combine heuristic and ML analysis for final verdict
    final_score = (red_flags + (1 - ml_credibility) * 5) / 2

    # Updated verdict logic based on red flags and ML analysis
    if final_score >= 4:
        verdict = 'Likely Misinformation / Unreliable'
        explanation = 'Multiple red flags and ML analysis strongly suggest this is misinformation or from an unreliable source.'
    elif final_score >= 3:
        verdict = 'Possibly Unreliable'
        explanation = 'ML analysis and heuristics indicate several suspicious characteristics that warrant verification.'
    elif final_score >= 1.5:
        verdict = 'Uncertain - Some red flags present'
        explanation = 'This article has some concerning elements but may still be legitimate.'
    else:
        verdict = 'Likely Reliable'
        explanation = 'ML analysis and source verification indicate this is from a credible source with proper attribution.'
    
    # Human-readable analysis
    author_meaning = f"✓ Author: {result['author']}" if result['author'] != 'Not found' else "⚠️ No author information - can't verify credibility"
    date_meaning = f"✓ Published: {result['published_date']}" if result['published_date'] != 'Not found' else "⚠️ No publication date - suspicious"
    domain_meaning = f"✓ From known reputable source ({domain})" if result['is_reputable'] else f"⚠️ Unknown/potentially unreliable domain ({domain})"
    sensational_meaning = f"⚠️ Uses {sensational_count} sensational words - clickbait style" if sensational_count > 0 else "✓ Neutral language - professional tone"
    caps_meaning = f"⚠️ Excessive caps in title ({caps_ratio*100:.0f}%) - clickbait indicator" if caps_ratio > 0.3 else f"✓ Normal title capitalization ({caps_ratio*100:.0f}%)"
    
    analysis = {
        'author': {
            'value': result['author'],
            'meaning': author_meaning
        },
        'publication_date': {
            'value': result['published_date'],
            'meaning': date_meaning
        },
        'source_domain': {
            'value': domain,
            'meaning': domain_meaning
        },
        'sensational_language': {
            'value': f"{sensational_count} instances",
            'meaning': sensational_meaning
        },
        'title_caps_ratio': {
            'value': f"{caps_ratio*100:.0f}%",
            'meaning': caps_meaning
        }
    }
    
    # Add ML credibility analysis if available
    if ML_AVAILABLE and ml_confidence > 0:
        ml_meaning = f"Text credibility analysis: {ml_credibility*100:.1f}% confidence in article authenticity"
        analysis['ml_credibility'] = {
            'value': f"{ml_credibility*100:.1f}%",
            'meaning': ml_meaning
        }
    
    result['verdict'] = verdict
    result['explanation'] = explanation
    result['red_flags'] = red_flags
    result['score'] = final_score
    result['analysis'] = analysis
    return result
