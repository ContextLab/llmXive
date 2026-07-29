"""
Feature Extraction Module (T014, T015).
Extracts linguistic features (modal verbs, imperative ratio, citation density) 
from the ingested dataset and flags undefined ratios.
"""
import os
import re
import csv
import logging
import sys
from pathlib import Path
import pandas as pd

from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define modal verbs for frequency counting
MODAL_VERBS = {
    'can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would',
    'need', 'dare', 'ought', 'used'
}

def extract_features(text: str) -> dict:
    """
    Extract linguistic features from a single text prompt.
    
    Args:
        text: The prompt text to analyze
        
    Returns:
        Dictionary with modal_verb_freq, imperative_ratio, citation_density
    """
    if not isinstance(text, str) or not text.strip():
        return {
            'modal_verb_freq': 0.0,
            'imperative_ratio': 0.0,
            'citation_density': 0.0,
            'sentence_count': 0
        }
    
    text_lower = text.lower()
    
    # 1. Modal Verb Frequency
    # Count occurrences of modal verbs as whole words
    modal_count = 0
    for verb in MODAL_VERBS:
        pattern = r'\b' + re.escape(verb) + r'\b'
        modal_count += len(re.findall(pattern, text_lower))
    
    # Normalize by text length (per 100 words)
    word_count = len(text.split())
    modal_freq = (modal_count / word_count * 100) if word_count > 0 else 0.0
    
    # 2. Sentence Analysis for Imperative Ratio
    # Split into sentences (basic heuristic)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    
    imperative_count = 0
    for sentence in sentences:
        # Heuristic: Imperative sentences often start with a verb (no subject)
        # Simplified: Check if first word is a verb-like token (common in medical directives)
        words = sentence.split()
        if words:
            first_word = words[0].lower()
            # Common imperative starters in medical context
            imperative_markers = {'take', 'use', 'avoid', 'do', 'stop', 'start', 'consider', 'ensure', 'consult', 'check'}
            if first_word in imperative_markers:
                imperative_count += 1
            # Also check for "should/must" + verb structure as directive
            elif first_word in ['should', 'must', 'need', 'have']:
                imperative_count += 1
    
    # Calculate ratio
    # If sentence_count is 0, ratio is undefined (handled in T015)
    if sentence_count > 0:
        imperative_ratio = imperative_count / sentence_count
    else:
        imperative_ratio = 0.0
    
    # 3. Citation Density
    # Count patterns like [1], (Author, Year), or "according to..."
    citation_pattern = r'\[\d+\]|\(\w+,\s*\d{4}\)|according\s+to\s+\w+'
    citation_matches = re.findall(citation_pattern, text, re.IGNORECASE)
    citation_count = len(citation_matches)
    
    citation_density = (citation_count / word_count * 100) if word_count > 0 else 0.0
    
    return {
        'modal_verb_freq': round(modal_freq, 4),
        'imperative_ratio': round(imperative_ratio, 4),
        'citation_density': round(citation_density, 4),
        'sentence_count': sentence_count
    }

def flag_undefined_imperative_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    T015: Flag prompts where imperative ratio is undefined (zero sentences).
    
    Args:
        df: DataFrame with feature columns
        
    Returns:
        DataFrame with added 'is_ratio_undefined' boolean column
    """
    df['is_ratio_undefined'] = df['sentence_count'] == 0
    logger.info(f"Flagged {df['is_ratio_undefined'].sum()} rows with undefined imperative ratio.")
    return df

def run_feature_extraction():
    """
    Run feature extraction on the ingested dataset.
    Reads from data/raw/medmis_subset.csv and writes to data/processed/features_raw.csv.
    """
    config = get_config()
    input_path = Path(config['paths']['raw']) / 'medmis_subset.csv'
    output_path = Path(config['paths']['processed']) / 'features_raw.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion (T013) first.")
    
    logger.info(f"Reading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'prompt_id' not in df.columns:
        raise ValueError("Input dataset missing 'prompt_id' column.")
    
    if 'text' not in df.columns and 'prompt' not in df.columns:
        # Try to find a text column
        text_col = None
        for col in df.columns:
            if 'text' in col.lower() or 'prompt' in col.lower():
                text_col = col
                break
        if not text_col:
            raise ValueError("Input dataset missing text column. Expected 'text' or 'prompt'.")
    else:
        text_col = 'text' if 'text' in df.columns else 'prompt'
    
    logger.info(f"Extracting features for {len(df)} prompts using column '{text_col}'")
    
    features_list = []
    for idx, row in df.iterrows():
        text = row[text_col]
        features = extract_features(text)
        features['prompt_id'] = row['prompt_id']
        features_list.append(features)
        
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} prompts")
    
    df_features = pd.DataFrame(features_list)
    
    # Apply T015 flagging
    df_features = flag_undefined_imperative_ratio(df_features)
    
    # Save intermediate results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(output_path, index=False)
    logger.info(f"Saved intermediate features to {output_path}")
    
    return df_features

def run_feature_extraction_pipeline():
    """Execute the full feature extraction pipeline (T014, T015)."""
    logger.info("Starting Feature Extraction Pipeline")
    df = run_feature_extraction()
    logger.info(f"Feature extraction completed. Total rows: {len(df)}")
    return df

def main():
    """Entry point for feature extraction."""
    try:
        run_feature_extraction_pipeline()
    except Exception as e:
        logger.error(f"Feature extraction pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
