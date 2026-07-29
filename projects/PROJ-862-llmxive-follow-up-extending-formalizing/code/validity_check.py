"""
Validity checks for input drift and output validity using SBERT and BERTScore.
Implements incremental writing to ensure data hygiene and prevent data loss on crash.
"""
import os
import csv
import json
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
import bert_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/validity_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"
INPUT_DRIFT_THRESHOLD = 0.95
OUTPUT_VALIDITY_BERTSCORE_THRESHOLD = 0.85
OUTPUT_VALIDITY_PERPLEXITY_MAX = 2.0

# Global singleton for SBERT model (lazy-loaded)
GLOBAL_SBERT = None
GLOBAL_SBERT_LOCK = False  # Simple flag for lazy loading

class SBERTLoadError(Exception):
    """Raised when SBERT model fails to load."""
    pass

def get_sbert() -> SentenceTransformer:
    """
    Lazy-load the SBERT model as a module-level singleton.
    This ensures the model is loaded only once and reused across calls.
    """
    global GLOBAL_SBERT, GLOBAL_SBERT_LOCK

    if GLOBAL_SBERT is not None:
        return GLOBAL_SBERT

    # Simple lock mechanism to prevent race conditions in multi-threaded environments
    # In a production environment, use threading.Lock()
    if GLOBAL_SBERT_LOCK:
        # Wait briefly for the model to load
        time.sleep(0.1)
        return get_sbert()

    GLOBAL_SBERT_LOCK = True
    try:
        logger.info(f"Loading SBERT model: {SBERT_MODEL_NAME}")
        # Load on CPU to avoid GPU memory issues
        GLOBAL_SBERT = SentenceTransformer(SBERT_MODEL_NAME, device='cpu')
        logger.info("SBERT model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load SBERT model: {e}")
        raise SBERTLoadError(f"Failed to load SBERT model: {e}")
    finally:
        GLOBAL_SBERT_LOCK = False

    return GLOBAL_SBERT

def check_input_drift(baseline_input: str, perturbed_input: str) -> Tuple[bool, float]:
    """
    Check for input drift between baseline and perturbed inputs using SBERT.

    Args:
        baseline_input: The original input text
        perturbed_input: The perturbed input text

    Returns:
        Tuple of (is_valid, cosine_similarity)
        - is_valid: True if cosine similarity >= INPUT_DRIFT_THRESHOLD
        - cosine_similarity: The calculated cosine similarity score
    """
    sbert = get_sbert()

    # Encode inputs
    try:
        baseline_embedding = sbert.encode(baseline_input, convert_to_numpy=True, show_progress_bar=False)
        perturbed_embedding = sbert.encode(perturbed_input, convert_to_numpy=True, show_progress_bar=False)
    except Exception as e:
        logger.error(f"Failed to encode inputs for drift check: {e}")
        return False, 0.0

    # Calculate cosine similarity
    # Ensure embeddings are normalized
    baseline_embedding = baseline_embedding / np.linalg.norm(baseline_embedding)
    perturbed_embedding = perturbed_embedding / np.linalg.norm(perturbed_embedding)

    cosine_similarity = np.dot(baseline_embedding, perturbed_embedding)

    # Check if similarity meets threshold
    is_valid = cosine_similarity >= INPUT_DRIFT_THRESHOLD

    return is_valid, float(cosine_similarity)

def check_input_drift_incremental(
    baseline_inputs: List[str],
    perturbed_inputs: List[str],
    pair_ids: List[str],
    task_types: List[str],
    sigma: float,
    output_path: str
) -> List[Dict[str, Any]]:
    """
    Check input drift for a batch of pairs and write results incrementally.
    This function appends to the validity_log.csv file immediately after processing
    each batch to ensure data hygiene and prevent loss on crash.

    Args:
        baseline_inputs: List of baseline input texts
        perturbed_inputs: List of perturbed input texts
        pair_ids: List of pair IDs
        task_types: List of task types
        sigma: The noise sigma value used for perturbation
        output_path: Path to the validity_log.csv file

    Returns:
        List of dictionaries containing drift check results for all pairs
    """
    if len(baseline_inputs) != len(perturbed_inputs) or \
       len(baseline_inputs) != len(pair_ids) or \
       len(baseline_inputs) != len(task_types):
        raise ValueError("All input lists must have the same length")

    results = []
    sbert = get_sbert()

    # Prepare to write to CSV
    file_exists = os.path.exists(output_path)

    with open(output_path, 'a', newline='') as csvfile:
        fieldnames = ['pair_id', 'task_type', 'sigma', 'baseline_input', 'perturbed_input',
                     'cosine_similarity', 'is_valid', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for i in range(len(baseline_inputs)):
            pair_id = pair_ids[i]
            task_type = task_types[i]
            baseline_input = baseline_inputs[i]
            perturbed_input = perturbed_inputs[i]

            # Check input drift
            is_valid, similarity = check_input_drift(baseline_input, perturbed_input)

            result = {
                'pair_id': pair_id,
                'task_type': task_type,
                'sigma': sigma,
                'baseline_input': baseline_input,
                'perturbed_input': perturbed_input,
                'cosine_similarity': similarity,
                'is_valid': is_valid,
                'timestamp': time.time()
            }
            results.append(result)

            # Write immediately to ensure data hygiene
            writer.writerow(result)

            # Log progress
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(baseline_inputs)} pairs for sigma={sigma}")

    return results

