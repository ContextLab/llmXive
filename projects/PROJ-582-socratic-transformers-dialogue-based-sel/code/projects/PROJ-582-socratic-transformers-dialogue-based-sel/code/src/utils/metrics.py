"""
Metric utilities for the Socratic Transformers pipeline.

Provides functions to compute standard accuracy, loss, and proxy metrics
for evaluating model performance on reasoning tasks.
"""

import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


def compute_prediction_error_proxy(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    questions: List[str],
    ground_truth_answers: List[str],
    max_length: int = 512,
) -> List[float]:
    """
    Computes a proxy for prediction error based on log-probability of the ground truth.

    This metric serves as a proxy for "surprise" or "error" without explicit
    symbolic evaluation, aligning with the need to measure system confidence.

    Args:
        model: The transformer model.
        tokenizer: The associated tokenizer.
        questions: List of input questions/prompts.
        ground_truth_answers: List of expected answers (ground truth).
        max_length: Maximum sequence length for tokenization.

    Returns:
        A list of float values representing the negative log-likelihood (NLL)
        for each sample. Lower values indicate higher confidence/correctness.
    """
    if len(questions) != len(ground_truth_answers):
        raise ValueError("Questions and ground_truth_answers must have the same length.")

    model.eval()
    nll_scores = []

    with torch.no_grad():
        for question, answer in zip(questions, ground_truth_answers):
            # Construct input: question + answer to calculate probability of answer given question
            full_text = f"{question} {answer}"
            inputs = tokenizer(
                full_text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
            )

            # Shift labels to compute loss on the answer part only
            # We assume the answer starts after the question tokens.
            # A simpler proxy is to compute the loss on the entire sequence
            # or specifically the answer tokens if we can identify them.
            # For this proxy, we compute the average negative log probability
            # of the tokens corresponding to the answer.

            input_ids = inputs["input_ids"]
            attention_mask = inputs["attention_mask"]

            # Run model
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits

            # Shift logits and labels for next-token prediction loss
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = input_ids[..., 1:].contiguous()

            # Create a mask for the answer part
            # Find the start index of the answer in the tokenized sequence
            # This is a heuristic: assume the answer tokens are the last N tokens
            # corresponding to the answer string.
            # A more robust way: tokenize answer separately and match.
            answer_tokens = tokenizer(answer, return_tensors="pt", truncation=True, max_length=max_length)["input_ids"][0]
            
            # Simple heuristic: the answer tokens are the suffix of the input_ids
            # corresponding to the length of answer_tokens.
            # This assumes the tokenizer didn't add special tokens that shift things unexpectedly
            # or that we are consistent.
            start_idx = len(input_ids[0]) - len(answer_tokens)
            
            # Extract relevant logits and labels
            relevant_logits = shift_logits[0, start_idx : start_idx + len(answer_tokens)]
            relevant_labels = shift_labels[0, start_idx : start_idx + len(answer_tokens)]

            # Calculate log probs
            log_probs = torch.nn.functional.log_softmax(relevant_logits, dim=-1)
            # Gather log probs for the correct tokens
            chosen_log_probs = log_probs.gather(1, relevant_labels.unsqueeze(-1)).squeeze(-1)

            # Average negative log likelihood
            avg_nll = -chosen_log_probs.mean().item()
            nll_scores.append(avg_nll)

    return nll_scores


