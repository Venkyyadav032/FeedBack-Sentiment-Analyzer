import re
import string
from typing import List

# Common English stop words
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and',
    'any', 'are', 'aren', 'as', 'at', 'be', 'because', 'been', 'before', 'being',
    'below', 'between', 'both', 'but', 'by', 'can', 'could', 'did', 'do', 'does',
    'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had',
    'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him',
    'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself',
    'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of',
    'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out',
    'over', 'own', 's', 'same', 'she', 'should', 'so', 'some', 'such', 'than',
    'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
    'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until',
    'up', 'very', 'was', 'wasn', 'we', 'were', 'what', 'when', 'where', 'which',
    'while', 'who', 'whom', 'why', 'with', 'would', 'you', 'your', 'yours',
    'yourself', 'yourselves', 'the', 'this', 'is', 'was', 'will', 'be', 'it'
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Replace newlines/tabs with space
    text = re.sub(r'[\r\n\t]+', ' ', text)
    # Standardize spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    cleaned = clean_text(text)
    # Remove punctuation
    cleaned_no_punct = cleaned.translate(str.maketrans('', '', string.punctuation))
    words = cleaned_no_punct.split()
    
    # Filter stop words and numbers/short words
    meaningful_words = [w for w in words if w not in STOP_WORDS and len(w) > 2 and not w.isdigit()]
    
    # Also extract bigrams for context
    bigrams = []
    for i in range(len(meaningful_words) - 1):
        bigrams.append(f"{meaningful_words[i]} {meaningful_words[i+1]}")
        
    # Count frequencies
    freq = {}
    for word in meaningful_words + bigrams:
        freq[word] = freq.get(word, 0) + 1
        
    # Sort by frequency and return top N
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_words[:top_n]]
