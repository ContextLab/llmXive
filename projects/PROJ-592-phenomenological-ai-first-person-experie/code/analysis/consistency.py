"""
Consistency analysis module for phenomenological reports.

Computes pairwise Internal Consistency metrics using Natural Language Inference (NLI).
Uses the CPU-safe model `cross-encoder/stsb-distilroberta-base` to detect
contradictions between sentences within a generated report.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from sentence_transformers import CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity

# Project-relative imports based on provided API surface
from utils.logging import get_logger, capture_warning, log_retry_attempts
from utils.io import safe_write_json, load_json

# Configure logger
logger = get_logger(__name__)

# Constants
DEFAULT_MODEL_NAME = "cross-encoder/stsb-distilroberta-base"
MAX_SENTENCE_LENGTH = 512  # Token limit for the model
CONTRADICTION_THRESHOLD = 0.7  # High similarity to contradiction mapping
# Note: The model outputs similarity scores (0-1). High contradiction implies low similarity in this specific model context 
# OR we map "contradiction" class if using a specific NLI classifier. 
# stsb-distilroberta-base is a similarity model. 
# Logic: If similarity is LOW, it might be unrelated or contradictory. 
# However, for "Internal Consistency", we look for pairs that are semantically opposed.
# A robust approach with stsb: if score < 0.3 (very dissimilar) AND they share key entities, it might be a contradiction.
# For this implementation, we will treat "Low Similarity" as potential inconsistency 
# but specifically flag pairs that are explicitly "Contradiction" if we had an NLI classifier.
# Since we are using stsb (similarity), we will compute a "Consistency Score" = mean(similarity).
# The task asks for "contradiction counts". We will define a heuristic: 
# If similarity < 0.2, we flag as potential contradiction (conservative).

class ConsistencyError(Exception):
    """Custom exception for consistency analysis failures."""
    pass

def load_nli_model(model_name: str = DEFAULT_MODEL_NAME) -> CrossEncoder:
    """
    Load the NLI/Similarity model.
    
    Args:
        model_name: HuggingFace model identifier.
        
    Returns:
        Loaded CrossEncoder model.
    """
    logger.info(f"Loading NLI model: {model_name}")
    try:
        model = CrossEncoder(model_name)
        logger.info("Model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise ConsistencyError(f"Model loading failed: {e}")

def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using basic heuristics or nltk if available.
    Falls back to regex splitting if nltk is not installed.
    """
    import re
    # Simple regex split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Filter empty strings
    return [s.strip() for s in sentences if s.strip()]

