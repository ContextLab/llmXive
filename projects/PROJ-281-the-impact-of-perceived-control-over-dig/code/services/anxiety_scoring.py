import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from langdetect import detect, LangDetectException
from langdetect.lang_detect_exception import DetectorCreationError

# Import config utilities from the project
from code.config import CONFIG
from code.services.proxy_extractor import load_analysis_config
from code.services.anxiety_scoring import ConfigurationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config_params() -> Dict[str, Any]:
    """Load configuration parameters for anxiety scoring."""
    return CONFIG.get("anxiety_scoring", {})

def calculate_text_entropy(text: str) -> float:
    """Calculate character-level entropy of a text string."""
    if not text or len(text) < 2:
        return 0.0
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1
    length = len(text)
    entropy = 0.0
    for count in char_counts.values():
        prob = count / length
        if prob > 0:
            entropy -= prob * np.log2(prob)
    return entropy

def filter_text_quality(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter text quality based on entropy and length.
    Reads thresholds from contracts/analysis.schema.yaml.
    """
    try:
        config = load_analysis_config()
        entropy_threshold = config.get("gibberish_filter", {}).get("entropy_threshold", 2.5)
        min_length = config.get("gibberish_filter", {}).get("min_length", 3)
    except (FileNotFoundError, KeyError) as e:
        logger.error(f"Configuration missing for gibberish filter: {e}")
        raise ConfigurationError("Missing gibberish filter configuration in contracts/analysis.schema.yaml")

    def is_gibberish(row):
        text = row.get("text", "")
        if not isinstance(text, str) or len(text) < min_length:
            return True
        entropy = calculate_text_entropy(text)
        return entropy > entropy_threshold

    # Filter out gibberish
    mask = df.apply(is_gibberish, axis=1)
    filtered_df = df[~mask].copy()
    logger.info(f"Filtered out {len(df) - len(filtered_df)} rows due to gibberish detection.")
    return filtered_df

def filter_non_english(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out non-English text using langdetect.
    Returns only rows where detected language is 'en'.
    """
    logger.info("Starting non-English text filtering...")
    
    def detect_language_safe(text):
        if not isinstance(text, str) or len(text.strip()) == 0:
            return None
        try:
            return detect(text)
        except (LangDetectException, DetectorCreationError):
            return None

    # Apply detection
    logger.info("Detecting languages for %d rows...", len(df))
    df["detected_lang"] = df["text"].apply(detect_language_safe)
    
    # Keep only English
    english_mask = df["detected_lang"] == "en"
    english_df = df[english_mask].copy()
    
    logger.info("Language detection complete. Kept %d English rows out of %d total.", 
                len(english_df), len(df))
    
    # Drop the temporary column before returning
    return english_df.drop(columns=["detected_lang"])

def load_anxiety_model():
    """Load the anxiety/emotion model (placeholder for T015)."""
    # This will be implemented in T015
    pass

def compute_anxiety_scores(df: pd.DataFrame):
    """Compute anxiety scores (placeholder for T015)."""
    # This will be implemented in T015
    pass

def run_full_scoring_pipeline():
    """
    Run the full anxiety scoring pipeline including:
    1. Load preprocessed text (from T013/T014b input)
    2. Filter non-English text (T014b)
    3. Filter gibberish (T014c)
    4. Compute scores (T015)
    5. Filter confidence (T016)
    6. Save results (T017)
    """
    input_path = CONFIG["paths"]["raw_data"] / "social_media.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # T014b: Filter non-English
    df_en = filter_non_english(df)
    
    # T014c: Filter gibberish
    df_clean = filter_text_quality(df_en)
    
    # T015: Compute scores (placeholder)
    # df_scored = compute_anxiety_scores(df_clean)
    
    # T016: Filter confidence (placeholder)
    # df_filtered = filter_by_confidence(df_scored)
    
    # T017: Save results (placeholder)
    output_path = CONFIG["paths"]["processed_data"] / "preprocessed_text.csv"
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Saved preprocessed text to {output_path}")
    
    return df_clean

def run_full_scoring_pipeline_from_config():
    """Entry point for external callers."""
    return run_full_scoring_pipeline()
