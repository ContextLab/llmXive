"""
Validity checking module for the llmXive noise injection pipeline.

This module implements checks for input drift, output validity, and validity collapse.
It ensures that noise injection does not degrade semantic meaning or model performance.
"""
import os
import csv
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from config import ValidityConfig
from memory_monitor import get_rss_memory_mb, check_memory_limit
from data_loader import ConfigurationError

# Module-level singleton for SBERT (lazy-loaded)
GLOBAL_SBERT: Optional[SentenceTransformer] = None
_SBERT_MODEL_NAME = "all-MiniLM-L6-v2"
_SBERT_DEVICE = "cpu"

logger = logging.getLogger(__name__)

def _get_sbert_model() -> SentenceTransformer:
    """
    Lazy-load the Sentence-BERT model as a module-level singleton.
    This ensures the model is loaded only once per process.
    """
    global GLOBAL_SBERT
    if GLOBAL_SBERT is None:
        logger.info(f"Loading SBERT model: {_SBERT_MODEL_NAME} on {_SBERT_DEVICE}")
        try:
            GLOBAL_SBERT = SentenceTransformer(_SBERT_MODEL_NAME, device=_SBERT_DEVICE)
            logger.info("SBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SBERT model: {e}")
            raise
    return GLOBAL_SBERT

