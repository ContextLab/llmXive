"""
Metric utility for standard accuracy and loss calculations.

This module provides tools to compute evaluation metrics for the Socratic
Transformers pipeline, including accuracy, loss, and specialized proxy metrics
for dialogue-based selection analysis.
"""

import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


class MetricCalculator:
    """
    A utility class for computing various metrics relevant to the Socratic
    Transformers evaluation pipeline.

    This class handles standard metrics (accuracy, loss) as well as specialized
    metrics for analyzing dialogue-based selection and critique quality.
    """

    def __init__(self, model: Optional[PreTrainedModel] = None,
                 tokenizer: Optional[PreTrainedTokenizer] = None):
        """
        Initialize the MetricCalculator.

        Args:
            model: Optional PreTrainedModel for generating predictions.
            tokenizer: Optional PreTrainedTokenizer for tokenizing inputs.
        """
        self.model = model
        self.tokenizer = tokenizer

    def compute_accuracy(self, predictions: Union[List[int], torch.Tensor],
                         labels: Union[List[int], torch.Tensor]) -> float:
        """
        Compute accuracy between predictions and labels.

        Args:
            predictions: Model predictions (logits or token IDs).
            labels: Ground truth labels.

        Returns:
            Accuracy as a float between 0.0 and 1.0.
        """
        if isinstance(predictions, torch.Tensor):
            if predictions.dim() > 1:
                # If logits, take argmax
                predictions = torch.argmax(predictions, dim=-1)
            predictions = predictions.cpu().tolist()

        if isinstance(labels, torch.Tensor):
            labels = labels.cpu().tolist()

        if len(predictions) != len(labels):
            raise ValueError("Predictions and labels must have the same length")

        correct = sum(1 for p, l in zip(predictions, labels) if p == l)
        total = len(labels)

        return correct / total if total > 0 else 0.0

    def compute_loss(self, model: PreTrainedModel,
                     input_ids: torch.Tensor,
                     labels: torch.Tensor,
                     attention_mask: Optional[torch.Tensor] = None) -> float:
        """
        Compute the loss for a given input batch.

        Args:
            model: The model to use for loss computation.
            input_ids: Input token IDs.
            labels: Target labels for loss computation.
            attention_mask: Optional attention mask.

        Returns:
            The computed loss as a float.
        """
        model.eval()
        with torch.no_grad():
            outputs = model(
                input_ids=input_ids,
                labels=labels,
                attention_mask=attention_mask
            )
            loss = outputs.loss

        if isinstance(loss, torch.Tensor):
            return loss.item()
        return float(loss)

    def compute_prediction_error_proxy(self, generated_text: str,
                                       target_text: str) -> float:
        """
        Compute a proxy for prediction error based on text similarity.

        This is a heuristic metric for evaluating how close the generated
        text is to the target, useful when exact token matching isn't
        sufficient.

        Args:
            generated_text: The model's generated output.
            target_text: The expected target output.

        Returns:
            A float representing the error (lower is better).
            Returns 0.0 if texts match exactly, increases with difference.
        """
        if generated_text.strip() == target_text.strip():
            return 0.0

        # Normalize texts
        gen_tokens = generated_text.lower().split()
        target_tokens = target_text.lower().split()

        if not gen_tokens or not target_tokens:
            return 1.0

        # Simple token-level error rate
        gen_set = set(gen_tokens)
        target_set = set(target_tokens)

        # Jaccard distance as a proxy
        intersection = len(gen_set & target_set)
        union = len(gen_set | target_set)

        if union == 0:
            return 1.0

        jaccard_similarity = intersection / union
        return 1.0 - jaccard_similarity

    def compute_calibration_error(self, predictions: List[float],
                                  outcomes: List[bool],
                                  bins: int = 10) -> float:
        """
        Compute the Expected Calibration Error (ECE).

        This measures how well the predicted probabilities match the
        actual outcomes, which is crucial for evaluating the model's
        self-assessment capabilities in the Socratic framework.

        Args:
            predictions: List of predicted probabilities (0.0 to 1.0).
            outcomes: List of binary outcomes (True/False).
            bins: Number of bins for calibration curve.

        Returns:
            The Expected Calibration Error as a float.
        """
        if len(predictions) != len(outcomes):
            raise ValueError("Predictions and outcomes must have the same length")

        if len(predictions) == 0:
            return 0.0

        # Create bins
        bin_boundaries = [i / bins for i in range(bins + 1)]
        ece = 0.0
        total_samples = len(predictions)

        for i in range(bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]

            # Find samples in this bin
            bin_indices = [
                j for j, p in enumerate(predictions)
                if bin_lower <= p < bin_upper
            ]

            if i == bins - 1:  # Include upper bound for last bin
                bin_indices = [
                    j for j, p in enumerate(predictions)
                    if bin_lower <= p <= bin_upper
                ]

            if not bin_indices:
                continue

            # Calculate average confidence and accuracy in bin
            avg_confidence = sum(predictions[j] for j in bin_indices) / len(bin_indices)
            avg_accuracy = sum(1 for j in bin_indices if outcomes[j]) / len(bin_indices)

            # Add weighted error to ECE
            bin_weight = len(bin_indices) / total_samples
            ece += bin_weight * abs(avg_confidence - avg_accuracy)

        return ece

    def compute_ngram_overlap(self, text1: str, text2: str, n: int = 2) -> float:
        """
        Compute the n-gram overlap between two texts.

        This metric is useful for comparing the similarity of generated
        dialogues or critiques, particularly in ablation studies where
        token count is preserved but semantic content varies.

        Args:
            text1: First text to compare.
            text2: Second text to compare.
            n: Size of n-grams (default 2 for bigrams).

        Returns:
            The Jaccard similarity of n-gram sets (0.0 to 1.0).
        """
        def get_ngrams(text: str, n: int) -> set:
            tokens = text.lower().split()
            if len(tokens) < n:
                return set()
            return set(' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

        ngrams1 = get_ngrams(text1, n)
        ngrams2 = get_ngrams(text2, n)

        if not ngrams1 and not ngrams2:
            return 1.0 if not ngrams1 and not ngrams2 else 0.0

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)

        return intersection / union if union > 0 else 0.0


def compute_prediction_error_proxy(generated_text: str, target_text: str) -> float:
    """
    Standalone function to compute prediction error proxy.

    Args:
        generated_text: The model's generated output.
        target_text: The expected target output.

    Returns:
        A float representing the error (lower is better).
    """
    calculator = MetricCalculator()
    return calculator.compute_prediction_error_proxy(generated_text, target_text)


def compute_calibration_error(predictions: List[float],
                              outcomes: List[bool],
                              bins: int = 10) -> float:
    """
    Standalone function to compute calibration error.

    Args:
        predictions: List of predicted probabilities.
        outcomes: List of binary outcomes.
        bins: Number of bins for calibration curve.

    Returns:
        The Expected Calibration Error.
    """
    calculator = MetricCalculator()
    return calculator.compute_calibration_error(predictions, outcomes, bins)


def compute_ngram_overlap(text1: str, text2: str, n: int = 2) -> float:
    """
    Standalone function to compute n-gram overlap.

    Args:
        text1: First text.
        text2: Second text.
        n: N-gram size.

    Returns:
        Jaccard similarity of n-gram sets.
    """
    calculator = MetricCalculator()
    return calculator.compute_ngram_overlap(text1, text2, n)
