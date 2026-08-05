from typing import List, Dict, Literal, Tuple, Optional
import numpy as np
from scipy.stats import wilcoxon
from datasets import Dataset
from config import Config
from utils.logger import get_logger
from sklearn.metrics import accuracy_score

logger = get_logger(__name__)

def wilcoxon_test(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    """
    Performs a Wilcoxon signed-rank test on two paired samples.
    Returns (statistic, p-value).
    """
    if len(sample1) != len(sample2):
        raise ValueError("Samples must be of equal length for Wilcoxon test.")
    
    statistic, p_value = wilcoxon(sample1, sample2)
    return statistic, p_value

def calculate_few_shot_accuracy(predictions: List[int], labels: List[int]) -> float:
    """
    Calculates accuracy for few-shot evaluation.
    """
    if not predictions or not labels:
        return 0.0
    return accuracy_score(labels, predictions)

def evaluate_on_holdout(model, dataset: Dataset, config: Config) -> float:
    """
    Evaluates a model on a hold-out dataset.
    """
    # Placeholder for actual evaluation logic
    # In a real implementation, this would run inference and collect predictions
    logger.info(f"Evaluating on holdout set of size {len(dataset)}")
    # Simulate a calculation for the sake of the structure if model is not fully implemented in this context
    # But since we are implementing T036, we assume the trainer returns real accuracy.
    # This function is a stub for the API surface if needed elsewhere.
    return 0.0
