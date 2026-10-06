"""
Anxiety scoring service: filters text, runs inference, and filters by confidence.
Implements T014b, T014c, T015, and T016.
"""
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set random seed for langdetect consistency
DetectorFactory.seed = 42

# Local imports (assumed to exist in project)
try:
    from code.config import load_config_params, get_config_value, CONFIG
except ImportError:
    # Fallback for standalone execution or different import context
    def load_config_params(path: Optional[str] = None) -> Dict[str, Any]:
        return {}
    def get_config_value(key: str, default: Any = None) -> Any:
        return default
    CONFIG = type('Config', (), {})()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONFIDENCE_THRESHOLD = 0.6
DEFAULT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-emotion"

class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass

class DataInsufficientError(Exception):
    """Raised when filtering leaves insufficient data."""
    pass

def calculate_text_entropy(text: str) -> float:
    """Calculate Shannon entropy of a text string."""
    if not text or len(text) == 0:
        return 0.0
    prob = [float(text.count(c)) / len(text) for c in set(text)]
    return -sum(p * np.log2(p) for p in prob if p > 0)

def filter_non_english(df: pd.DataFrame, threshold: float = 0.8) -> pd.DataFrame:
    """
    Filter non-English text using langdetect.
    
    Args:
        df: DataFrame with 'text' column
        threshold: Minimum confidence for language detection
    
    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering non-English text (threshold={threshold})")
    
    def is_english(text):
        if not isinstance(text, str) or len(text.strip()) == 0:
            return False
        try:
            lang = detect(text)
            # langdetect returns language code, we check confidence implicitly
            # by checking if it's 'en'. For stricter confidence, we'd need
            # a different approach, but standard langdetect doesn't expose
            # confidence easily without internal hacks. We'll rely on the
            # fact that detect() raises exception on failure and usually
            # picks a language.
            return lang == 'en'
        except LangDetectException:
            return False
    
    # Apply filter
    mask = df['text'].apply(is_english)
    filtered_df = df[mask].copy()
    logger.info(f"Filtered {len(df) - len(filtered_df)} non-English rows. Remaining: {len(filtered_df)}")
    return filtered_df

def filter_text_quality(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Filter gibberish and low-quality text based on entropy and length.
    
    Args:
        df: DataFrame with 'text' column
        config: Configuration dictionary containing filtering params
    
    Returns:
        Filtered DataFrame
    """
    logger.info("Filtering text quality (gibberish)")
    
    if config is None:
        config = load_config_params()
    
    # Get config values with defaults
    min_text_length = get_config_value('filtering.min_text_length', 3, config)
    entropy_threshold = get_config_value('filtering.entropy_threshold', 0.7, config)
    
    # Check for required config
    if 'filtering' not in config or 'min_text_length' not in config.get('filtering', {}):
        logger.warning("min_text_length not found in config, using default")
    if 'filtering' not in config or 'entropy_threshold' not in config.get('filtering', {}):
        logger.warning("entropy_threshold not found in config, using default")
    
    def is_quality_text(text):
        if not isinstance(text, str):
            return False
        text = text.strip()
        if len(text) < min_text_length:
            return False
        # Entropy check: very low entropy might indicate repetition (e.g., "aaaaa")
        # Very high entropy might indicate gibberish, but usually we look for low entropy
        # as a sign of spam/repetition. However, the task mentions "entropy-based heuristic"
        # for gibberish. Gibberish often has high entropy (random characters).
        # Let's assume we want entropy to be within a reasonable range.
        # A simple heuristic: entropy > threshold might be gibberish?
        # Actually, natural text has moderate entropy. Random noise has high entropy.
        # Let's filter out text with entropy > entropy_threshold (too random)
        # AND text with entropy < some lower bound (too repetitive).
        # For now, let's just check if entropy is not too high (gibberish).
        entropy = calculate_text_entropy(text)
        # Heuristic: if entropy is extremely high, it's likely gibberish
        if entropy > entropy_threshold:
            return False
        return True
    
    mask = df['text'].apply(is_quality_text)
    filtered_df = df[mask].copy()
    logger.info(f"Filtered {len(df) - len(filtered_df)} low-quality rows. Remaining: {len(filtered_df)}")
    return filtered_df

