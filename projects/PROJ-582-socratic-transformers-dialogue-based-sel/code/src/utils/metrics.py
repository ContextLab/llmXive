"""
Metric utility for standard accuracy and loss calculations.
"""

import math
from typing import List, Optional, Tuple, Union
import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

class MetricCalculator:
    """Calculates various metrics for model evaluation."""

    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.model.eval()

    def compute_accuracy(self, predictions: List[int], labels: List[int]) -> float:
        """
        Computes accuracy given predicted and true token IDs.

        Args:
            predictions: List of predicted token IDs.
            labels: List of true token IDs.

        Returns:
            Accuracy score.
        """
        if len(predictions) != len(labels):
            raise ValueError("Predictions and labels must be of the same length.")
        
        if not predictions:
            return 0.0

        correct = sum(p == l for p, l in zip(predictions, labels))
        return correct / len(predictions)

    def compute_loss(self, input_ids: torch.Tensor, labels: torch.Tensor) -> float:
        """
        Computes the loss for a given batch.

        Args:
            input_ids: Input token IDs.
            labels: Target token IDs.

        Returns:
            The computed loss.
        """
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, labels=labels)
            return outputs.loss.item()

def compute_prediction_error_proxy(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    question: str,
    answer: str
) -> float:
    """
    Computes a proxy for prediction error by evaluating the likelihood of the answer.

    Args:
        model: The model.
        tokenizer: The tokenizer.
        question: The question string.
        answer: The answer string.

    Returns:
        A proxy error score (negative log likelihood).
    """
    prompt = f"Question: {question}\nAnswer: {answer}"
    inputs = tokenizer(prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model(**inputs, labels=inputs['input_ids'])
        loss = outputs.loss.item()
    
    return loss

def compute_calibration_error(
    predicted_probs: List[float],
    actual_outcomes: List[bool]
) -> float:
    """
    Computes the calibration error (Brier score variant).

    Args:
        predicted_probs: List of predicted probabilities.
        actual_outcomes: List of boolean outcomes.

    Returns:
        The calibration error.
    """
    if len(predicted_probs) != len(actual_outcomes):
        raise ValueError("Lengths must match.")
    
    total_error = 0.0
    for p, actual in zip(predicted_probs, actual_outcomes):
        actual_val = 1.0 if actual else 0.0
        total_error += (p - actual_val) ** 2
    
    return total_error / len(predicted_probs)

def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 2
) -> float:
    """
    Computes the n-gram overlap (Jaccard similarity) between two texts.

    Args:
        text1: First text.
        text2: Second text.
        n: N-gram size.

    Returns:
        Jaccard similarity score.
    """
    def get_ngrams(text, n):
        words = text.lower().split()
        return set([' '.join(words[i:i+n]) for i in range(len(words) - n + 1)])

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = ngrams1.intersection(ngrams2)
    union = ngrams1.union(ngrams2)

    return len(intersection) / len(union)

def main():
    """Test the metrics utility."""
    print("Metrics utility initialized.")

if __name__ == "__main__":
    main()
