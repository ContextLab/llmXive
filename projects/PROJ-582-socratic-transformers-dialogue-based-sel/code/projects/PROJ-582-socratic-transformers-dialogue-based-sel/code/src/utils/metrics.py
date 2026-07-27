"""
Metrics module for Socratic Transformers project.

Implements prediction error proxy calculations using log-probability normalized
by sequence length, as well as calibration error and n-gram overlap metrics.
"""

import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


def compute_prediction_error_proxy(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    prompt: str,
    response: str,
    device: Optional[torch.device] = None
) -> float:
    """
    Compute the prediction error proxy as negative log-probability normalized by sequence length.

    This metric serves as a proxy for the model's uncertainty or "surprise" at its own
    generated response. Lower values indicate higher confidence (lower error), while
    higher values indicate lower confidence (higher error).

    Args:
        model: The transformer model to use for computing log-probabilities.
        tokenizer: The tokenizer corresponding to the model.
        prompt: The input prompt text.
        response: The generated response text to evaluate.
        device: Optional device to run computation on. If None, uses model's device.

    Returns:
        float: The normalized negative log-probability (prediction error proxy).
               Returns infinity if the response is empty or has zero probability.

    Raises:
        ValueError: If prompt or response is empty after tokenization.
    """
    if device is None:
        device = next(model.parameters()).device

    # Tokenize the full sequence (prompt + response)
    full_text = prompt + response
    encoded = tokenizer(
        full_text,
        return_tensors="pt",
        truncation=True,
        max_length=2048
    ).to(device)

    input_ids = encoded["input_ids"]
    attention_mask = encoded["attention_mask"]

    # Check if we have any tokens to process
    if input_ids.numel() == 0:
        raise ValueError("No tokens generated from input")

    # Get model outputs
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits

    # Shift logits to align with labels (logits[i] predicts token i+1)
    # We want to compute the probability of the response tokens given the prompt
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = input_ids[..., 1:].contiguous()

    # Create a mask for the response portion
    # Find where the response starts in the tokenized sequence
    prompt_encoded = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048).to(device)
    prompt_length = prompt_encoded["input_ids"].size(1)

    # Create a mask that is 1 for response tokens, 0 for prompt tokens
    response_mask = torch.zeros_like(shift_labels, dtype=torch.bool)
    if prompt_length < shift_labels.size(1):
        response_mask[:, prompt_length:] = True

    # Apply attention mask
    effective_mask = response_mask & (attention_mask[:, 1:] == 1)

    # Compute log probabilities
    log_probs = torch.nn.functional.log_softmax(shift_logits, dim=-1)

    # Gather the log probability of the actual tokens
    # log_probs shape: (batch_size, seq_len-1, vocab_size)
    # shift_labels shape: (batch_size, seq_len-1)
    batch_size, seq_len, vocab_size = log_probs.shape
    indices = shift_labels.unsqueeze(-1).expand(-1, -1, vocab_size)
    token_log_probs = torch.gather(log_probs, dim=2, index=indices).squeeze(-1)

    # Sum log probabilities for response tokens only
    response_log_probs = token_log_probs * effective_mask.float()
    total_log_prob = response_log_probs.sum(dim=1)

    # Count number of response tokens
    num_response_tokens = effective_mask.sum(dim=1).float()

    # Avoid division by zero
    num_response_tokens = torch.clamp(num_response_tokens, min=1.0)

    # Normalize by sequence length
    normalized_log_prob = total_log_prob / num_response_tokens

    # Return negative log probability (prediction error proxy)
    # Higher values = higher error = lower confidence
    prediction_error = -normalized_log_prob.item()

    return prediction_error


def compute_calibration_error(
    predicted_probs: List[float],
    actual_correct: List[bool]
) -> float:
    """
    Compute the calibration error between predicted probabilities and actual correctness.

    This measures how well the model's confidence aligns with its actual accuracy.
    A perfectly calibrated model would have a calibration error of 0.

    Args:
        predicted_probs: List of predicted probabilities (0-1) for each prediction.
        actual_correct: List of booleans indicating whether each prediction was correct.

    Returns:
        float: The mean absolute calibration error.

    Raises:
        ValueError: If input lists have different lengths or are empty.
    """
    if len(predicted_probs) != len(actual_correct):
        raise ValueError("predicted_probs and actual_correct must have the same length")

    if len(predicted_probs) == 0:
        raise ValueError("Input lists cannot be empty")

    calibration_errors = []
    for prob, correct in zip(predicted_probs, actual_correct):
        if not (0.0 <= prob <= 1.0):
            raise ValueError(f"Probability {prob} is not in range [0, 1]")

        actual = 1.0 if correct else 0.0
        calibration_errors.append(abs(prob - actual))

    return sum(calibration_errors) / len(calibration_errors)