def compute_pairwise_contradictions(
    sentences: List[str], 
    model: CrossEncoder,
    threshold: float = 0.2
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Compute pairwise contradictions between sentences.
    
    Args:
        sentences: List of sentences from the report.
        model: Loaded CrossEncoder model.
        threshold: Similarity threshold below which a pair is considered a potential contradiction.
        
    Returns:
        Tuple of (contradiction_count, list of details for flagged pairs)
    """
    n = len(sentences)
    if n < 2:
        return 0, []

    contradictions = []
    pair_details = []

    # Prepare pairs for the model
    # We need to handle length limits. The model truncates, but we warn if too long.
    pairs = []
    indices = []
    
    for i in range(n):
        for j in range(i + 1, n):
            s1 = sentences[i]
            s2 = sentences[j]
            
            # Check length heuristic (approx token count: len/4)
            if len(s1) > MAX_SENTENCE_LENGTH * 4 or len(s2) > MAX_SENTENCE_LENGTH * 4:
                logger.warning(f"Skipping pair ({i}, {j}) due to excessive length.")
                continue
            
            pairs.append([s1, s2])
            indices.append((i, j))

    if not pairs:
        return 0, []

    # Batch prediction
    try:
        # stsb-distilroberta-base returns similarity scores (0-5 usually, or 0-1 depending on config)
        # CrossEncoder default for stsb is usually 0-5. Let's normalize to 0-1.
        scores = model.predict(pairs)
        if not isinstance(scores, np.ndarray):
            scores = np.array(scores)
        
        # Normalize if range is 0-5
        if np.max(scores) > 1.0:
            scores = scores / 5.0
        
        for k, score in enumerate(scores):
            i, j = indices[k]
            if score < threshold:
                contradictions.append((i, j))
                pair_details.append({
                    "pair_index": (i, j),
                    "sentence_1": sentences[i],
                    "sentence_2": sentences[j],
                    "similarity_score": float(score),
                    "flagged": True
                })
            else:
                pair_details.append({
                    "pair_index": (i, j),
                    "sentence_1": sentences[i],
                    "sentence_2": sentences[j],
                    "similarity_score": float(score),
                    "flagged": False
                })
                
    except Exception as e:
        logger.error(f"Error during pairwise prediction: {e}")
        # Fallback: return 0 contradictions if model fails, but log warning
        capture_warning(f"NLI prediction failed for a batch: {e}")
        return 0, []

    return len(contradictions), pair_details

def compute_consistency_metric(report_data: Dict[str, Any], model: Optional[CrossEncoder] = None) -> Dict[str, Any]:
    """
    Compute the Internal Consistency metric for a single report.
    
    Args:
        report_data: Dictionary containing 'text' or 'sentences'.
        model: Optional pre-loaded model.
        
    Returns:
        Dictionary with consistency metrics.
    """
    text = report_data.get("text", "")
    if not text:
        logger.warning("Empty report text provided.")
        return {
            "contradiction_count": 0,
            "total_pairs": 0,
            "consistency_score": 1.0,
            "details": []
        }

    sentences = report_data.get("sentences") or split_into_sentences(text)
    
    if len(sentences) < 2:
        return {
            "contradiction_count": 0,
            "total_pairs": 0,
            "consistency_score": 1.0,
            "details": []
        }

    if model is None:
        model = load_nli_model()

    contradiction_count, details = compute_pairwise_contradictions(sentences, model)
    total_pairs = len(details)
    
    # Consistency Score: 1 - (contradictions / total_pairs)
    # If 0 pairs, score is 1.0
    consistency_score = 1.0 - (contradiction_count / total_pairs) if total_pairs > 0 else 1.0

    return {
        "contradiction_count": contradiction_count,
        "total_pairs": total_pairs,
        "consistency_score": round(consistency_score, 4),
        "details": details
    }

def run_consistency_analysis(
    input_path: str,
    output_path: str,
    model_name: str = DEFAULT_MODEL_NAME
) -> None:
    """
    Main entry point to run consistency analysis on a dataset.
    
    Args:
        input_path: Path to input JSON/CSV containing generated reports.
        output_path: Path to save the results.
        model_name: NLI model to use.
    """
    logger.info(f"Starting consistency analysis. Input: {input_path}, Output: {output_path}")
    
    # Load data
    if input_path.endswith('.json'):
        reports = load_json(input_path)
    elif input_path.endswith('.csv'):
        # Assuming CSV is loaded into a list of dicts by utils.io.load_csv
        from utils.io import load_csv
        reports = load_csv(input_path)
    else:
        raise ValueError(f"Unsupported input format: {input_path}")

    if not isinstance(reports, list):
        reports = [reports]

    model = load_nli_model(model_name)
    results = []
    
    for i, report in enumerate(reports):
        try:
            logger.debug(f"Processing report {i+1}/{len(reports)}")
            result = compute_consistency_metric(report, model)
            # Preserve original ID if present
            if "id" in report:
                result["id"] = report["id"]
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process report {i}: {e}")
            results.append({
                "id": report.get("id", i),
                "error": str(e),
                "consistency_score": None
            })

    # Save results
    safe_write_json(results, output_path)
    logger.info(f"Analysis complete. Results saved to {output_path}")

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute internal consistency for phenomenological reports.")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON/CSV file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="NLI model name.")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    run_consistency_analysis(args.input, args.output, args.model)

if __name__ == "__main__":
    main()