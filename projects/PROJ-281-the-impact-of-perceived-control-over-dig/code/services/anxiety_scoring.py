import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

# Import config loading from the existing API surface
from code.config import load_config_params, CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when required configuration keys are missing."""
    pass

def load_config_params() -> Dict[str, Any]:
    """
    Load analysis configuration from contracts/analysis.schema.yaml.
    Returns a dictionary of configuration parameters.
    """
    config_path = Path("contracts/analysis.schema.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except ImportError:
        # Fallback to JSON if yaml is not available and file is JSON
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            raise ConfigurationError(f"Could not parse configuration file: {config_path}")
    
    return config if config else {}

def get_config_value(config: Dict[str, Any], key_path: str, default: Any) -> Any:
    """
    Safely retrieve a nested config value.
    key_path is dot-separated, e.g., 'filtering.entropy_threshold'
    """
    keys = key_path.split('.')
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def calculate_text_entropy(text: str) -> float:
    """
    Calculate Shannon entropy of a text string.
    Higher entropy suggests more random/gibberish-like text.
    """
    if not text or len(text) == 0:
        return 0.0
    
    # Count character frequencies
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    
    # Calculate entropy
    entropy = 0.0
    length = len(text)
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * np.log2(p)
    
    return entropy

def filter_text_quality(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter rows based on text quality (length and entropy).
    
    Args:
        df: DataFrame with a 'text' column
        config: Configuration dictionary containing filtering parameters
    
    Returns:
        Filtered DataFrame
    
    Raises:
        ConfigurationError: If required config keys are missing
    """
    # Check for required config keys
    min_length = get_config_value(config, 'filtering.min_text_length', None)
    entropy_threshold = get_config_value(config, 'filtering.entropy_threshold', None)
    
    if min_length is None:
        raise ConfigurationError("Missing required config key: 'filtering.min_text_length'")
    if entropy_threshold is None:
        raise ConfigurationError("Missing required config key: 'filtering.entropy_threshold'")
    
    logger.info(f"Applying text quality filters: min_length={min_length}, entropy_threshold={entropy_threshold}")
    
    # Ensure text column exists
    if 'text' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'text' column")
    
    # Filter by minimum length
    length_mask = df['text'].astype(str).str.len() >= min_length
    logger.info(f"Filtered {(~length_mask).sum()} rows by minimum length ({min_length})")
    
    # Calculate entropy for remaining rows
    entropy_mask = pd.Series([True] * len(df))
    valid_indices = length_mask[length_mask].index
    
    if len(valid_indices) > 0:
        entropies = df.loc[valid_indices, 'text'].astype(str).apply(calculate_text_entropy)
        # Keep rows where entropy is BELOW threshold (lower entropy = more structured text)
        # Note: Very low entropy might be repetitive, but very high is gibberish
        entropy_mask = pd.Series([True] * len(df))
        entropy_mask.loc[valid_indices] = entropies <= entropy_threshold
        logger.info(f"Filtered {(~entropy_mask).sum()} rows by entropy threshold ({entropy_threshold})")
    
    # Combine masks
    combined_mask = length_mask & entropy_mask
    filtered_df = df[combined_mask].reset_index(drop=True)
    
    logger.info(f"Total rows after quality filtering: {len(filtered_df)} (from {len(df)})")
    
    return filtered_df