def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 3
) -> float:
    """
    Compute the n-gram overlap (Jaccard similarity) between two texts.

    This is used to detect degenerate dialogues where the model repeats itself
    or fails to generate novel content.

    Args:
        text1: First text to compare.
        text2: Second text to compare.
        n: The size of n-grams to use (default: 3 for trigrams).

    Returns:
        float: The Jaccard similarity coefficient (0-1), where 1 means identical
               n-gram sets and 0 means no overlap.
    """
    def get_ngrams(text: str, n: int) -> set:
        """Extract n-grams from text."""
        tokens = text.lower().split()
        if len(tokens) < n:
            return set()
        return set(zip(*[tokens[i:] for i in range(n)]))

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2

    return len(intersection) / len(union) if union else 0.0


class MetricCalculator:
    """
    A class to compute and aggregate various metrics for the Socratic Transformers project.

    This class provides a convenient interface for computing multiple metrics
    and storing them for later analysis.
    """

    def __init__(self):
        """Initialize the MetricCalculator with empty metric storage."""
        self.metrics: dict = {}
        self._metric_history: List[dict] = []

    def add_prediction_error(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        prompt: str,
        response: str,
        label: Optional[str] = None
    ) -> float:
        """
        Compute and store the prediction error proxy for a given prompt-response pair.

        Args:
            model: The transformer model to use.
            tokenizer: The corresponding tokenizer.
            prompt: The input prompt.
            response: The generated response.
            label: Optional label for this metric entry.

        Returns:
            float: The computed prediction error proxy.
        """
        error = compute_prediction_error_proxy(model, tokenizer, prompt, response)

        entry = {
            "type": "prediction_error",
            "value": error,
            "prompt_length": len(prompt),
            "response_length": len(response)
        }
        if label:
            entry["label"] = label

        self._metric_history.append(entry)
        self.metrics[f"prediction_error_{len(self.metrics)}"] = error

        return error

    def add_calibration_error(
        self,
        predicted_probs: List[float],
        actual_correct: List[bool],
        label: Optional[str] = None
    ) -> float:
        """
        Compute and store the calibration error.

        Args:
            predicted_probs: List of predicted probabilities.
            actual_correct: List of actual correctness booleans.
            label: Optional label for this metric entry.

        Returns:
            float: The computed calibration error.
        """
        error = compute_calibration_error(predicted_probs, actual_correct)

        entry = {
            "type": "calibration_error",
            "value": error,
            "num_samples": len(predicted_probs)
        }
        if label:
            entry["label"] = label

        self._metric_history.append(entry)
        self.metrics[f"calibration_error_{len(self.metrics)}"] = error

        return error

    def add_ngram_overlap(
        self,
        text1: str,
        text2: str,
        n: int = 3,
        label: Optional[str] = None
    ) -> float:
        """
        Compute and store the n-gram overlap between two texts.

        Args:
            text1: First text.
            text2: Second text.
            n: N-gram size.
            label: Optional label for this metric entry.

        Returns:
            float: The computed n-gram overlap.
        """
        overlap = compute_ngram_overlap(text1, text2, n)

        entry = {
            "type": "ngram_overlap",
            "value": overlap,
            "n": n,
            "text1_length": len(text1),
            "text2_length": len(text2)
        }
        if label:
            entry["label"] = label

        self._metric_history.append(entry)
        self.metrics[f"ngram_overlap_{len(self.metrics)}"] = overlap

        return overlap

    def get_summary(self) -> dict:
        """
        Get a summary of all computed metrics.

        Returns:
            dict: A dictionary containing summary statistics for each metric type.
        """
        summary = {}
        for metric_type in ["prediction_error", "calibration_error", "ngram_overlap"]:
            values = [
                entry["value"] for entry in self._metric_history
                if entry["type"] == metric_type
            ]
            if values:
                summary[metric_type] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        return summary

    def get_history(self) -> List[dict]:
        """
        Get the full history of metric computations.

        Returns:
            List[dict]: List of all metric entries in chronological order.
        """
        return self._metric_history.copy()