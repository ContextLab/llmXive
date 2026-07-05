"""
Prediction error proxy calculator for Socratic Transformers.

Implements log-probability normalized by sequence length as the primary
uncertainty metric, aligned with the assumptions for self-teaching signals.
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
    device: Optional[torch.device] = None,
) -> float:
    """
    Compute the prediction error proxy for a given (prompt, response) pair.

    The proxy is defined as the negative log-likelihood of the response
    tokens conditioned on the prompt, normalized by the sequence length
    (number of tokens in the response). This provides a per-token uncertainty
    measure that is comparable across responses of different lengths.

    Args:
        model: The transformer model used for computing log-probabilities.
        tokenizer: The tokenizer for encoding text.
        prompt: The input prompt text.
        response: The model-generated response text.
        device: Optional device to move model and inputs to. If None, the model's
                current device is used.

    Returns:
        float: The normalized negative log-likelihood (higher = more uncertain/error).
               Returns infinity if the response cannot be tokenized or has zero length.

    Raises:
        ValueError: If the response tokens are not a suffix of the prompt+response
                    sequence (indicating tokenization mismatch).
    """
    if device is None:
        device = model.device

    # Encode the full sequence
    full_text = prompt + response
    encoded = tokenizer(
        full_text,
        return_tensors="pt",
        truncation=False,
        add_special_tokens=False,
    )

    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)

    # Tokenize prompt and response separately to identify response token IDs
    prompt_encoded = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=False,
        add_special_tokens=False,
    )
    prompt_len = prompt_encoded["input_ids"].shape[1]

    response_encoded = tokenizer(
        response,
        return_tensors="pt",
        truncation=False,
        add_special_tokens=False,
    )
    response_ids = response_encoded["input_ids"].to(device)
    response_len = response_ids.shape[1]

    # Validate that response tokens match the suffix of the full sequence
    full_response_tokens = input_ids[0, prompt_len:]
    if not torch.equal(full_response_tokens, response_ids[0]):
        raise ValueError(
            "Tokenization mismatch: response tokens do not match the suffix "
            "of the prompt+response sequence. This may be due to tokenizer "
            "differences or whitespace handling."
        )

    if response_len == 0:
        return float("inf")

    # Compute log probabilities for the response tokens
    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        logits = outputs.logits  # Shape: (batch, seq_len, vocab_size)

    # Extract logits for response tokens: for each position i in response,
    # we want the log-prob of token at position prompt_len + i given prefix up to prompt_len + i - 1
    response_logits = logits[0, prompt_len - 1 : prompt_len + response_len - 1]
    response_targets = response_ids[0]

    # Compute log probabilities
    log_probs = torch.nn.functional.log_softmax(response_logits, dim=-1)
    # Select the log-prob for the actual target token at each position
    chosen_log_probs = log_probs.gather(1, response_targets.unsqueeze(1)).squeeze(1)

    # Sum log probabilities and normalize by length
    total_log_prob = chosen_log_probs.sum()
    normalized_error = -total_log_prob / response_len

    return normalized_error.item()


def compute_calibration_error(
    predicted_probs: List[float],
    actual_correct: List[bool],
    bins: int = 10,
) -> float:
    """
    Compute the Expected Calibration Error (ECE) for a set of predictions.

    This metric measures the discrepancy between predicted confidence and
    actual accuracy, addressing the over-confidence bias highlighted by
    Daniel Kahneman's reviews on System 1 vs System 2 reasoning.

    Args:
        predicted_probs: List of predicted probabilities (confidence scores) for each prediction.
        actual_correct: List of booleans indicating whether each prediction was correct.
        bins: Number of bins for calibration curve.

    Returns:
        float: The Expected Calibration Error (lower = better calibrated).
    """
    if len(predicted_probs) != len(actual_correct):
        raise ValueError("predicted_probs and actual_correct must have the same length")

    if len(predicted_probs) == 0:
        return 0.0

    # Convert to tensors for easier computation
    probs = torch.tensor(predicted_probs)
    correct = torch.tensor(actual_correct, dtype=torch.float32)

    # Create bin edges
    bin_edges = torch.linspace(0, 1, bins + 1)
    ece = 0.0
    total_samples = len(probs)

    for i in range(bins):
        lower, upper = bin_edges[i], bin_edges[i + 1]
        mask = (probs >= lower) & (probs < upper)
        if i == bins - 1:  # Include upper bound for last bin
            mask = (probs >= lower) & (probs <= upper)

        bin_count = mask.sum().item()
        if bin_count == 0:
            continue

        bin_accuracy = correct[mask].mean().item()
        bin_confidence = probs[mask].mean().item()

        ece += (bin_count / total_samples) * abs(bin_accuracy - bin_confidence)

    return ece


def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 2,
) -> float:
    """
    Compute the n-gram overlap ratio between two texts.

    Used to detect degenerate dialogues where the model repeats itself
    or fails to generate novel content (threshold > 0.9 triggers truncation).

    Args:
        text1: First text string.
        text2: Second text string.
        n: N-gram size (default 2 for bigrams).

    Returns:
        float: Jaccard similarity coefficient of n-gram sets (0.0 to 1.0).
    """
    def get_ngrams(text: str, n: int) -> set:
        words = text.lower().split()
        return {
            " ".join(words[i : i + n])
            for i in range(len(words) - n + 1)
        }

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    if not ngrams1 and not ngrams2:
        return 1.0
    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2

    return len(intersection) / len(union)


class MetricCalculator:
    """
    A utility class for computing various metrics required by the Socratic
    dialogue system, including prediction error proxies and calibration metrics.
    """

    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, device: Optional[torch.device] = None):
        """
        Initialize the metric calculator with a model and tokenizer.

        Args:
            model: The transformer model.
            tokenizer: The tokenizer.
            device: Optional device for computation.
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device or model.device

    def compute_error_proxy(self, prompt: str, response: str) -> float:
        """
        Compute the prediction error proxy for a (prompt, response) pair.

        Args:
            prompt: Input prompt text.
            response: Generated response text.

        Returns:
            float: Normalized negative log-likelihood.
        """
        return compute_prediction_error_proxy(
            self.model, self.tokenizer, prompt, response, self.device
        )

    def compute_calibration_error(
        self,
        predicted_probs: List[float],
        actual_correct: List[bool],
        bins: int = 10,
    ) -> float:
        """
        Compute the Expected Calibration Error.

        Args:
            predicted_probs: List of confidence scores.
            actual_correct: List of correctness booleans.
            bins: Number of bins.

        Returns:
            float: Expected Calibration Error.
        """
        return compute_calibration_error(predicted_probs, actual_correct, bins)

    def compute_ngram_overlap(self, text1: str, text2: str, n: int = 2) -> float:
        """
        Compute n-gram overlap between two texts.

        Args:
            text1: First text.
            text2: Second text.
            n: N-gram size.

        Returns:
            float: Jaccard similarity.
        """
        return compute_ngram_overlap(text1, text2, n)
