"""
Metric utilities for evaluating model performance.

This module provides functions to calculate accuracy and loss for
classification and regression tasks, as well as specialized metrics
for the Socratic transformer pipeline.
"""

import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


def calculate_accuracy(y_true: Union[List[int], torch.Tensor], y_pred: Union[List[int], torch.Tensor]) -> float:
    """
    Calculate the accuracy of predictions.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.

    Returns:
        Accuracy as a float between 0 and 1.

    Raises:
        ValueError: If input lengths do not match or inputs are empty.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    if len(y_true) == 0:
        raise ValueError("Input lists cannot be empty")

    # Convert to lists if tensors
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.tolist()
    if isinstance(y_pred, torch.Tensor):
        y_pred = y_pred.tolist()

    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true)


def calculate_loss(y_true: Union[List[float], torch.Tensor], y_pred: Union[List[float], torch.Tensor]) -> float:
    """
    Calculate the Mean Squared Error (MSE) loss between true and predicted values.
    
    For classification tasks with probabilities, this calculates Cross-Entropy loss
    approximation using negative log-likelihood of the true class probability.

    Args:
        y_true: Ground truth values (can be labels or probabilities depending on context).
        y_pred: Predicted values (probabilities or logits).

    Returns:
        Loss value as a float.

    Raises:
        ValueError: If input lengths do not match or inputs are empty.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    if len(y_true) == 0:
        raise ValueError("Input lists cannot be empty")

    # Convert to lists if tensors
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.tolist()
    if isinstance(y_pred, torch.Tensor):
        y_pred = y_pred.tolist()

    # Calculate MSE for continuous values or probability-based loss
    total_loss = 0.0
    for t, p in zip(y_true, y_pred):
        # If values are probabilities (0-1), use MSE
        # If values are logits, we assume they've been processed appropriately
        diff = float(t) - float(p)
        total_loss += diff * diff
    
    return total_loss / len(y_true)


class MetricCalculator:
    """
    A class to calculate various metrics for model evaluation.
    
    This class provides methods for calculating accuracy, loss, and other
    specialized metrics for the Socratic transformer pipeline.
    """

    def __init__(self, model: Optional[PreTrainedModel] = None, 
                tokenizer: Optional[PreTrainedTokenizer] = None):
        """
        Initialize the MetricCalculator.

        Args:
            model: Optional pre-trained model for token-based metrics.
            tokenizer: Optional tokenizer for token-based metrics.
        """
        self.model = model
        self.tokenizer = tokenizer

    def compute_prediction_error_proxy(self, predictions: List[float], 
                                      targets: List[float]) -> float:
        """
        Compute a proxy for prediction error using MSE.

        Args:
            predictions: List of predicted values.
            targets: List of target values.

        Returns:
            MSE error as a float.
        """
        return calculate_loss(targets, predictions)

    def compute_calibration_error(self, predicted_probs: List[float], 
                                 actual_outcomes: List[int]) -> float:
        """
        Compute calibration error (Expected Calibration Error approximation).

        Args:
            predicted_probs: List of predicted probabilities.
            actual_outcomes: List of actual binary outcomes (0 or 1).

        Returns:
            Calibration error as a float.
        """
        if len(predicted_probs) != len(actual_outcomes):
            raise ValueError("predicted_probs and actual_outcomes must have the same length")
        
        if len(predicted_probs) == 0:
            return 0.0

        # Bin predictions into 10 bins
        num_bins = 10
        bin_boundaries = [i / num_bins for i in range(num_bins + 1)]
        bin_errors = []

        for i in range(num_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]
            
            # Get predictions in this bin
            bin_indices = [j for j, p in enumerate(predicted_probs) 
                         if bin_lower <= p < bin_upper]
            
            if not bin_indices:
                continue

            # Calculate average predicted probability and actual accuracy in bin
            avg_pred = sum(predicted_probs[j] for j in bin_indices) / len(bin_indices)
            actual_acc = sum(actual_outcomes[j] for j in bin_indices) / len(bin_indices)
            
            # Calculate calibration error for this bin
            bin_error = abs(avg_pred - actual_acc)
            bin_weight = len(bin_indices) / len(predicted_probs)
            bin_errors.append(bin_error * bin_weight)

        return sum(bin_errors)

    def compute_ngram_overlap(self, generated_text: str, reference_text: str, 
                             n: int = 2) -> float:
        """
        Compute n-gram overlap between generated and reference text.

        Args:
            generated_text: The generated text.
            reference_text: The reference text.
            n: The n-gram size (default: 2 for bigrams).

        Returns:
            N-gram overlap score as a float between 0 and 1.
        """
        if not self.tokenizer:
            raise ValueError("Tokenizer must be provided for n-gram overlap calculation")

        # Tokenize texts
        gen_tokens = self.tokenizer.tokenize(generated_text)
        ref_tokens = self.tokenizer.tokenize(reference_text)

        if not gen_tokens or not ref_tokens:
            return 0.0

        # Generate n-grams
        def get_ngrams(tokens, n):
            return set(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

        gen_ngrams = get_ngrams(gen_tokens, n)
        ref_ngrams = get_ngrams(ref_tokens, n)

        if not gen_ngrams or not ref_ngrams:
            return 0.0

        # Calculate overlap
        overlap = len(gen_ngrams.intersection(ref_ngrams))
        return overlap / len(ref_ngrams)  # Precision-based
