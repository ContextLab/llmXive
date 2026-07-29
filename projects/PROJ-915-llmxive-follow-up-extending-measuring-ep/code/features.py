"""
code/features.py
Implements linguistic feature extraction and undefined ratio handling.
"""
import os
import re
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config import get_config
from error_handling import DatasetDownloadError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/features_extraction.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Modal verbs list
MODAL_VERBS = [
    'can', 'could', 'may', 'might', 'must', 'shall', 'should', 'will', 'would',
    'can\'t', 'couldn\'t', 'mayn\'t', 'mightn\'t', 'mustn\'t', 'shan\'t', 'shouldn\'t', 'won\'t', 'wouldn\'t'
]

def extract_features(text: str) -> Dict[str, Any]:
    """
    Extract linguistic features from a single text prompt.
    
    Args:
        text: The prompt text to analyze.
        
    Returns:
        Dictionary containing extracted features.
    """
    if not text or not isinstance(text, str):
        text = ""
    
    # Normalize text for analysis
    text_lower = text.lower()
    
    # 1. Modal verb frequency
    modal_count = 0
    for verb in MODAL_VERBS:
        # Use word boundary matching to avoid partial matches
        pattern = r'\b' + re.escape(verb) + r'\b'
        matches = re.findall(pattern, text_lower)
        modal_count += len(matches)
    
    modal_freq = modal_count / max(len(text.split()), 1)  # Normalize by word count
    
    # 2. Sentence segmentation
    # Simple sentence splitter: split on ., !, ?
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total_sentences = len(sentences)
    
    # 3. Imperative vs Declarative detection
    # Imperative sentences often start with base verbs (be, do, have, etc.) or lack a subject
    # This is a heuristic approximation
    imperative_count = 0
    declarative_count = 0
    
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        
        first_word = words[0].lower()
        
        # Heuristic: Imperative often starts with a verb (base form) and has no explicit subject
        # Common base verbs that might start imperatives
        imperative_starters = ['be', 'do', 'have', 'get', 'make', 'take', 'give', 'let', 'look', 'make', 'put', 'set', 'turn', 'come', 'go', 'stop', 'start', 'try', 'use', 'watch', 'work']
        
        if first_word in imperative_starters:
            # Check if it looks like an imperative (no subject pronoun before)
            # Simple heuristic: if the sentence starts with a verb and doesn't have a subject pronoun early
            imperative_count += 1
        else:
            declarative_count += 1
    
    # 4. Citation density
    # Count patterns like [1], [12], (Author, Year), etc.
    citation_patterns = [
        r'\[\d+\]',           # [1], [12]
        r'\(\w+,\s*\d{4}\)',  # (Smith, 2020)
        r'\d{4}',             # Year standalone (less specific but common)
        r'et\s+al\.',         # et al.
        r'\b[A-Z][a-z]+\s+\d{4}\b' # Author Year (e.g., Smith 2020)
    ]
    
    citation_count = 0
    for pattern in citation_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        citation_count += len(matches)
    
    citation_density = citation_count / max(len(sentences), 1)
    
    # 5. Calculate imperative ratio
    # Ratio = imperative_count / total_sentences
    # Handle division by zero
    if total_sentences == 0:
        imperative_ratio = None  # Will be flagged later
        is_ratio_undefined = True
    else:
        imperative_ratio = imperative_count / total_sentences
        is_ratio_undefined = False
    
    return {
        'modal_verb_frequency': modal_freq,
        'total_sentences': total_sentences,
        'imperative_count': imperative_count,
        'declarative_count': declarative_count,
        'citation_density': citation_density,
        'imperative_ratio': imperative_ratio,
        'is_ratio_undefined': is_ratio_undefined
    }

def flag_undefined_imperative_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the 'is_ratio_undefined' flag is correctly set for all rows.
    Also impute undefined ratios with 0.0 for downstream compatibility.
    
    Args:
        df: DataFrame with feature columns including 'imperative_ratio'.
        
    Returns:
        DataFrame with updated 'is_ratio_undefined' and imputed 'imperative_ratio'.
    """
    # Ensure the flag column exists
    if 'is_ratio_undefined' not in df.columns:
        df['is_ratio_undefined'] = df['imperative_ratio'].isna()
    
    # Update flag based on total_sentences == 0 check if available
    if 'total_sentences' in df.columns:
        df['is_ratio_undefined'] = df['total_sentences'] == 0
    
    # Impute undefined ratios with 0.0 (safe default for modeling)
    # This prevents division-by-zero errors in downstream modeling (Phase 5)
    if 'imperative_ratio' in df.columns:
        df['imperative_ratio'] = df['imperative_ratio'].fillna(0.0)
    
    # Verify the flag is consistent with the data
    undefined_mask = df['is_ratio_undefined']
    if undefined_mask.any():
        logger.warning(f"Found {undefined_mask.sum()} rows with undefined imperative ratio. "
                     f"Imputed with 0.0 and flagged for exclusion from modeling if necessary.")
    
    return df

def run_feature_extraction(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Run feature extraction on a CSV file containing prompts.
    
    Args:
        input_path: Path to input CSV (e.g., data/raw/medmis_subset.csv).
        output_path: Path to output CSV (e.g., data/processed/features.csv).
        
    Returns:
        DataFrame with extracted features.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Reading input data from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'prompt_text' not in df.columns and 'text' not in df.columns:
        # Try to find a text column
        text_cols = [c for c in df.columns if 'text' in c.lower() or 'prompt' in c.lower()]
        if text_cols:
            text_col = text_cols[0]
            logger.info(f"Using column '{text_col}' as prompt text")
        else:
            raise ValueError(f"Could not find a text column in {input_path}. "
                           f"Expected 'prompt_text' or 'text'. Found: {df.columns.tolist()}")
    else:
        text_col = 'prompt_text' if 'prompt_text' in df.columns else 'text'
    
    logger.info(f"Extracting features from {len(df)} rows...")
    
    features_list = []
    for idx, row in df.iterrows():
        text = row[text_col]
        features = extract_features(text)
        features['prompt_id'] = row.get('prompt_id', idx)  # Keep prompt ID for merging
        features_list.append(features)
        
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} rows")
    
    features_df = pd.DataFrame(features_list)
    
    # Flag undefined ratios and impute
    features_df = flag_undefined_imperative_ratio(features_df)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Saving features to {output_path}")
    features_df.to_csv(output_path, index=False)
    
    # Log summary
    undefined_count = features_df['is_ratio_undefined'].sum()
    logger.info(f"Feature extraction complete. {len(features_df)} rows processed. "
               f"{undefined_count} rows have undefined imperative ratio (imputed to 0.0).")
    
    return features_df

def run_feature_extraction_pipeline() -> None:
    """
    Main pipeline entry point for feature extraction.
    Loads config, runs extraction, and saves results.
    """
    config = get_config()
    input_path = config.get('paths', {}).get('medmis_subset', 'data/raw/medmis_subset.csv')
    output_path = config.get('paths', {}).get('features', 'data/processed/features.csv')
    
    logger.info("Starting feature extraction pipeline")
    
    try:
        run_feature_extraction(input_path, output_path)
        logger.info("Feature extraction pipeline completed successfully")
    except Exception as e:
        logger.error(f"Feature extraction pipeline failed: {e}", exc_info=True)
        raise

def main():
    """
    CLI entry point.
    """
    run_feature_extraction_pipeline()

if __name__ == '__main__':
    main()