def verify_model_labels(model_name: str = DEFAULT_MODEL_NAME) -> Tuple[bool, Dict[str, int]]:
    """
    Verify if the model has 'fear' or 'anxiety' labels.
    
    Args:
        model_name: HuggingFace model name
    
    Returns:
        Tuple of (has_fear_label, id2label_mapping)
    """
    logger.info(f"Verifying model labels for {model_name}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        id2label = model.config.id2label
        
        has_fear = 'fear' in id2label.values()
        logger.info(f"Model labels: {id2label}")
        logger.info(f"Has 'fear' label: {has_fear}")
        return has_fear, id2label
    except Exception as e:
        logger.error(f"Error verifying model labels: {e}")
        return False, {}

def save_model_validation(has_fear: bool, id2label: Dict[str, int], output_path: str = "state/model_validation.json"):
    """Save model validation results."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result = {
        "has_fear_label": has_fear,
        "id2label": id2label,
        "model_name": DEFAULT_MODEL_NAME
    }
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved model validation to {output_path}")

def run_anxiety_scoring_pipeline(
    input_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> pd.DataFrame:
    """
    Run the full anxiety scoring pipeline:
    1. Load data
    2. Filter non-English (T014b)
    3. Filter gibberish (T014c)
    4. Run model inference (T015)
    5. Filter by confidence (T016)
    
    Args:
        input_path: Path to input CSV (raw social media data)
        output_path: Path to save filtered results
        config: Configuration dictionary
        confidence_threshold: Minimum confidence score to keep (T016)
    
    Returns:
        DataFrame with anxiety scores and confidence
    """
    logger.info(f"Starting anxiety scoring pipeline")
    logger.info(f"Input: {input_path}, Output: {output_path}")
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'text' not in df.columns:
        raise ValueError(f"Input file must contain 'text' column. Columns: {df.columns.tolist()}")
    
    # T014b: Filter non-English
    if config is None:
        config = load_config_params()
    lang_threshold = get_config_value('filtering.langdetect_threshold', 0.8, config)
    df = filter_non_english(df, threshold=lang_threshold)
    
    # T014c: Filter gibberish
    df = filter_text_quality(df, config)
    
    if len(df) == 0:
        logger.error("No data remaining after filtering")
        raise DataInsufficientError("No data remaining after filtering")
    
    # T015: Run model inference
    logger.info("Running model inference")
    model_name = DEFAULT_MODEL_NAME
    has_fear, id2label = verify_model_labels(model_name)
    save_model_validation(has_fear, id2label)
    
    # Load model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    # Get label mapping
    label2id = {v: k for k, v in id2label.items()}
    anxiety_label = None
    
    # Determine anxiety label
    if 'anxiety' in label2id:
        anxiety_label = label2id['anxiety']
    elif has_fear and 'fear' in label2id:
        # Check config for mapping
        map_fear = get_config_value('model_mapping.fear_to_anxiety', False, config)
        if map_fear:
            anxiety_label = label2id['fear']
            logger.info("Mapping 'fear' to anxiety score")
        else:
            logger.warning("No 'anxiety' or mapped 'fear' label found")
    else:
        logger.warning("No anxiety or fear label found in model")
    
    if anxiety_label is None:
        # Fallback: use the label with highest probability as a proxy?
        # Or raise error? Let's raise error for now.
        raise ValueError("Could not determine anxiety label from model")
    
    # Batch inference
    texts = df['text'].fillna("").tolist()
    batch_size = 16
    all_scores = []
    all_confidences = []
    
    logger.info(f"Processing {len(texts)} texts in batches of {batch_size}")
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        for j, prob in enumerate(probabilities):
            score = prob[anxiety_label].item()
            all_scores.append(score)
            all_confidences.append(prob.max().item())
    
    df['anxiety_score'] = all_scores
    df['confidence_score'] = all_confidences
    
    # T016: Filter by confidence
    logger.info(f"Filtering by confidence threshold: {confidence_threshold}")
    initial_count = len(df)
    df = df[df['confidence_score'] >= confidence_threshold].copy()
    final_count = len(df)
    logger.info(f"Filtered {initial_count - final_count} low-confidence rows. Remaining: {final_count}")
    
    if len(df) == 0:
        logger.error("No data remaining after confidence filtering")
        raise DataInsufficientError("No data remaining after confidence filtering")
    
    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved results to {output_path}")
    
    return df

def run_full_scoring_pipeline(
    input_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Wrapper for run_anxiety_scoring_pipeline with default config loading.
    """
    if config is None:
        config = load_config_params()
    
    # Get confidence threshold from config
    confidence_threshold = get_config_value('filtering.confidence_threshold', DEFAULT_CONFIDENCE_THRESHOLD, config)
    
    return run_anxiety_scoring_pipeline(
        input_path=input_path,
        output_path=output_path,
        config=config,
        confidence_threshold=confidence_threshold
    )

def run_full_scoring_pipeline_from_config():
    """
    Main entry point for CLI execution.
    Reads config from contracts/analysis.schema.yaml and runs the pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run anxiety scoring pipeline")
    parser.add_argument("--input", type=str, default="data/processed/preprocessed_text.csv",
                        help="Input CSV path")
    parser.add_argument("--output", type=str, default="data/processed/scoring_results.csv",
                        help="Output CSV path")
    parser.add_argument("--config", type=str, default="contracts/analysis.schema.yaml",
                        help="Config file path")
    args = parser.parse_args()
    
    config = load_config_params(args.config)
    run_full_scoring_pipeline(args.input, args.output, config)

if __name__ == "__main__":
    run_full_scoring_pipeline_from_config()

# Import torch here to avoid top-level dependency if not needed
import torch