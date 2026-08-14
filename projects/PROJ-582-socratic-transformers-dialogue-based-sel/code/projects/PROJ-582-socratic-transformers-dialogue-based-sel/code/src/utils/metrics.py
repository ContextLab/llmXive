"""
Metric utility for standard accuracy and loss calculations.

This module provides functions to compute evaluation metrics for the
Socratic Transformers pipeline, including accuracy, loss, and proxy
metrics for prediction error and calibration.
"""

import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

class MetricCalculator:
    """
    A utility class for calculating various evaluation metrics.

    Attributes:
        device (torch.device): The device to perform calculations on.
    """

    def __init__(self, device: Optional[torch.device] = None):
        """
        Initialize the MetricCalculator.

        Args:
            device: The device to use for calculations. Defaults to CUDA if available, else CPU.
        """
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device

    def compute_accuracy(
        self,
        predictions: Union[List[int], torch.Tensor],
        labels: Union[List[int], torch.Tensor]
    ) -> float:
        """
        Computes the accuracy between predictions and labels.

        Args:
            predictions: The predicted token IDs or logits.
            labels: The ground truth token IDs.

        Returns:
            float: The accuracy score (0.0 to 1.0).
        """
        if isinstance(predictions, torch.Tensor):
            preds = predictions.argmax(dim=-1) if predictions.dim() > 1 else predictions
        else:
            preds = torch.tensor(predictions)

        if isinstance(labels, torch.Tensor):
            true_labels = labels
        else:
            true_labels = torch.tensor(labels)

        # Ensure tensors are on the same device
        preds = preds.to(self.device)
        true_labels = true_labels.to(self.device)

        # Handle padding if necessary (assuming -100 is the ignore index)
        mask = true_labels != -100
        if not mask.any():
            return 0.0

        correct = (preds[mask] == true_labels[mask]).sum().item()
        total = mask.sum().item()

        return correct / total if total > 0 else 0.0

    def compute_loss(
        self,
        model: PreTrainedModel,
        input_ids: torch.Tensor,
        labels: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> float:
        """
        Computes the loss for a given model and input batch.

        Args:
            model: The HuggingFace model instance.
            input_ids: The input token IDs.
            labels: The ground truth labels.
            attention_mask: Optional attention mask.

        Returns:
            float: The computed loss value.
        """
        model.to(self.device)
        input_ids = input_ids.to(self.device)
        labels = labels.to(self.device)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)

        with torch.no_grad():
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss

        return loss.item()


def compute_prediction_error_proxy(
    predictions: List[float],
    targets: List[float]
) -> float:
    """
    Computes a proxy for prediction error, such as Mean Squared Error (MSE).

    This is useful for continuous outputs or confidence scores.

    Args:
        predictions: A list of predicted values.
        targets: A list of target values.

    Returns:
        float: The mean squared error.

    Raises:
        ValueError: If input lists have different lengths or are empty.
    """
    if len(predictions) != len(targets):
        raise ValueError("Predictions and targets must have the same length.")
    if not predictions:
        raise ValueError("Input lists cannot be empty.")

    mse = sum((p - t) ** 2 for p, t in zip(predictions, targets)) / len(predictions)
    return mse


def compute_calibration_error(
    predicted_confidences: List[float],
    correct_flags: List[bool]
) -> float:
    """
    Computes the Expected Calibration Error (ECE) proxy.

    This measures the difference between predicted confidence and actual accuracy.

    Args:
        predicted_confidences: List of confidence scores (0.0 to 1.0).
        correct_flags: List of booleans indicating if the prediction was correct.

    Returns:
        float: The average absolute difference between confidence and correctness.

    Raises:
        ValueError: If input lists have different lengths or are empty.
    """
    if len(predicted_confidences) != len(correct_flags):
        raise ValueError("Confidences and correct flags must have the same length.")
    if not predicted_confidences:
        raise ValueError("Input lists cannot be empty.")

    total_error = 0.0
    for conf, is_correct in zip(predicted_confidences, correct_flags):
        actual_accuracy = 1.0 if is_correct else 0.0
        total_error += abs(conf - actual_accuracy)

    return total_error / len(predicted_confidences)


def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 2
) -> float:
    """
    Computes the n-gram overlap (Jaccard similarity) between two texts.

    Args:
        text1: The first text string.
        text2: The second text string.
        n: The size of the n-grams (default is 2 for bigrams).

    Returns:
        float: The Jaccard similarity coefficient (0.0 to 1.0).
    """
    def get_ngrams(text: str, n: int) -> set:
        words = text.lower().split()
        if len(words) < n:
            return set()
        return set(tuple(words[i:i+n]) for i in range(len(words) - n + 1))

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    if not ngrams1 and not ngrams2:
        return 1.0
    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = ngrams1.intersection(ngrams2)
    union = ngrams1.union(ngrams2)

    return len(intersection) / len(union)
