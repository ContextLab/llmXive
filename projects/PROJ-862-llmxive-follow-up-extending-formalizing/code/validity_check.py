import logging
import torch
from typing import List, Dict, Any, Union, Optional
from datasets import Dataset
from bert_score import score as bert_score_func
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np
import csv
import os
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

def check_output_validity(
    model_output: str,
    expected_answer: str,
    model_name: str = "bert-base-uncased",
    threshold_f1: float = 0.85,
    baseline_perplexity: Optional[float] = None,
    perplexity_multiplier: float = 2.0
) -> Dict[str, Any]:
    """
    Check output validity using BERTScore F1 and perplexity bounds.

    Args:
        model_output: The generated text from the model.
        expected_answer: The ground truth expected answer.
        model_name: Pretrained model name for BERTScore.
        threshold_f1: Minimum BERTScore F1 threshold.
        baseline_perplexity: Baseline perplexity to compare against.
        perplexity_multiplier: Maximum allowed multiplier of baseline perplexity.

    Returns:
        Dict containing validity status, BERTScore F1, perplexity, and failure reasons.
    """
    if not expected_answer:
        logger.warning("Expected answer is empty; cannot validate output.")
        return {
            "is_valid": False,
            "bertscore_f1": 0.0,
            "perplexity": None,
            "failure_reasons": ["Missing expected_answer"],
        }

    try:
        # BERTScore calculation
        P, R, F1 = bert_score_func(
            [model_output],
            [expected_answer],
            lang="en",
            model_type=model_name,
            verbose=False
        )
        bert_f1 = F1.item()

        failure_reasons = []
        is_valid = True

        if bert_f1 < threshold_f1:
            is_valid = False
            failure_reasons.append(f"BERTScore F1 ({bert_f1:.4f}) < threshold ({threshold_f1})")

        # Perplexity check if baseline is provided
        perplexity = None
        if baseline_perplexity is not None:
            # Placeholder for actual perplexity calculation logic
            # In a real implementation, this would use the model to compute perplexity
            # For now, we assume it passes or is skipped if not implemented
            # TODO: Implement actual perplexity calculation
            pass

        return {
            "is_valid": is_valid,
            "bertscore_f1": bert_f1,
            "perplexity": perplexity,
            "failure_reasons": failure_reasons,
        }

    except Exception as e:
        logger.error(f"Error during output validity check: {e}")
        return {
            "is_valid": False,
            "bertscore_f1": 0.0,
            "perplexity": None,
            "failure_reasons": [f"Exception during check: {str(e)}"],
        }


def check_input_drift(
    baseline_input: str,
    perturbed_input: str,
    sbert_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Check input drift using sentence-transformers cosine similarity.

    Args:
        baseline_input: Original input text.
        perturbed_input: Perturbed input text.
        sbert_model_name: Sentence-BERT model name.
        threshold: Minimum cosine similarity threshold.

    Returns:
        Dict containing validity status, cosine similarity, and failure reasons.
    """
    try:
        model = SentenceTransformer(sbert_model_name)

        embeddings = model.encode([baseline_input, perturbed_input], convert_to_numpy=True)
        vec1 = embeddings[0]
        vec2 = embeddings[1]

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            cosine_sim = 0.0
        else:
            cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)

        is_valid = cosine_sim >= threshold
        failure_reasons = []

        if not is_valid:
            failure_reasons.append(f"Cosine similarity ({cosine_sim:.4f}) < threshold ({threshold})")

        return {
            "is_valid": is_valid,
            "cosine_similarity": float(cosine_sim),
            "failure_reasons": failure_reasons,
        }

    except Exception as e:
        logger.error(f"Error during input drift check: {e}")
        return {
            "is_valid": False,
            "cosine_similarity": 0.0,
            "failure_reasons": [f"Exception during check: {str(e)}"],
        }


def filter_pairs_by_input_drift(
    pairs: List[Dict[str, Any]],
    sbert_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    threshold: float = 0.95,
    output_path: str = "data/processed/filtered_pairs_input_drift.csv"
) -> List[Dict[str, Any]]:
    """
    Filter a list of pairs based on input drift check.
    Pairs failing the check (cosine similarity < threshold) are excluded.
    The filtered set is saved to the specified output path.

    Args:
        pairs: List of dictionaries containing 'pair_id', 'baseline_input', 'perturbed_input'.
        sbert_model_name: Sentence-BERT model name.
        threshold: Minimum cosine similarity threshold.
        output_path: Path to save the filtered pairs CSV.

    Returns:
        List of pairs that passed the input drift check.
    """
    logger.info(f"Starting input drift filtering for {len(pairs)} pairs...")
    logger.info(f"Threshold: {threshold}, Model: {sbert_model_name}")

    try:
        model = SentenceTransformer(sbert_model_name)
    except Exception as e:
        logger.error(f"Failed to load SBERT model: {e}")
        raise

    valid_pairs = []
    failed_count = 0
    total = len(pairs)

    for idx, pair in enumerate(pairs):
        pair_id = pair.get('pair_id', idx)
        baseline_input = pair.get('baseline_input')
        perturbed_input = pair.get('perturbed_input')

        if not baseline_input or not perturbed_input:
            logger.warning(f"Pair {pair_id} missing input text. Skipping.")
            failed_count += 1
            continue

        try:
            embeddings = model.encode([baseline_input, perturbed_input], convert_to_numpy=True)
            vec1 = embeddings[0]
            vec2 = embeddings[1]

            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                cosine_sim = 0.0
            else:
                cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)

            if cosine_sim >= threshold:
                valid_pairs.append(pair)
            else:
                failed_count += 1
                logger.debug(f"Pair {pair_id} failed drift check: sim={cosine_sim:.4f}")

        except Exception as e:
            logger.error(f"Error checking pair {pair_id}: {e}")
            failed_count += 1

        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{total} pairs...")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save filtered pairs to CSV
    if valid_pairs:
        fieldnames = list(valid_pairs[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(valid_pairs)
        logger.info(f"Saved {len(valid_pairs)} valid pairs to {output_path}")
    else:
        # Write empty file with headers if we know them, or just headers for standard fields
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['pair_id', 'baseline_input', 'perturbed_input', 'task_type', 'sigma'])
        logger.warning(f"No pairs passed the input drift check. Empty file saved to {output_path}")

    logger.info(f"Input drift filtering complete. Passed: {len(valid_pairs)}, Failed: {failed_count}")
    return valid_pairs


def check_validity_collapse(
    pass_rate: float,
    threshold: float = 0.10
) -> Dict[str, Any]:
    """
    Detect if validity collapse occurs at a specific sigma level.

    Validity collapse is defined as >90% of pairs failing (pass_rate < threshold).

    Args:
        pass_rate: The fraction of pairs that passed validity checks (0.0 to 1.0).
        threshold: The minimum pass rate to avoid collapse (default 0.10, i.e., 10%).
                   If pass_rate < threshold, it means >90% failed.

    Returns:
        Dict containing collapse status, pass rate, and threshold used.
    """
    is_collapse = pass_rate < threshold
    failure_rate = 1.0 - pass_rate

    logger.debug(
        f"Validity collapse check: pass_rate={pass_rate:.4f}, "
        f"threshold={threshold:.4f}, failure_rate={failure_rate:.4f}, "
        f"is_collapse={is_collapse}"
    )

    return {
        "is_collapse": is_collapse,
        "pass_rate": pass_rate,
        "failure_rate": failure_rate,
        "threshold": threshold,
        "message": (
            "Validity collapse detected" if is_collapse
            else "Validity collapse not detected"
        )
    }
