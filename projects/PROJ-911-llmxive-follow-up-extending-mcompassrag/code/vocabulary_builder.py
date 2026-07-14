import json
import re
from collections import Counter
from typing import List, Dict, Any, Set

from sklearn.feature_extraction.text import TfidfVectorizer
from code.config import (
    MIN_DF, MAX_DF, N_TOP_TERMS, PROCESSED_DIR, RANDOM_SEED, MAX_DOCS
)
from code.data_loader import load_hotpotqa_sample, load_wikipedia_sample

def clean_text(text: str) -> str:
    """Basic text cleaning: lowercasing and removing non-alphanumeric chars."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_fixed_vocabulary() -> Dict[str, int]:
    """
    Implements TF-IDF filtering with a fixed reference vocabulary.
    Loads real data from HotpotQA and Wikipedia, computes TF-IDF on the union,
    and saves the top N terms to data/processed/fixed_vocab.json.
    
    This ensures the vocabulary is derived from real data (FR-001) and versioned.
    """
    print("Loading real datasets...")
    hotpot_docs = load_hotpotqa_sample()
    wiki_docs = load_wikipedia_sample()
    
    all_docs = hotpot_docs + wiki_docs
    print(f"Total documents loaded: {len(all_docs)} (Max allowed: {MAX_DOCS * 2})")
    
    # Extract text and clean
    clean_texts = [clean_text(doc['text']) for doc in all_docs]
    clean_titles = [clean_text(doc['title']) for doc in all_docs]
    
    # Combine title and text for better representation
    combined_texts = [f"{t} {txt}" for t, txt in zip(clean_titles, clean_texts)]
    
    print("Computing TF-IDF to select fixed vocabulary...")
    
    # Initialize TfidfVectorizer
    # Using MIN_DF and MAX_DF from config to filter noise
    vectorizer = TfidfVectorizer(
        min_df=MIN_DF,
        max_df=MAX_DF,
        max_features=N_TOP_TERMS,
        stop_words='english',
        token_pattern=r"(?u)\b\w+\b"
    )
    
    # Fit on the corpus
    try:
        tfidf_matrix = vectorizer.fit_transform(combined_texts)
    except ValueError as e:
        # Fallback if no documents meet min_df or all are filtered
        print(f"TF-IDF fit failed: {e}. Attempting with relaxed constraints...")
        vectorizer = TfidfVectorizer(
            min_df=1,
            max_df=1.0,
            max_features=N_TOP_TERMS,
            stop_words='english',
            token_pattern=r"(?u)\b\w+\b"
        )
        tfidf_matrix = vectorizer.fit_transform(combined_texts)

    feature_names = vectorizer.get_feature_names_out()
    
    # Convert to a dictionary {term: index}
    # The vectorizer already sorted features by the 'max_features' argument (top TF-IDF scores)
    # or alphabetically if max_features is not used. Here max_features is used.
    vocab_dict = {term: idx for idx, term in enumerate(feature_names)}
    
    print(f"Fixed vocabulary size: {len(vocab_dict)}")
    
    # Save to file
    output_path = PROCESSED_DIR / "fixed_vocab.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(vocab_dict, f, indent=2)
    
    print(f"Vocabulary saved to {output_path}")
    return vocab_dict

if __name__ == "__main__":
    build_fixed_vocabulary()
