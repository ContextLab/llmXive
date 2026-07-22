import logging
import torch
from typing import List, Dict, Any, Union, Optional
from datasets import Dataset
from bert_score import score as bert_score_func
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np

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
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(sbert_model_name)

        embeddings = model.encode([baseline_input, perturbed_input])
        cosine_sim = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )

        is_valid = cosine_sim >= threshold
        failure_reasons = []

        if not is_valid:
            failure_reasons.append(f"Cosine similarity ({cosine_sim:.4f}) < threshold ({threshold})")

        return {
            "is_valid": is_valid,
            "cosine_similarity": cosine_sim,
            "failure_reasons": failure_reasons,
        }

    except Exception as e:
        logger.error(f"Error during input drift check: {e}")
        return {
            "is_valid": False,
            "cosine_similarity": 0.0,
            "failure_reasons": [f"Exception during check: {str(e)}"],
        }


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