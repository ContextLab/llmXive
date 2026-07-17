"""
Feature extraction module: Extract linguistic features from prompts.
"""
import os
import re
import csv
import logging
import nltk
from typing import List, Dict, Any, Tuple
import pandas as pd

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

from config import config

logger = logging.getLogger(__name__)

MODAL_VERBS = {'can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would'}

def extract_features(text: str) -> Dict[str, float]:
    """
    Extract linguistic features from a text string.
    Returns: dict with modal_verb_freq, imperative_ratio, citation_density
    """
    if not text or not isinstance(text, str):
        return {
            "modal_verb_freq": 0.0,
            "imperative_ratio": 0.0,
            "citation_density": 0.0,
            "total_sentences": 0,
            "imperative_count": 0
        }

    # Tokenize and tag
    sentences = nltk.sent_tokenize(text)
    total_sentences = len(sentences)
    
    if total_sentences == 0:
        return {
            "modal_verb_freq": 0.0,
            "imperative_ratio": 0.0,
            "citation_density": 0.0,
            "total_sentences": 0,
            "imperative_count": 0
        }

    modal_count = 0
    imperative_count = 0
    citation_count = 0

    for sentence in sentences:
        tokens = nltk.word_tokenize(sentence)
        pos_tags = nltk.pos_tag(tokens)
        
        # Modal verbs
        for word, tag in pos_tags:
            if word.lower() in MODAL_VERBS:
                modal_count += 1
        
        # Imperative detection (VB tag at start of sentence, no subject)
        if pos_tags and pos_tags[0][1] == 'VB':
            # Simple heuristic: starts with verb and no pronoun subject before
            imperative_count += 1
        
        # Citation density: count patterns like [1], (1), etc.
        citations = re.findall(r'\[\d+\]|\(\d+\)', sentence)
        citation_count += len(citations)

    modal_verb_freq = modal_count / total_sentences
    imperative_ratio = imperative_count / total_sentences if total_sentences > 0 else 0.0
    citation_density = citation_count / total_sentences

    return {
        "modal_verb_freq": modal_verb_freq,
        "imperative_ratio": imperative_ratio,
        "citation_density": citation_density,
        "total_sentences": total_sentences,
        "imperative_count": imperative_count
    }

def run_feature_extraction(input_path: str, output_path: str):
    """
    Run feature extraction on a CSV file.
    Expects 'text' column. Outputs features to new CSV.
    """
    logger.info(f"Starting feature extraction on {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    
    if 'text' not in df.columns:
        raise ValueError("Input CSV must contain a 'text' column.")

    features = []
    for idx, row in df.iterrows():
        feats = extract_features(str(row['text']))
        feats['prompt_id'] = row.get('prompt_id', idx)
        features.append(feats)

    features_df = pd.DataFrame(features)
    features_df.to_csv(output_path, index=False)
    logger.info(f"Feature extraction complete. Saved to {output_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example usage
    input_file = os.path.join(config.paths["data_raw"], "medmis_subset.csv")
    output_file = os.path.join(config.paths["data_processed"], "features.csv")
    if os.path.exists(input_file):
        run_feature_extraction(input_file, output_file)
    else:
        logger.warning(f"Input file {input_file} not found. Skipping extraction.")
