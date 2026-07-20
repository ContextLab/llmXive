import os
import json
import logging
import math
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from scipy import stats
import numpy as np

# Import from project API surface
from data.sampling import load_hf_corpus
from config.settings import get_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_annotated_corpus() -> Optional[pd.DataFrame]:
    """
    Load human annotations if they exist in data/raw/annotations.json.
    Returns None if the file does not exist.
    """
    config = get_config()
    annotation_path = config.dataset_paths.raw / "annotations.json"

    if not annotation_path.exists():
        logger.info(f"Human annotations not found at {annotation_path}. Proceeding with HuggingFace corpus.")
        return None

    try:
        with open(annotation_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Ensure required columns exist
        if 'text' not in df.columns or 'label' not in df.columns:
            raise ValueError("Annotation file must contain 'text' and 'label' columns.")
        
        logger.info(f"Loaded {len(df)} human annotations.")
        return df
    except Exception as e:
        logger.warning(f"Failed to load human annotations: {e}. Proceeding with HuggingFace corpus.")
        return None

def apply_vader_sentiment(texts: List[str]) -> List[float]:
    """
    Apply VADER sentiment analysis to a list of texts.
    Returns a list of compound scores.
    """
    sia = SentimentIntensityAnalyzer()
    scores = []
    for text in texts:
        if pd.isna(text) or not isinstance(text, str):
            scores.append(0.0)
        else:
            score = sia.polarity_scores(text)['compound']
            scores.append(score)
    return scores

def load_hf_corpus_wrapper() -> pd.DataFrame:
    """
    Wrapper to load the HuggingFace sentiment corpus as a fallback.
    Uses the sampling module's logic to fetch real data.
    """
    try:
        # The sampling module provides a function to load the HF corpus
        # We assume it returns a DataFrame with 'text' and 'label' (or equivalent sentiment label)
        df = load_hf_corpus()
        
        # If the loaded corpus doesn't have 'label' but has 'sentiment', map it
        if 'sentiment' in df.columns and 'label' not in df.columns:
            # Map sentiment strings to numeric labels if necessary, or keep as is if VADER comparison is string-based
            # For Cohen's Kappa, we need categorical labels. 
            # Standard NLTK sentiment corpus uses 0 (neg) and 1 (pos) usually, or specific classes.
            # Let's ensure we have a 'label' column for the reliability calculation.
            if 'label' not in df.columns:
                # Assuming the HF dataset 'sentiment' has 0/1 or 'neg'/'pos'
                # If it's 0/1, we are good. If it's strings, we map.
                pass 
            else:
                df['label'] = df['sentiment']
        
        return df
    except Exception as e:
        logger.error(f"Failed to load HuggingFace corpus: {e}")
        raise RuntimeError("Could not load real data source for validation. Pipeline cannot proceed.")

def get_vader_label(compound_score: float, threshold: float = 0.05) -> int:
    """
    Convert VADER compound score to a binary label (0: negative, 1: positive).
    Neutral is often treated as negative or excluded, but for binary Kappa:
    < -threshold -> 0 (Negative)
    > threshold -> 1 (Positive)
    In between -> 0 (Negative/Neutral) or excluded. 
    Standard practice for binary validation: Neg/Pos.
    """
    if compound_score > threshold:
        return 1
    else:
        return 0

def compute_cohen_kappa(labels_true: List[int], labels_pred: List[int]) -> float:
    """
    Compute Cohen's Kappa coefficient between two lists of labels.
    """
    if len(labels_true) != len(labels_pred):
        raise ValueError("Label lists must be of equal length.")
    
    if len(labels_true) == 0:
        return 0.0

    # Use scipy.stats.cohen_kappa
    kappa, _ = stats.cohen_kappa(labels_true, labels_pred)
    return float(kappa)

def compute_bootstrapped_ci(
    labels_true: List[int], 
    labels_pred: List[int], 
    n_iterations: int = 1000, 
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Compute bootstrapped confidence intervals for Cohen's Kappa.
    """
    n = len(labels_true)
    if n == 0:
        return (0.0, 0.0)

    kappa_samples = []
    for _ in range(n_iterations):
        # Sample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        true_sample = [labels_true[i] for i in indices]
        pred_sample = [labels_pred[i] for i in indices]
        
        # Compute Kappa for this sample
        # Handle edge cases where only one class exists in sample (Kappa undefined)
        try:
            kappa_val, _ = stats.cohen_kappa(true_sample, pred_sample)
            if not math.isnan(kappa_val):
                kappa_samples.append(kappa_val)
        except ValueError:
            continue # Skip samples with only one class

    if not kappa_samples:
        logger.warning("Could not compute bootstrap samples for CI.")
        return (0.0, 0.0)

    kappa_samples.sort()
    lower_idx = int((1 - confidence) / 2 * n_iterations)
    upper_idx = int((1 + confidence) / 2 * n_iterations)
    
    lower = kappa_samples[lower_idx] if lower_idx < len(kappa_samples) else 0.0
    upper = kappa_samples[upper_idx] if upper_idx < len(kappa_samples) else 0.0

    return (lower, upper)

def validate_vader_against_corpus(
    df: pd.DataFrame, 
    use_human: bool = False
) -> Dict[str, Any]:
    """
    Run VADER against the corpus and compute reliability metrics.
    """
    texts = df['text'].tolist()
    # Assume 'label' is the ground truth (0 or 1)
    if 'label' not in df.columns:
        raise ValueError("Corpus must have a 'label' column for validation.")
    
    true_labels = df['label'].tolist()
    
    # Apply VADER
    compound_scores = apply_vader_sentiment(texts)
    
    # Convert VADER scores to labels
    pred_labels = [get_vader_label(s) for s in compound_scores]
    
    # Compute Kappa
    kappa = compute_cohen_kappa(true_labels, pred_labels)
    
    # Compute CI
    ci_lower, ci_upper = compute_bootstrapped_ci(true_labels, pred_labels)
    
    source = "human_annotations" if use_human else "hf_corpus"
    
    return {
        "source": source,
        "sample_size": len(df),
        "kappa": kappa,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "mean_compound": float(np.mean(compound_scores)),
        "vader_distribution": {
            "positive": sum(1 for l in pred_labels if l == 1),
            "negative": sum(1 for l in pred_labels if l == 0)
        }
    }

def generate_validation_justification(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a justification report based on the validation results.
    """
    kappa = report['kappa']
    ci = (report['ci_lower'], report['ci_upper'])
    
    justification = {
        "kappa_value": kappa,
        "confidence_interval": {
            "lower": ci[0],
            "upper": ci[1]
        },
        "interpretation": "",
        "validity_justification": ""
    }
    
    if kappa >= 0.6:
        justification["interpretation"] = "Substantial agreement"
        justification["validity_justification"] = f"Kappa ({kappa:.3f}) >= 0.6 indicates VADER is reliable for this corpus."
    elif kappa >= 0.4:
        justification["interpretation"] = "Moderate agreement"
        justification["validity_justification"] = f"Kappa ({kappa:.3f}) is between 0.4 and 0.6. Use with caution."
    else:
        justification["interpretation"] = "Poor agreement"
        justification["validity_justification"] = f"Kappa ({kappa:.3f}) < 0.4. VADER may not be suitable for this specific domain without calibration."
    
    return justification

def main():
    """
    Main entry point for the Sentiment Validation Pipeline.
    """
    config = get_config()
    output_dir = config.dataset_paths.processed
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    # Try human annotations first
    df_human = load_annotated_corpus()
    
    if df_human is not None:
        logger.info("Using human annotations for validation.")
        df = df_human
        use_human = True
    else:
        logger.info("Loading HuggingFace corpus for validation.")
        df = load_hf_corpus_wrapper()
        use_human = False

    # 2. Validate
    validation_results = validate_vader_against_corpus(df, use_human=use_human)
    
    # 3. Save Validation Report
    report_path = output_dir / "vader_validation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2)
    logger.info(f"Saved validation report to {report_path}")

    # 4. Generate Justification
    justification = generate_validation_justification(validation_results)
    justification_path = output_dir / "validation_justification.json"
    with open(justification_path, 'w', encoding='utf-8') as f:
        json.dump(justification, f, indent=2)
    logger.info(f"Saved validation justification to {justification_path}")

    # 5. Log Summary
    logger.info(f"Validation Complete. Kappa: {validation_results['kappa']:.3f} ({validation_results['source']})")
    if validation_results['kappa'] < 0.6:
        logger.warning("Kappa is below 0.6 threshold. Review justification for details.")

if __name__ == "__main__":
    main()