def filter_pairs_by_input_drift(
    validity_log_path: str,
    output_path: str
) -> List[str]:
    """
    Filter pairs that passed the input drift check and save to a new CSV file.
    This function reads the validity_log.csv and extracts pairs with is_valid=True.

    Args:
        validity_log_path: Path to the validity_log.csv file
        output_path: Path to save the filtered pairs CSV

    Returns:
        List of pair_ids that passed the input drift check
    """
    if not os.path.exists(validity_log_path):
        logger.error(f"Validity log file not found: {validity_log_path}")
        return []

    passed_pair_ids = []

    with open(validity_log_path, 'r') as infile, open(output_path, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        if fieldnames is None:
            logger.error("Invalid CSV file: no fieldnames found")
            return []

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if row.get('is_valid', 'False') == 'True':
                writer.writerow(row)
                passed_pair_ids.append(row['pair_id'])

    logger.info(f"Filtered {len(passed_pair_ids)} pairs that passed input drift check")
    return passed_pair_ids

def check_output_validity(
    model_output: str,
    expected_answer: str,
    tokenizer,
    model
) -> Tuple[bool, float, float]:
    """
    Check output validity using BERTScore and perplexity.

    Args:
        model_output: The model's generated output
        expected_answer: The ground truth expected answer
        tokenizer: The tokenizer for the model
        model: The model for perplexity calculation

    Returns:
        Tuple of (is_valid, bert_score_f1, perplexity_ratio)
        - is_valid: True if BERTScore F1 >= OUTPUT_VALIDITY_BERTSCORE_THRESHOLD
                    and perplexity_ratio <= OUTPUT_VALIDITY_PERPLEXITY_MAX
        - bert_score_f1: The BERTScore F1 score
        - perplexity_ratio: The ratio of output perplexity to baseline perplexity
    """
    # Calculate BERTScore
    try:
        P, R, F1 = bert_score.score(
            cands=[model_output],
            ref=[expected_answer],
            lang='en',
            verbose=False
        )
        bert_score_f1 = float(F1[0])
    except Exception as e:
        logger.error(f"Failed to calculate BERTScore: {e}")
        return False, 0.0, float('inf')

    # Calculate perplexity ratio
    # We'll use a simple approach: calculate perplexity of the output vs the expected answer
    try:
        # Tokenize both outputs
        output_tokens = tokenizer(model_output, return_tensors='pt', truncation=True, max_length=512)
        expected_tokens = tokenizer(expected_answer, return_tensors='pt', truncation=True, max_length=512)

        # Calculate log probabilities
        with torch.no_grad():
            output_loss = model(**output_tokens, labels=output_tokens['input_ids']).loss
            expected_loss = model(**expected_tokens, labels=expected_tokens['input_ids']).loss

        # Convert loss to perplexity
        output_perplexity = torch.exp(output_loss).item()
        expected_perplexity = torch.exp(expected_loss).item()

        # Calculate ratio (handle division by zero)
        if expected_perplexity > 0:
            perplexity_ratio = output_perplexity / expected_perplexity
        else:
            perplexity_ratio = float('inf')

    except Exception as e:
        logger.error(f"Failed to calculate perplexity: {e}")
        perplexity_ratio = float('inf')

    # Check if both conditions are met
    is_valid = (bert_score_f1 >= OUTPUT_VALIDITY_BERTSCORE_THRESHOLD and
               perplexity_ratio <= OUTPUT_VALIDITY_PERPLEXITY_MAX)

    return is_valid, bert_score_f1, perplexity_ratio

def check_validity_collapse(
    pass_rate: float,
    threshold: float = 0.90
) -> bool:
    """
    Check if validity has collapsed at a specific sigma level.
    Validity collapse is defined as >90% of pairs failing at a specific sigma.

    Args:
        pass_rate: The current pass rate (0.0 to 1.0)
        threshold: The threshold for collapse detection (default 0.90)

    Returns:
        True if validity has collapsed (pass_rate < 1 - threshold)
    """
    return pass_rate < (1 - threshold)

def main():
    """
    Main function to demonstrate the validity check functionality.
    This is primarily for testing and validation purposes.
    """
    logger.info("Starting validity check demonstration")

    # Example usage
    baseline_input = "What is the capital of France?"
    perturbed_input = "What is the capital of France? (slightly modified)"

    is_valid, similarity = check_input_drift(baseline_input, perturbed_input)
    logger.info(f"Input drift check result: valid={is_valid}, similarity={similarity:.4f}")

    logger.info("Validity check demonstration completed")

if __name__ == "__main__":
    main()
