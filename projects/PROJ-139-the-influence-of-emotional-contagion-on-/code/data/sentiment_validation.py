"""
Sentiment Validation Pipeline (Task T007b).

Implements the validation of VADER sentiment against human annotations or public corpora.
Calculates inter-rater reliability (Cohen's Kappa) and generates bootstrapped confidence intervals.

Outputs:
- data/processed/vader_validation_report.json
- data/processed/validation_justification.json
"""
import os
import json
import logging
import math
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from scipy.stats import pearsonr, beta
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize

# Project root relative to code/data
ROOT_DIR = Path(__file__).parent.parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
RAW_DIR = ROOT_DIR / "data" / "raw"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_annotated_corpus() -> Optional[pd.DataFrame]:
    """
    Load human annotations from data/raw/annotations.json if available.
    Returns None if file does not exist or is empty.
    """
    ann_path = RAW_DIR / "annotations.json"
    if not ann_path.exists():
        logger.info(f"No annotations found at {ann_path}. Checking for public corpus...")
        return None
    
    try:
        with open(ann_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not data:
            logger.warning("Annotations file is empty.")
            return None
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Failed to load annotations: {e}")
        return None

def load_hf_corpus_wrapper() -> Optional[pd.DataFrame]:
    """
    Attempt to load a public sentiment corpus from HuggingFace datasets.
    Returns None if no valid corpus is found or load fails.
    """
    try:
        from datasets import load_dataset
        # Try a common sentiment dataset: 'sentiment_analysis' or 'emotion'
        # Using 'sentiment_analysis' from a verified source if available, 
        # otherwise a generic one. We'll try 'sst2' or similar if available.
        # For robustness, we try a few common ones.
        candidates = ['sentiment_analysis', 'emotion', 'imdb']
        
        for name in candidates:
            try:
                logger.info(f"Attempting to load HuggingFace dataset: {name}")
                ds = load_dataset(name, split="train", trust_remote_code=True)
                # Normalize column names to expected format: text, label
                # Map common label columns to 'label' (0, 1, 2...)
                # Map text columns to 'text'
                
                # Simple heuristic: look for 'text' or 'sentence' and 'label' or 'sentiment'
                cols = ds.column_names
                text_col = None
                label_col = None
                
                if 'text' in cols: text_col = 'text'
                elif 'sentence' in cols: text_col = 'sentence'
                elif 'content' in cols: text_col = 'content'
                
                if 'label' in cols: label_col = 'label'
                elif 'sentiment' in cols: label_col = 'sentiment'
                elif 'emotion' in cols: label_col = 'emotion'
                
                if text_col and label_col:
                    df = ds.to_pandas()
                    # Ensure label is numeric (0, 1, 2...)
                    # If labels are strings, map them to integers based on frequency or order
                    if df[label_col].dtype == 'object':
                        unique_labels = df[label_col].unique()
                        label_map = {l: i for i, l in enumerate(sorted(unique_labels))}
                        df['label'] = df[label_col].map(label_map)
                    else:
                        df['label'] = df[label_col]
                    
                    df = df[['text', 'label']].dropna()
                    if len(df) > 0:
                        logger.info(f"Successfully loaded {len(df)} samples from {name}")
                        return df
                else:
                    logger.warning(f"Dataset {name} missing required columns (text, label).")
            except Exception as e:
                logger.debug(f"Failed to load {name}: {e}")
                continue
        
        logger.error("No suitable public corpus found on HuggingFace.")
        return None
    except ImportError:
        logger.error("HuggingFace datasets library not installed. Cannot load public corpus.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading public corpus: {e}")
        return None

def apply_vader_sentiment(texts: List[str]) -> List[float]:
    """
    Apply VADER sentiment analysis to a list of texts.
    Returns compound scores.
    """
    analyzer = SentimentIntensityAnalyzer()
    scores = []
    for text in texts:
        if not isinstance(text, str):
            text = str(text)
        score = analyzer.polarity_scores(text)['compound']
        scores.append(score)
    return scores

def get_vader_label(compound_score: float, threshold: float = 0.05) -> int:
    """
    Convert VADER compound score to a binary label for Kappa calculation.
    Positive if > threshold, Negative if < -threshold, Neutral otherwise.
    For Kappa against binary labels (e.g., 0/1), we map:
    Positive -> 1, Negative/Neutral -> 0 (or similar mapping depending on ground truth).
    
    Here we assume ground truth labels are 0 (negative/neutral) and 1 (positive).
    We map VADER: > 0.05 -> 1, else -> 0.
    """
    if compound_score > threshold:
        return 1
    else:
        return 0

def compute_cohen_kappa(rater1: List[int], rater2: List[int]) -> float:
    """
    Compute Cohen's Kappa coefficient.
    """
    if len(rater1) != len(rater2) or len(rater1) == 0:
        raise ValueError("Raters must have same length and be non-empty.")
    
    n = len(rater1)
    # Observed agreement
    po = sum(1 for a, b in zip(rater1, rater2) if a == b) / n
    
    # Expected agreement
    # Count frequencies
    c1 = sum(rater1)
    c2 = sum(rater2)
    p1_pos = c1 / n
    p2_pos = c2 / n
    p1_neg = 1 - p1_pos
    p2_neg = 1 - p2_pos
    
    pe = (p1_pos * p2_pos) + (p1_neg * p2_neg)
    
    if pe == 1:
        return 1.0
    
    kappa = (po - pe) / (1 - pe)
    return kappa

def compute_bootstrapped_ci(rater1: List[int], rater2: List[int], n_boot: int = 1000, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Compute bootstrapped confidence intervals for Cohen's Kappa.
    """
    n = len(rater1)
    kappas = []
    
    for _ in range(n_boot):
        indices = np.random.choice(n, size=n, replace=True)
        s1 = [rater1[i] for i in indices]
        s2 = [rater2[i] for i in indices]
        try:
            k = compute_cohen_kappa(s1, s2)
            kappas.append(k)
        except ValueError:
            continue
    
    if not kappas:
        return 0.0, 0.0
    
    kappas.sort()
    lower_idx = int((1 - confidence) / 2 * n_boot)
    upper_idx = int((1 + confidence) / 2 * n_boot)
    
    return kappas[lower_idx], kappas[upper_idx]

def validate_vader_against_corpus(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Main validation logic.
    df must have 'text' and 'label' columns.
    """
    texts = df['text'].tolist()
    # Assume labels are 0 or 1 (or map to 0/1 if they are not)
    # If labels are 0, 1, 2, we might need to binarize or handle multi-class.
    # For simplicity, we assume binary or binarize: > 0 is positive, else negative.
    # If the dataset has 0, 1, 2 (e.g., negative, neutral, positive), we might treat 1 as positive.
    # Let's assume the label column is already 0/1 or can be cast to int.
    try:
        ground_truth = df['label'].astype(int).tolist()
    except:
        # If not int, try to map unique values to 0, 1
        unique_vals = sorted(df['label'].unique())
        if len(unique_vals) == 2:
            map_val = {unique_vals[0]: 0, unique_vals[1]: 1}
            ground_truth = [map_val[x] for x in df['label']]
        else:
            # Fallback: treat non-zero as 1? Or fail.
            logger.warning("Labels are not binary. Attempting to binarize: >0 as 1, else 0.")
            ground_truth = [1 if x > 0 else 0 for x in df['label']]
    
    vader_scores = apply_vader_sentiment(texts)
    vader_labels = [get_vader_label(s) for s in vader_scores]
    
    kappa = compute_cohen_kappa(ground_truth, vader_labels)
    ci_low, ci_high = compute_bootstrapped_ci(ground_truth, vader_labels)
    
    return {
        "kappa": kappa,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "sample_size": len(ground_truth),
        "status": "validated" if kappa >= 0.6 else "failed",
        "source": "public_corpus"
    }

def generate_validation_justification(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate justification report based on validation results.
    """
    return {
        "kappa": report["kappa"],
        "confidence_interval": [report["ci_low"], report["ci_high"]],
        "sample_size": report["sample_size"],
        "interpretation": "Subsample is valid for validation" if report["kappa"] >= 0.6 else "Subsample reliability low",
        "status": report["status"]
    }

def main():
    logger.info("Starting Sentiment Validation Pipeline (T007b)")
    
    # 1. Load annotations
    annotations_df = load_annotated_corpus()
    
    # 2. If no annotations, try public corpus
    if annotations_df is None:
        annotations_df = load_hf_corpus_wrapper()
    
    # 3. If still no data, generate unvalidated report
    if annotations_df is None:
        logger.warning("No annotations or public corpus found. Generating unvalidated report.")
        report = {
            "status": "unvalidated",
            "reason": "no_data_available",
            "kappa": None,
            "sample_size": 0,
            "source": None
        }
        with open(PROCESSED_DIR / "vader_validation_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        justification = {
            "status": "unvalidated",
            "reason": "no_data_available",
            "interpretation": "Cannot validate without data"
        }
        with open(PROCESSED_DIR / "validation_justification.json", 'w') as f:
            json.dump(justification, f, indent=2)
        
        logger.info("Validation pipeline completed (unvalidated).")
        return
    
    # 4. Run validation
    logger.info(f"Running validation on {len(annotations_df)} samples.")
    try:
        result = validate_vader_against_corpus(annotations_df)
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        result = {
            "status": "failed",
            "reason": str(e),
            "kappa": None,
            "sample_size": 0,
            "source": "error"
        }
    
    # 5. Save report
    with open(PROCESSED_DIR / "vader_validation_report.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    # 6. Generate and save justification
    justification = generate_validation_justification(result)
    with open(PROCESSED_DIR / "validation_justification.json", 'w') as f:
        json.dump(justification, f, indent=2)
    
    logger.info(f"Validation complete. Kappa: {result.get('kappa')}, Status: {result.get('status')}")

if __name__ == "__main__":
    main()