def _compute_embedding_hash(text: str) -> str:
    """
    Compute a deterministic hash of the input text.
    Used for identifying unique embeddings in logs.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

def _get_text_from_vector_record(record: Dict[str, Any]) -> str:
    """
    Extract the original text question from a vector record.
    The record is expected to have 'question' or 'input_text' field.
    """
    if 'question' in record:
        return record['question']
    elif 'input_text' in record:
        return record['input_text']
    else:
        raise KeyError(f"Record missing 'question' or 'input_text' field: {record.keys()}")

def check_input_drift(
    baseline_input: str,
    perturbed_input: str,
    threshold: float = 0.95
) -> Tuple[float, bool]:
    """
    Check input drift between baseline and perturbed inputs using SBERT.
    
    Args:
        baseline_input: The original input text.
        perturbed_input: The perturbed input text.
        threshold: Minimum cosine similarity to pass (default 0.95).
        
    Returns:
        Tuple of (drift_score, pass_status) where drift_score is cosine similarity
        and pass_status is True if similarity >= threshold.
        
    Raises:
        RuntimeError: If SBERT model fails to load.
    """
    model = _get_sbert_model()
    
    # Check memory before encoding
    if not check_memory_limit():
        logger.warning("Memory limit approaching during SBERT encoding")
    
    # Encode inputs
    try:
        baseline_embedding = model.encode(baseline_input, convert_to_numpy=True, show_progress_bar=False)
        perturbed_embedding = model.encode(perturbed_input, convert_to_numpy=True, show_progress_bar=False)
    except Exception as e:
        logger.error(f"SBERT encoding failed: {e}")
        raise
    
    # Compute cosine similarity
    baseline_norm = np.linalg.norm(baseline_embedding)
    perturbed_norm = np.linalg.norm(perturbed_embedding)
    
    if baseline_norm == 0 or perturbed_norm == 0:
        logger.warning("Zero norm encountered in SBERT embedding")
        similarity = 0.0
    else:
        similarity = np.dot(baseline_embedding, perturbed_embedding) / (baseline_norm * perturbed_norm)
    
    # Ensure similarity is in [-1, 1] range (numerical stability)
    similarity = float(np.clip(similarity, -1.0, 1.0))
    
    pass_status = similarity >= threshold
    return similarity, pass_status

def filter_pairs_by_input_drift(
    baseline_vectors_path: str,
    perturbed_vectors_path: str,
    output_path: str,
    threshold: float = 0.95,
    config: Optional[ValidityConfig] = None
) -> Dict[str, Any]:
    """
    Filter pairs based on input drift check and save results to CSV.
    
    This function:
    1. Loads baseline and perturbed vector records
    2. Checks input drift for each pair
    3. Excludes pairs with cosine similarity < threshold
    4. Saves filtered results to CSV
    5. Returns statistics about the filtering process
    
    Args:
        baseline_vectors_path: Path to baseline_vectors.csv
        perturbed_vectors_path: Path to perturbed_vectors.csv
        output_path: Path to save filtered_pairs_input_drift.csv
        threshold: Minimum cosine similarity to pass (default 0.95)
        config: Optional ValidityConfig for parameters
        
    Returns:
        Dictionary with filtering statistics
        
    Raises:
        FileNotFoundError: If input files don't exist
        ConfigurationError: If required columns are missing
    """
    if config is not None:
        threshold = config.input_drift_threshold
    
    logger.info(f"Starting input drift filter with threshold: {threshold}")
    logger.info(f"Baseline vectors: {baseline_vectors_path}")
    logger.info(f"Perturbed vectors: {perturbed_vectors_path}")
    logger.info(f"Output path: {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load baseline vectors
    baseline_records = {}
    with open(baseline_vectors_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_cols = {'pair_id', 'task_type', 'question'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ConfigurationError(f"Baseline vectors missing required columns: {required_cols - set(reader.fieldnames or [])}")
        
        for row in reader:
            pair_id = row['pair_id']
            baseline_records[pair_id] = row
    
    # Load perturbed vectors
    perturbed_records = {}
    with open(perturbed_vectors_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_cols = {'pair_id', 'task_type', 'question', 'sigma'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ConfigurationError(f"Perturbed vectors missing required columns: {required_cols - set(reader.fieldnames or [])}")
        
        for row in reader:
            pair_id = row['pair_id']
            sigma = row['sigma']
            key = f"{pair_id}_{sigma}"
            perturbed_records[key] = row
    
    # Process pairs
    results = []
    passed_count = 0
    failed_count = 0
    total_count = 0
    
    for key, perturbed_record in perturbed_records.items():
        pair_id = perturbed_record['pair_id']
        sigma = perturbed_record['sigma']
        task_type = perturbed_record['task_type']
        
        if pair_id not in baseline_records:
            logger.warning(f"Pair {pair_id} not found in baseline vectors, skipping")
            continue
        
        baseline_record = baseline_records[pair_id]
        baseline_question = _get_text_from_vector_record(baseline_record)
        perturbed_question = _get_text_from_vector_record(perturbed_record)
        
        total_count += 1
        
        # Check input drift
        drift_score, passed = check_input_drift(baseline_question, perturbed_question, threshold)
        
        baseline_hash = _compute_embedding_hash(baseline_question)
        perturbed_hash = _compute_embedding_hash(perturbed_question)
        
        result = {
            'PairID': pair_id,
            'baseline_embedding_hash': baseline_hash,
            'perturbed_embedding_hash': perturbed_hash,
            'drift_score': f"{drift_score:.6f}",
            'pass/fail': 'pass' if passed else 'fail',
            'task_type': task_type,
            'sigma': sigma
        }
        results.append(result)
        
        if passed:
            passed_count += 1
        else:
            failed_count += 1
        
        # Log progress every 100 pairs
        if total_count % 100 == 0:
            logger.info(f"Processed {total_count} pairs: {passed_count} passed, {failed_count} failed")
            logger.info(f"Current RSS: {get_rss_memory_mb():.2f} MB")
    
    # Save results
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['PairID', 'baseline_embedding_hash', 'perturbed_embedding_hash', 'drift_score', 'pass/fail']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            # Only write the required columns
            row = {k: result[k] for k in fieldnames}
            writer.writerow(row)
    
    # Log summary
    logger.info(f"Input drift filtering complete:")
    logger.info(f"  Total pairs processed: {total_count}")
    logger.info(f"  Passed: {passed_count} ({100*passed_count/total_count:.1f}%)")
    logger.info(f"  Failed: {failed_count} ({100*failed_count/total_count:.1f}%)")
    logger.info(f"  Output saved to: {output_path}")
    
    return {
        'total_processed': total_count,
        'passed': passed_count,
        'failed': failed_count,
        'pass_rate': passed_count / total_count if total_count > 0 else 0.0,
        'output_path': output_path
    }

def check_output_validity(
    model_output: str,
    expected_answer: str,
    bertscore_threshold: float = 0.85,
    perplexity_threshold: float = 2.0
) -> Dict[str, Any]:
    """
    Check if model output is valid compared to expected answer.
    
    Uses BERTScore for semantic similarity and perplexity for fluency.
    
    Args:
        model_output: The model's generated output.
        expected_answer: The ground truth expected answer.
        bertscore_threshold: Minimum BERTScore F1 to pass.
        perplexity_threshold: Maximum allowed perplexity multiplier.
        
    Returns:
        Dictionary with validity check results.
        
    Raises:
        ConfigurationError: If BERTScore check fails or expected_answer is missing.
    """
    try:
        from bert_score import score as bert_score_fn
    except ImportError:
        raise ConfigurationError("bert_score package not installed. Please install it via pip install bert_score")
    
    if not expected_answer or expected_answer.strip() == "":
        raise ConfigurationError("Expected answer is missing or empty. Cannot perform output validity check.")
    
    # Compute BERTScore
    try:
        P, R, F1 = bert_score_fn([model_output], [expected_answer], lang="en", verbose=False)
        bertscore_f1 = F1[0].item()
    except Exception as e:
        logger.error(f"BERTScore computation failed: {e}")
        raise
    
    # Check BERTScore threshold
    bertscore_passed = bertscore_f1 >= bertscore_threshold
    
    # Compute perplexity (simplified - using language model)
    # Note: In a full implementation, we would use a language model to compute perplexity
    # For now, we'll use a placeholder that always passes if BERTScore passes
    # This should be replaced with actual perplexity computation in production
    perplexity_multiplier = 1.0  # Placeholder
    perplexity_passed = perplexity_multiplier <= perplexity_threshold
    
    overall_passed = bertscore_passed and perplexity_passed
    
    return {
        'bertscore_f1': bertscore_f1,
        'bertscore_passed': bertscore_passed,
        'perplexity_multiplier': perplexity_multiplier,
        'perplexity_passed': perplexity_passed,
        'overall_passed': overall_passed
    }

def check_validity_collapse(
    pass_rates: List[float],
    threshold: float = 0.1
) -> Tuple[bool, Optional[int]]:
    """
    Check if validity has collapsed at a specific sigma level.
    
    Validity collapse is defined as >90% failure rate (pass_rate < threshold).
    
    Args:
        pass_rates: List of pass rates at different sigma levels.
        threshold: Maximum pass rate to consider as collapse (default 0.1 = 10%).
        
    Returns:
        Tuple of (collapsed, collapse_index) where collapse_index is the index
        in pass_rates where collapse first occurred.
    """
    for i, rate in enumerate(pass_rates):
        if rate < threshold:
            return True, i
    
    return False, None

def main():
    """
    Main function to run input drift filtering.
    This is intended to be called from the main pipeline or as a standalone script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter pairs by input drift")
    parser.add_argument("--baseline", required=True, help="Path to baseline_vectors.csv")
    parser.add_argument("--perturbed", required=True, help="Path to perturbed_vectors.csv")
    parser.add_argument("--output", required=True, help="Path to save filtered_pairs_input_drift.csv")
    parser.add_argument("--threshold", type=float, default=0.95, help="Minimum cosine similarity")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        stats = filter_pairs_by_input_drift(
            baseline_vectors_path=args.baseline,
            perturbed_vectors_path=args.perturbed,
            output_path=args.output,
            threshold=args.threshold
        )
        
        print(json.dumps(stats, indent=2))
        
    except Exception as e:
        logger.error(f"Input drift filtering failed: {e}")
        raise

if __name__ == "__main__":
    main()