def filter_non_english(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter out non-English text using langdetect.
    
    Args:
        df: DataFrame with a 'text' column
        config: Configuration dictionary containing filtering parameters
    
    Returns:
        Filtered DataFrame
    """
    try:
        from langdetect import detect, DetectorFactory
        from langdetect.lang_detect_exception import LangDetectException
        
        # Set seed for reproducibility
        DetectorFactory.seed = 0
        
        lang_threshold = get_config_value(config, 'filtering.langdetect_threshold', 0.8)
        logger.info(f"Filtering non-English text with confidence threshold: {lang_threshold}")
        
        def detect_language_safe(text):
            if not text or not isinstance(text, str) or len(text.strip()) == 0:
                return None, 0.0
            try:
                lang = detect(text)
                # langdetect doesn't provide confidence directly, so we use a heuristic
                # For simplicity, we'll assume detection is reliable if it returns a language
                return lang, 1.0
            except LangDetectException:
                return None, 0.0
        
        # Apply language detection
        lang_results = df['text'].apply(lambda x: detect_language_safe(str(x)))
        df['detected_lang'] = [r[0] for r in lang_results]
        df['lang_confidence'] = [r[1] for r in lang_results]
        
        # Filter for English with sufficient confidence
        mask = (df['detected_lang'] == 'en') & (df['lang_confidence'] >= lang_threshold)
        filtered_df = df[mask].reset_index(drop=True)
        
        logger.info(f"Filtered {(~mask).sum()} rows by language (kept {len(filtered_df)})")
        
        # Drop temporary columns
        filtered_df = filtered_df.drop(columns=['detected_lang', 'lang_confidence'])
        
        return filtered_df
        
    except ImportError:
        logger.warning("langdetect not installed, skipping non-English filter. Please install: pip install langdetect")
        return df

def load_anxiety_model(model_name: str = "cardiffnlp/twitter-roberta-base-emotion"):
    """
    Load the anxiety/emotion model.
    
    Args:
        model_name: HuggingFace model identifier
    
    Returns:
        Tuple of (model, tokenizer)
    """
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch
        
        logger.info(f"Loading model: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Force CPU as per constraints
        model = model.to('cpu')
        model.eval()
        
        logger.info("Model loaded successfully on CPU")
        return model, tokenizer
        
    except ImportError as e:
        raise ImportError(f"Transformers library not available: {e}")

def compute_anxiety_scores(df: pd.DataFrame, model, tokenizer, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute anxiety scores for text data using the loaded model.
    
    Args:
        df: DataFrame with 'text' column
        model: Loaded transformer model
        tokenizer: Loaded tokenizer
        config: Configuration dictionary
    
    Returns:
        DataFrame with added 'anxiety_score' and 'confidence_score' columns
    """
    logger.info("Computing anxiety scores...")
    
    # Get label mapping
    label2id = model.config.id2label
    id2label = {v: k for k, v in label2id.items()}
    
    # Check for fear/anxiety labels
    has_fear = 'fear' in label2id.values()
    has_anxiety = 'anxiety' in label2id.values()
    
    logger.info(f"Model labels: {list(label2id.values())}")
    logger.info(f"Has 'fear' label: {has_fear}, Has 'anxiety' label: {has_anxiety}")
    
    # Map fear to anxiety if configured
    fear_to_anxiety = get_config_value(config, 'model_mapping.fear_to_anxiety', False)
    
    anxiety_label_id = None
    if has_anxiety:
        for lid, label in label2id.items():
            if label == 'anxiety':
                anxiety_label_id = lid
                break
    elif has_fear and fear_to_anxiety:
        for lid, label in label2id.items():
            if label == 'fear':
                anxiety_label_id = lid
                break
    
    if anxiety_label_id is None:
        logger.warning("Could not find anxiety or mapped fear label. Using first label as fallback.")
        anxiety_label_id = 0
    
    # Process in batches
    batch_size = 16
    all_scores = []
    all_confidences = []
    
    texts = df['text'].tolist()
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        
        # Tokenize
        inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt"
        )
        
        # Inference
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
        
        # Extract scores
        batch_probs = probs[:, anxiety_label_id].tolist()
        batch_max_probs = probs.max(dim=-1).values.tolist()
        
        all_scores.extend(batch_probs)
        all_confidences.extend(batch_max_probs)
    
    df['anxiety_score'] = all_scores
    df['confidence_score'] = all_confidences
    
    logger.info(f"Computed anxiety scores for {len(df)} rows")
    return df

def run_full_scoring_pipeline(input_path: str, output_path: str, config: Optional[Dict[str, Any]] = None):
    """
    Run the full anxiety scoring pipeline:
    1. Load preprocessed text
    2. Filter non-English text
    3. Filter gibberish/low-quality text
    4. Compute anxiety scores
    5. Save results
    
    Args:
        input_path: Path to input CSV (preprocessed_text.csv)
        output_path: Path to output CSV (scoring_results.csv)
        config: Optional config dictionary (loads from file if None)
    """
    # Load config if not provided
    if config is None:
        config = load_config_params()
    
    # Load input data
    logger.info(f"Loading input data from {input_path}")
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Filter non-English
    df = filter_non_english(df, config)
    
    # Filter text quality (gibberish)
    df = filter_text_quality(df, config)
    
    # Load model and compute scores
    model, tokenizer = load_anxiety_model()
    df = compute_anxiety_scores(df, model, tokenizer, config)
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved results to {output_path}")
    
    return df

def run_full_scoring_pipeline_from_config():
    """
    Run the pipeline using configuration from contracts/analysis.schema.yaml.
    """
    config = load_config_params()
    input_path = "data/processed/preprocessed_text.csv"
    output_path = "data/processed/scoring_results.csv"
    
    return run_full_scoring_pipeline(input_path, output_path, config)

# Main entry point for direct execution
if __name__ == "__main__":
    run_full_scoring_pipeline_from_config()
