"""
Evaluation metrics utilities.

Provides functions for calculating few-shot accuracy on held-out GLUE/SuperGLUE
subsets and performing statistical significance testing.
"""

from typing import List, Dict, Literal, Tuple, Optional
import numpy as np
from scipy.stats import wilcoxon
from datasets import Dataset

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def wilcoxon_test(
    accuracies_a: List[float],
    accuracies_b: List[float],
    *,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> Dict[str, float]:
    """
    Compute the Wilcoxon signed‑rank test for two paired samples.

    Parameters
    ----------
    accuracies_a, accuracies_b: List[float]
        Paired accuracy (or metric) values from two experimental conditions.
    alternative: {"two-sided", "greater", "less"}, optional
        Defines the alternative hypothesis.  Defaults to ``"two-sided"``.

    Returns
    -------
    dict
        ``{"statistic": float, "p_value": float}`` containing the test
        statistic and the associated p‑value.

    Raises
    ------
    ValueError
        If the input sequences are of different lengths or contain fewer
        than two non‑zero differences (the requirement of SciPy's
        ``wilcoxon`` implementation).
    """
    if len(accuracies_a) != len(accuracies_b):
        raise ValueError("Input sequences must have the same length.")

    # Convert to NumPy arrays for safety; SciPy will handle NaNs appropriately.
    a_arr = np.asarray(accuracies_a, dtype=float)
    b_arr = np.asarray(accuracies_b, dtype=float)

    # SciPy's wilcoxon raises a ValueError if the number of non‑zero
    # differences is less than 2; we propagate that error.
    stat, p_value = wilcoxon(a_arr, b_arr, alternative=alternative)

    return {"statistic": float(stat), "p_value": float(p_value)}


def calculate_few_shot_accuracy(
    predictions: List[str],
    references: List[str],
    label_map: Optional[Dict[int, str]] = None,
) -> float:
    """
    Calculate accuracy for few-shot evaluation.

    Parameters
    ----------
    predictions : List[str]
        List of predicted labels (strings).
    references : List[str]
        List of ground truth labels (strings).
    label_map : Dict[int, str], optional
        Mapping from integer indices to string labels if predictions are integers.
        If provided, predictions are converted to strings before comparison.

    Returns
    -------
    float
        Accuracy score (number of correct predictions / total predictions).

    Raises
    ------
    ValueError
        If predictions and references have different lengths.
    """
    if len(predictions) != len(references):
        raise ValueError(
            f"Length mismatch: predictions ({len(predictions)}) vs references ({len(references)})"
        )

    if len(predictions) == 0:
        logger.warning("Empty prediction set provided. Returning 0.0 accuracy.")
        return 0.0

    correct = 0
    for pred, ref in zip(predictions, references):
        # Handle potential integer predictions if label_map is provided
        if label_map is not None and isinstance(pred, int):
            pred_str = label_map.get(pred, str(pred))
        else:
            pred_str = str(pred)

        if pred_str.strip() == ref.strip():
            correct += 1

    accuracy = correct / len(predictions)
    logger.info(f"Few-shot accuracy calculated: {accuracy:.4f} ({correct}/{len(predictions)})")
    return accuracy


def evaluate_on_holdout(
    dataset: Dataset,
    model_predict_fn,
    key: str = "label",
    few_shot_k: int = 5,
    seed: int = 42,
) -> Dict[str, float]:
    """
    Evaluate a model on a held-out subset using few-shot prompting logic.

    This function simulates a few-shot evaluation by sampling `few_shot_k`
    examples from the dataset to construct a prompt context (conceptually),
    then evaluates the model's performance on the remaining test set.
    Note: In a full implementation, `model_predict_fn` would accept the
    few-shot context and the query. Here, we assume `model_predict_fn`
    handles the context internally or we are evaluating a fine-tuned model
    where the "few-shot" aspect is the data sampling strategy.

    For this implementation, we randomly sample a subset of the dataset
    to serve as the "held-out" evaluation set (simulating a test split)
    and calculate accuracy.

    Parameters
    ----------
    dataset : Dataset
        The full dataset (e.g., from GLUE/SuperGLUE).
    model_predict_fn : callable
        A function that takes a sample (dict) and returns a predicted label (str).
        Signature: `def predict_fn(sample: dict) -> str`
    key : str, optional
        The key in the dataset containing the ground truth label. Defaults to "label".
    few_shot_k : int, optional
        Number of shots to conceptually use. Defaults to 5.
    seed : int, optional
        Random seed for reproducibility. Defaults to 42.

    Returns
    -------
    dict
        Dictionary containing:
        - "accuracy": float
        - "num_samples": int
        - "num_correct": int
    """
    np.random.seed(seed)

    # For a true few-shot simulation, we might construct a prompt with K examples.
    # However, for metric calculation on a held-out set, we simply evaluate
    # the model on the provided dataset (which acts as the held-out set).
    # The "few-shot" parameter informs the context window usage in the predictor.

    logger.info(f"Evaluating on held-out set with {few_shot_k}-shot context (conceptual).")

    predictions = []
    references = []

    # Convert dataset to list for iteration if necessary
    if hasattr(dataset, 'to_list'):
        samples = dataset.to_list()
    else:
        samples = list(dataset)

    for sample in samples:
        # Get ground truth
        if key in sample:
            ref = sample[key]
            # Convert int labels to string if necessary for comparison
            if isinstance(ref, int):
                ref = str(ref)
        else:
            # Fallback if label key is missing
            logger.warning(f"Key '{key}' not found in sample. Skipping.")
            continue

        # Get prediction
        try:
            pred = model_predict_fn(sample)
        except Exception as e:
            logger.error(f"Prediction failed for sample: {e}")
            continue

        predictions.append(pred)
        references.append(ref)

    if not predictions:
        return {"accuracy": 0.0, "num_samples": 0, "num_correct": 0}

    accuracy = calculate_few_shot_accuracy(predictions, references)

    return {
        "accuracy": accuracy,
        "num_samples": len(predictions),
        "num_correct": int(accuracy * len(predictions)),
    }