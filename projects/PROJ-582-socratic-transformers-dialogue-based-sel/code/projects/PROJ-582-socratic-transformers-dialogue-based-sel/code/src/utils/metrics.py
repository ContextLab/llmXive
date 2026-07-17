"""
Metrics module for Socratic Transformers.

Implements prediction error proxy calculations using log-probability normalized
by sequence length, calibration error, and n-gram overlap detection.
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
    use_attention_mask: bool = True
) -> float:
    """
    Compute the prediction error proxy for a given question-answer pair.

    The proxy is defined as the negative log-likelihood of the answer tokens
    given the question context, normalized by the number of tokens in the answer.
    This serves as a measure of the model's "surprise" or uncertainty about the answer.

    Args:
        model: The transformer model to use for computing probabilities.
        tokenizer: The tokenizer corresponding to the model.
        question: The question string (context).
        answer: The answer string (target sequence).
        use_attention_mask: Whether to use attention masks in computation.

    Returns:
        float: The normalized negative log-likelihood (prediction error proxy).
               Higher values indicate higher uncertainty/error.

    Raises:
        ValueError: If the answer tokenizes to an empty sequence.
    """
    # Tokenize the combined input
    full_text = f"{question} {answer}"
    inputs = tokenizer(
        full_text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=1024
    )

    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"] if use_attention_mask else None

    # Ensure we have the answer token IDs
    # We need to compute log-probs for the answer part specifically
    # The answer starts after the question tokens
    question_tokens = tokenizer(question, return_tensors="pt", add_special_tokens=False)["input_ids"]
    question_len = question_tokens.shape[1]
    answer_len = input_ids.shape[1] - question_len

    if answer_len <= 0:
        raise ValueError("Answer tokenized to empty sequence or answer is before question.")

    # Get model outputs (logits)
    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=input_ids
        )
        # loss is the mean cross-entropy over the sequence
        # We want the sum of log probs for the answer tokens
        # The loss is -mean(log_probs) over the sequence
        # So sum of log_probs = -loss * total_tokens
        # But we need to be careful: loss is computed over the whole sequence including question
        # We need to manually compute log probs for answer tokens

        logits = outputs.logits  # (batch, seq_len, vocab)

    # Shift logits and labels to compute next-token prediction
    # logits[i] predicts token[i+1]
    # So for answer tokens (indices question_len to end), we look at logits[question_len-1 to end-1]
    # But we need to mask out the question part for the loss calculation

    # Create a mask for the answer part
    answer_mask = torch.zeros_like(input_ids, dtype=torch.bool)
    answer_mask[:, question_len:] = True

    # Shift labels: we want to predict answer[i] given input up to answer[i-1]
    # So we shift input_ids left by 1
    shifted_labels = input_ids.clone()
    shifted_labels[:, :-1] = input_ids[:, 1:]
    shifted_labels[:, -1] = -100  # Ignore last token

    # Compute log probabilities
    # Apply softmax to get probs, then log
    # To avoid numerical issues, we use log_softmax
    log_probs = torch.nn.functional.log_softmax(logits, dim=-1)

    # Gather log probs for the actual tokens
    # log_probs[batch, token_idx, vocab] -> we want log_probs[batch, token_idx, actual_token]
    # Use gather: log_probs.gather(2, labels.unsqueeze(-1)).squeeze(-1)
    token_log_probs = log_probs.gather(2, input_ids.unsqueeze(-1)).squeeze(-1)

    # We only care about the answer part
    # The answer tokens are at positions question_len to end
    # But the prediction for answer[i] comes from logits[i-1]
    # So for answer tokens starting at index question_len, we look at token_log_probs at indices question_len-1 to end-1

    answer_start_idx = question_len
    answer_end_idx = input_ids.shape[1]

    if answer_start_idx >= answer_end_idx:
        raise ValueError("Answer start index is beyond the sequence length.")

    # Extract log probs for the answer tokens
    # We want the log prob of predicting token[i] given previous tokens
    # So for answer tokens at indices [answer_start_idx, answer_end_idx),
    # we look at token_log_probs at indices [answer_start_idx - 1, answer_end_idx - 1)
    answer_log_probs = token_log_probs[:, answer_start_idx - 1:answer_end_idx - 1]

    # Mask out any padding tokens if present
    if use_attention_mask:
        # The attention mask for the answer part
        answer_attention_mask = attention_mask[:, answer_start_idx - 1:answer_end_idx - 1]
        # Set log probs to 0 where mask is 0 (padding)
        answer_log_probs = answer_log_probs * answer_attention_mask.float()

    # Sum the log probs for the answer
    total_log_prob = answer_log_probs.sum(dim=1)

    # Normalize by the number of answer tokens (excluding padding)
    if use_attention_mask:
        num_tokens = answer_attention_mask.sum(dim=1).float()
    else:
        num_tokens = torch.tensor([answer_len], dtype=torch.float)

    # Avoid division by zero
    num_tokens = torch.clamp(num_tokens, min=1.0)

    # Normalized negative log-likelihood
    nll = -total_log_prob / num_tokens

    return nll.item()


def compute_calibration_error(
    predicted_probs: List[float],
    actual_outcomes: List[bool]
) -> float:
    """
    Compute the calibration error (Expected Calibration Error - ECE).

    This measures the difference between predicted probabilities and actual
    outcomes, binned into intervals.

    Args:
        predicted_probs: List of predicted probabilities (0.0 to 1.0).
        actual_outcomes: List of boolean outcomes (True for correct, False for incorrect).

    Returns:
        float: The Expected Calibration Error (ECE).
    """
    if len(predicted_probs) != len(actual_outcomes):
        raise ValueError("predicted_probs and actual_outcomes must have the same length.")

    if len(predicted_probs) == 0:
        return 0.0

    n_bins = 10
    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]

    ece = 0.0
    total_samples = len(predicted_probs)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # Find samples in this bin
        in_bin = [
            j for j, prob in enumerate(predicted_probs)
            if bin_lower <= prob < bin_upper
        ]

        if i == n_bins - 1:
            # Include the upper boundary for the last bin
            in_bin = [
                j for j, prob in enumerate(predicted_probs)
                if bin_lower <= prob <= bin_upper
            ]

        if len(in_bin) == 0:
            continue

        # Compute average confidence and accuracy in the bin
        avg_confidence = sum(predicted_probs[j] for j in in_bin) / len(in_bin)
        avg_accuracy = sum(1.0 if actual_outcomes[j] else 0.0 for j in in_bin) / len(in_bin)

        # Weight by the number of samples in the bin
        ece += (len(in_bin) / total_samples) * abs(avg_confidence - avg_accuracy)

    return ece


def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 3
) -> float:
    """
    Compute the n-gram overlap (Jaccard similarity) between two texts.

    Args:
        text1: First text string.
        text2: Second text string.
        n: Size of n-grams (default 3 for trigrams).

    Returns:
        float: Jaccard similarity coefficient (0.0 to 1.0).
    """
    def get_ngrams(text, n):
        words = text.lower().split()
        if len(words) < n:
            return set()
        return set(tuple(words[i:i+n]) for i in range(len(words) - n + 1))

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    if not ngrams1 and not ngrams2:
        return 1.0  # Both empty, consider identical

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = ngrams1.intersection(ngrams2)
    union = ngrams1.union(ngrams2)

    return len(intersection) / len(union)


class MetricCalculator:
    """
    A utility class for computing various metrics on model predictions.
    """

    def __init__(
        self,
        model: Optional[PreTrainedModel] = None,
        tokenizer: Optional[PreTrainedTokenizer] = None
    ):
        """
        Initialize the MetricCalculator.

        Args:
            model: Optional transformer model for prediction error proxy.
            tokenizer: Optional tokenizer for prediction error proxy.
        """
        self.model = model
        self.tokenizer = tokenizer

    def set_model(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer
    ) -> None:
        """
        Set the model and tokenizer for prediction error proxy computation.

        Args:
            model: The transformer model.
            tokenizer: The corresponding tokenizer.
        """
        self.model = model
        self.tokenizer = tokenizer

    def compute_error_proxy(
        self,
        question: str,
        answer: str
    ) -> float:
        """
        Compute the prediction error proxy for a question-answer pair.

        Args:
            question: The question string.
            answer: The answer string.

        Returns:
            float: The prediction error proxy.

        Raises:
            RuntimeError: If model or tokenizer is not set.
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model and tokenizer must be set before computing error proxy.")

        return compute_prediction_error_proxy(self.model, self.tokenizer, question, answer)

    def compute_calibration(
        self,
        predicted_probs: List[float],
        actual_outcomes: List[bool]
    ) -> float:
        """
        Compute the calibration error.

        Args:
            predicted_probs: List of predicted probabilities.
            actual_outcomes: List of actual outcomes.

        Returns:
            float: The calibration error.
        """
        return compute_calibration_error(predicted_probs, actual_outcomes)

    def compute_overlap(
        self,
        text1: str,
        text2: str,
        n: int = 3
    ) -> float:
        """
        Compute the n-gram overlap between two texts.

        Args:
            text1: First text.
            text2: Second text.
            n: N-gram size.

        Returns:
            float: The Jaccard similarity.
        """
        return compute_ngram_overlap(text1, text2, n)
