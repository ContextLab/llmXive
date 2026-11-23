"""
Metric utility for standard accuracy and loss calculations.
Implements evaluation metrics for the Socratic Transformers pipeline.
"""

import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


class MetricCalculator:
    """
    Calculator for various evaluation metrics including accuracy, loss,
    and specialized metrics for the Socratic dialogue evaluation.
    """

    def __init__(
        self,
        model: Optional[PreTrainedModel] = None,
        tokenizer: Optional[PreTrainedTokenizer] = None
    ):
        """
        Initialize the MetricCalculator.

        Args:
            model: The transformer model for generating predictions or computing loss.
            tokenizer: The tokenizer for processing text inputs.
        """
        self.model = model
        self.tokenizer = tokenizer

    def compute_accuracy(
        self,
        predictions: Union[List[int], torch.Tensor],
        labels: Union[List[int], torch.Tensor]
    ) -> float:
        """
        Compute standard token-level accuracy.

        Args:
            predictions: Model predictions (logits or token IDs).
            labels: Ground truth token IDs.

        Returns:
            Accuracy as a float between 0 and 1.
        """
        if isinstance(predictions, torch.Tensor):
            if predictions.dim() > 1:
                # If logits, take argmax
                pred_ids = predictions.argmax(dim=-1)
            else:
                pred_ids = predictions
        else:
            pred_ids = torch.tensor(predictions)

        if isinstance(labels, torch.Tensor):
            label_ids = labels
        else:
            label_ids = torch.tensor(labels)

        # Align lengths
        min_len = min(len(pred_ids), len(label_ids))
        pred_ids = pred_ids[:min_len]
        label_ids = label_ids[:min_len]

        correct = (pred_ids == label_ids).sum().item()
        total = min_len

        if total == 0:
            return 0.0

        return correct / total

    def compute_loss(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: Optional[torch.Tensor] = None
    ) -> float:
        """
        Compute model loss (cross-entropy) for a batch.

        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.
            labels: Optional labels for loss computation. If None, uses input_ids shifted.

        Returns:
            Loss value as a float.
        """
        if self.model is None:
            raise ValueError("Model must be provided to compute loss.")

        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss

        return loss.item()

    def compute_perplexity(self, loss: float) -> float:
        """
        Compute perplexity from loss.

        Args:
            loss: Cross-entropy loss value.

        Returns:
            Perplexity (exp(loss)).
        """
        return math.exp(loss)

    def compute_exact_match(
        self,
        predictions: List[str],
        references: List[str]
    ) -> float:
        """
        Compute exact match accuracy for string outputs.

        Args:
            predictions: List of predicted strings.
            references: List of reference strings.

        Returns:
            Exact match ratio.
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length.")

        if len(predictions) == 0:
            return 0.0

        matches = sum(1 for p, r in zip(predictions, references) if p.strip() == r.strip())
        return matches / len(predictions)

def compute_prediction_error_proxy(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    question: str,
    expected_answer: str
) -> float:
    """
    Compute a proxy for prediction error by comparing model output to expected answer.

    This function generates an answer from the model and computes a simple
    error metric based on token overlap and length difference.

    Args:
        model: The transformer model.
        tokenizer: The tokenizer.
        question: The input question.
        expected_answer: The expected answer string.

    Returns:
        A proxy error score (lower is better).
    """
    inputs = tokenizer(question, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode the generated answer
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Simple error proxy: 1 - (overlap / max_length)
    gen_tokens = set(generated_text.split())
    exp_tokens = set(expected_answer.split())

    if len(gen_tokens) == 0 or len(exp_tokens) == 0:
        return 1.0

    overlap = len(gen_tokens.intersection(exp_tokens))
    max_tokens = max(len(gen_tokens), len(exp_tokens))

    return 1.0 - (overlap / max_tokens)

def compute_calibration_error(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    question: str,
    num_samples: int = 5
) -> float:
    """
    Compute a proxy for calibration error by measuring variance in log-probabilities
    across multiple samples.

    Args:
        model: The transformer model.
        tokenizer: The tokenizer.
        question: The input question.
        num_samples: Number of samples to generate.

    Returns:
        Average log-probability variance as a calibration error proxy.
    """
    inputs = tokenizer(question, return_tensors="pt", truncation=True, max_length=512)

    log_probs = []

    with torch.no_grad():
        for _ in range(num_samples):
            outputs = model.generate(
                **inputs,
                max_new_tokens=64,
                do_sample=True,
                temperature=0.7,
                pad_token_id=tokenizer.eos_token_id,
                return_dict_in_generate=True,
                output_scores=True
            )

            # Extract scores (logits) and convert to log probs
            scores = outputs.scores
            if len(scores) > 0:
                # Average log prob across generated tokens
                avg_log_prob = torch.stack(scores).mean().item()
                log_probs.append(avg_log_prob)

    if len(log_probs) < 2:
        return 0.0

    # Variance as calibration proxy
    mean_lp = sum(log_probs) / len(log_probs)
    variance = sum((lp - mean_lp) ** 2 for lp in log_probs) / len(log_probs)

    return variance

def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 2
) -> float:
    """
    Compute n-gram overlap (Jaccard similarity) between two texts.

    Args:
        text1: First text.
        text2: Second text.
        n: N-gram size.

    Returns:
        Jaccard similarity score between 0 and 1.
    """
    def get_ngrams(text: str, n: int) -> set:
        tokens = text.lower().split()
        if len(tokens) < n:
            return set()
        return set(
            ' '.join(tokens[i:i+n])
            for i in range(len(tokens) - n + 1)
        )

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    if len(ngrams1) == 0 or len(ngrams2) == 0:
        return 0.0

    intersection = ngrams1.intersection(ngrams2)
    union = ngrams1.union(ngrams2)

    return len(intersection) / len(union)