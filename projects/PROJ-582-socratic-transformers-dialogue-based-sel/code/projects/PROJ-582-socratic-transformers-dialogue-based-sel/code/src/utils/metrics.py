"""
Metrics module for Socratic Transformers project.

Implements prediction error proxies, calibration error, and n-gram overlap
calculations as defined in the project assumptions.
"""
import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


def compute_prediction_error_proxy(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    question: str,
    answer: str,
    max_length: int = 512,
    device: Optional[str] = None
) -> float:
    """
    Compute the prediction error proxy using log-probability normalized by sequence length.

    This metric serves as a proxy for model uncertainty/confidence on a given
    question-answer pair. Lower values indicate higher confidence (lower error).

    Args:
        model: The transformer model to use for prediction.
        tokenizer: The tokenizer corresponding to the model.
        question: The input question string.
        answer: The target answer string.
        max_length: Maximum sequence length for tokenization.
        device: Device to run inference on (e.g., 'cpu', 'cuda'). If None, uses model's device.

    Returns:
        float: The normalized negative log-likelihood (prediction error proxy).

    Raises:
        ValueError: If the input strings are empty or tokenization fails.
    """
    if not question or not answer:
        raise ValueError("Question and answer strings cannot be empty")

    if device is None:
        device = model.device

    # Construct the input sequence: "Question: {question} Answer: {answer}"
    input_text = f"Question: {question} Answer: {answer}"

    # Tokenize
    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        max_length=max_length,
        truncation=True,
        padding=True
    )

    # Move inputs to device
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs["attention_mask"].to(device)

    # Ensure we have at least one token to compute loss on
    if input_ids.numel() == 0:
        raise ValueError("Tokenization resulted in empty input")

    # Forward pass to get logits
    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True
        )
        logits = outputs.logits

    # Shift logits and labels for next-token prediction
    # logits shape: (batch_size, seq_len, vocab_size)
    # We want to compute the probability of each token given the previous ones
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = input_ids[..., 1:].contiguous()

    # Create a mask for valid positions (excluding padding)
    shift_attention_mask = attention_mask[..., 1:].contiguous()

    # Flatten for loss computation
    flat_logits = shift_logits.view(-1, shift_logits.size(-1))
    flat_labels = shift_labels.view(-1)
    flat_mask = shift_attention_mask.view(-1)

    # Compute log probabilities
    log_probs = torch.nn.functional.log_softmax(flat_logits, dim=-1)

    # Gather the log probability of the actual labels
    # Use gather to select the log prob of the correct token for each position
    nll = -log_probs.gather(dim=1, index=flat_labels.unsqueeze(1)).squeeze(1)

    # Apply mask to ignore padding tokens
    masked_nll = nll * flat_mask.float()
    total_nll = masked_nll.sum()
    valid_token_count = flat_mask.sum()

    if valid_token_count == 0:
        raise ValueError("No valid tokens to compute loss on")

    # Normalize by sequence length (number of valid tokens)
    normalized_nll = total_nll / valid_token_count

    return normalized_nll.item()


def compute_calibration_error(
    predicted_probs: List[float],
    actual_correct: List[bool]
) -> float:
    """
    Compute the calibration error (Expected Calibration Error approximation).

    This measures how well the predicted probabilities match the actual
    correctness rates.

    Args:
        predicted_probs: List of predicted probabilities (0.0 to 1.0).
        actual_correct: List of booleans indicating actual correctness.

    Returns:
        float: The mean absolute calibration error.

    Raises:
        ValueError: If input lists have different lengths or invalid values.
    """
    if len(predicted_probs) != len(actual_correct):
        raise ValueError("predicted_probs and actual_correct must have the same length")

    if len(predicted_probs) == 0:
        return 0.0

    # Validate inputs
    for p in predicted_probs:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"Probability must be between 0 and 1, got {p}")

    for c in actual_correct:
        if not isinstance(c, bool):
            raise ValueError(f"actual_correct must contain booleans, got {type(c)}")

    # Compute calibration error
    total_error = 0.0
    for prob, correct in zip(predicted_probs, actual_correct):
        actual_value = 1.0 if correct else 0.0
        total_error += abs(prob - actual_value)

    return total_error / len(predicted_probs)


def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 2
) -> float:
    """
    Compute the n-gram overlap (Jaccard similarity) between two texts.

    This is used to detect degenerate dialogues where the model repeats
    itself or produces highly similar content.

    Args:
        text1: First text string.
        text2: Second text string.
        n: N-gram size (default 2 for bigrams).

    Returns:
        float: Jaccard similarity score between 0.0 and 1.0.

    Raises:
        ValueError: If n < 1 or if texts are empty.
    """
    if n < 1:
        raise ValueError("N-gram size must be at least 1")

    if not text1 or not text2:
        return 0.0

    def get_ngrams(text: str, n: int) -> set:
        """Extract n-grams from text."""
        words = text.lower().split()
        if len(words) < n:
            # For short texts, return character n-grams as fallback
            return set(text.lower()[i:i+n] for i in range(len(text) - n + 1))
        return set(" ".join(words[i:i+n]) for i in range(len(words) - n + 1))

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    if not ngrams1 and not ngrams2:
        return 0.0

    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2

    return len(intersection) / len(union) if union else 0.0


class MetricCalculator:
    """
    A utility class for computing various metrics on model outputs.

    This class provides a convenient interface for batch computation of
    prediction error proxies and other metrics.
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        device: Optional[str] = None,
        max_length: int = 512
    ):
        """
        Initialize the MetricCalculator.

        Args:
            model: The transformer model to use.
            tokenizer: The corresponding tokenizer.
            device: Device for inference (e.g., 'cpu', 'cuda').
            max_length: Maximum sequence length for tokenization.
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device or model.device
        self.max_length = max_length

    def compute_error_proxy_batch(
        self,
        questions: List[str],
        answers: List[str]
    ) -> List[float]:
        """
        Compute prediction error proxies for a batch of question-answer pairs.

        Args:
            questions: List of question strings.
            answers: List of answer strings.

        Returns:
            List[float]: Prediction error proxy for each pair.

        Raises:
            ValueError: If input lists have different lengths.
        """
        if len(questions) != len(answers):
            raise ValueError("Questions and answers must have the same length")

        results = []
        for q, a in zip(questions, answers):
            error = compute_prediction_error_proxy(
                self.model,
                self.tokenizer,
                q,
                a,
                max_length=self.max_length,
                device=self.device
            )
            results.append(error)

        return results

    def compute_calibration_batch(
        self,
        predicted_probs: List[float],
        actual_correct: List[bool]
    ) -> float:
        """
        Compute calibration error for a batch of predictions.

        Args:
            predicted_probs: List of predicted probabilities.
            actual_correct: List of actual correctness booleans.

        Returns:
            float: Calibration error.
        """
        return compute_calibration_error(predicted_probs, actual_correct)

    def compute_ngram_overlap_batch(
        self,
        text_pairs: List[Tuple[str, str]],
        n: int = 2
    ) -> List[float]:
        """
        Compute n-gram overlap for a batch of text pairs.

        Args:
            text_pairs: List of (text1, text2) tuples.
            n: N-gram size.

        Returns:
            List[float]: N-gram overlap score for each pair.
        """
        results = []
        for t1, t2 in text_pairs:
            overlap = compute_ngram_overlap(t1, t2, n)
            results.append(overlap)

        return results