def compute_calibration_error(
    predicted_probs: List[float],
    binary_outcomes: List[int],
    n_bins: int = 10,
) -> Tuple[float, float, float]:
    """
    Computes Expected Calibration Error (ECE), Max Calibration Error (MCE),
    and Average Calibration Error (ACE).

    Args:
        predicted_probs: List of predicted probabilities (0.0 to 1.0).
        binary_outcomes: List of binary outcomes (0 or 1).
        n_bins: Number of bins for calibration curve.

    Returns:
        Tuple of (ECE, MCE, ACE).
    """
    if len(predicted_probs) != len(binary_outcomes):
        raise ValueError("predicted_probs and binary_outcomes must have the same length.")

    if n_bins <= 0:
        raise ValueError("n_bins must be positive.")

    bin_boundaries = torch.linspace(0, 1, n_bins + 1)
    ece = 0.0
    mce = 0.0
    ace = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # Find samples in this bin
        in_bin = (torch.tensor(predicted_probs) >= bin_lower) & (torch.tensor(predicted_probs) < bin_upper)
        # Handle the last bin to include the upper boundary
        if i == n_bins - 1:
            in_bin = (torch.tensor(predicted_probs) >= bin_lower) & (torch.tensor(predicted_probs) <= bin_upper)

        prop_in_bin = in_bin.float().mean().item()

        if prop_in_bin > 0:
            # Average confidence in this bin
            avg_confidence = torch.tensor(predicted_probs)[in_bin].mean().item()
            # Average accuracy in this bin
            avg_accuracy = torch.tensor(binary_outcomes)[in_bin].mean().item()

            # Calibration error for this bin
            calibration_error = abs(avg_confidence - avg_accuracy)

            ece += prop_in_bin * calibration_error
            mce = max(mce, calibration_error)
            ace += calibration_error

    ace = ace / n_bins if n_bins > 0 else 0.0

    return ece, mce, ace


def compute_ngram_overlap(
    generated_text: str,
    reference_text: str,
    n: int = 4,
) -> float:
    """
    Computes the n-gram overlap (precision) between generated and reference text.

    Args:
        generated_text: The model's generated text.
        reference_text: The ground truth reference text.
        n: The n-gram size.

    Returns:
        The precision of n-gram overlap (0.0 to 1.0).
    """
    def get_ngrams(text, n):
        words = text.lower().split()
        if len(words) < n:
            return set()
        return set(tuple(words[i:i + n]) for i in range(len(words) - n + 1))

    gen_ngrams = get_ngrams(generated_text, n)
    ref_ngrams = get_ngrams(reference_text, n)

    if not gen_ngrams:
        return 0.0

    overlap = len(gen_ngrams & ref_ngrams)
    return overlap / len(gen_ngrams)


class MetricCalculator:
    """
    A utility class to compute various metrics for the Socratic pipeline.
    """

    def __init__(self, model: Optional[PreTrainedModel] = None, tokenizer: Optional[PreTrainedTokenizer] = None):
        """
        Initialize the MetricCalculator.

        Args:
            model: Optional model for prediction-based metrics.
            tokenizer: Optional tokenizer for prediction-based metrics.
        """
        self.model = model
        self.tokenizer = tokenizer

    def compute_error_proxy(
        self,
        questions: List[str],
        ground_truth_answers: List[str],
        max_length: int = 512,
    ) -> List[float]:
        """
        Compute prediction error proxy using the initialized model and tokenizer.
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model and tokenizer must be initialized to compute error proxy.")
        return compute_prediction_error_proxy(self.model, self.tokenizer, questions, ground_truth_answers, max_length)

    def compute_calibration(
        self,
        predicted_probs: List[float],
        binary_outcomes: List[int],
        n_bins: int = 10,
    ) -> Tuple[float, float, float]:
        """
        Compute calibration metrics.
        """
        return compute_calibration_error(predicted_probs, binary_outcomes, n_bins)

    def compute_ngram(
        self,
        generated_text: str,
        reference_text: str,
        n: int = 4,
    ) -> float:
        """
        Compute n-gram overlap.
        """
        return compute_ngram_overlap(generated_text, reference_text, n)

    def compute_accuracy(
        self,
        predicted_labels: List[int],
        ground_truth_labels: List[int],
    ) -> float:
        """
        Compute standard accuracy.

        Args:
            predicted_labels: List of predicted class labels (0 or 1).
            ground_truth_labels: List of ground truth class labels (0 or 1).

        Returns:
            Accuracy score (0.0 to 1.0).
        """
        if len(predicted_labels) != len(ground_truth_labels):
            raise ValueError("predicted_labels and ground_truth_labels must have the same length.")
        
        if not predicted_labels:
            return 0.0

        correct = sum(p == g for p, g in zip(predicted_labels, ground_truth_labels))
        return correct / len(predicted_labels)

    def compute_loss(
        self,
        losses: List[float],
    ) -> float:
        """
        Compute average loss.

        Args:
            losses: List of loss values.

        Returns:
            Average loss.
        """
        if not losses:
            return 0.0
        return sum(losses) / len(losses)
