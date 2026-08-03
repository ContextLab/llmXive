"""
Metric utility for standard accuracy and loss calculations.
"""
import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


def compute_prediction_error_proxy(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    inputs: Union[str, List[str], torch.Tensor],
    labels: Optional[Union[str, List[str], torch.Tensor]] = None,
) -> float:
    """
    Compute a proxy for prediction error based on log-probabilities.
    
    This function calculates the average negative log-likelihood (NLL) of the
    model's predictions, which serves as a proxy for prediction error. Lower
    values indicate better predictions.
    
    Args:
        model: The transformer model.
        tokenizer: The tokenizer associated with the model.
        inputs: Input text(s) or tokenized inputs.
        labels: Optional target text(s) or tokenized labels. If None, uses inputs as labels.
        
    Returns:
        Average negative log-likelihood (NLL) per token.
    """
    if isinstance(inputs, str):
        inputs = [inputs]
    
    if isinstance(labels, str):
        labels = [labels]
    
    # Tokenize inputs
    if isinstance(inputs, str) or isinstance(inputs, list):
        tokenized = tokenizer(inputs, return_tensors="pt", padding=True, truncation=True)
    else:
        tokenized = inputs  # Assume already tokenized
    
    # Move to model device
    device = next(model.parameters()).device
    tokenized = {k: v.to(device) for k, v in tokenized.items()}
    
    # Compute loss if labels provided, otherwise use inputs as labels
    if labels is not None:
        if isinstance(labels, list):
            label_tokens = tokenizer(labels, return_tensors="pt", padding=True, truncation=True)
            label_tokens = {k: v.to(device) for k, v in label_tokens.items()}
            tokenized["labels"] = label_tokens["input_ids"]
        else:
            tokenized["labels"] = labels
    else:
        tokenized["labels"] = tokenized["input_ids"]
    
    with torch.no_grad():
        outputs = model(**tokenized)
        loss = outputs.loss.item()
    
    return loss


def compute_calibration_error(
    predicted_probs: List[float],
    true_labels: List[int],
    num_bins: int = 10,
) -> float:
    """
    Compute the Expected Calibration Error (ECE).
    
    This metric measures how well the predicted probabilities match the actual
    accuracy of the model. A perfectly calibrated model has ECE = 0.
    
    Args:
        predicted_probs: List of predicted probabilities (confidence scores).
        true_labels: List of true binary labels (0 or 1).
        num_bins: Number of bins for calibration.
        
    Returns:
        Expected Calibration Error (ECE).
    """
    if len(predicted_probs) != len(true_labels):
        raise ValueError("predicted_probs and true_labels must have the same length")
    
    bins = [[] for _ in range(num_bins)]
    
    for prob, label in zip(predicted_probs, true_labels):
        bin_idx = min(int(prob * num_bins), num_bins - 1)
        bins[bin_idx].append((prob, label))
    
    ece = 0.0
    total_samples = len(predicted_probs)
    
    for bin_items in bins:
        if not bin_items:
            continue
        
        avg_confidence = sum(p for p, _ in bin_items) / len(bin_items)
        avg_accuracy = sum(l for _, l in bin_items) / len(bin_items)
        bin_weight = len(bin_items) / total_samples
        
        ece += bin_weight * abs(avg_confidence - avg_accuracy)
    
    return ece


def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 2,
) -> float:
    """
    Compute the n-gram overlap (Jaccard similarity) between two texts.
    
    Args:
        text1: First text.
        text2: Second text.
        n: Size of n-grams.
        
    Returns:
        Jaccard similarity score (0.0 to 1.0).
    """
    def get_ngrams(text, n):
        words = text.lower().split()
        return set([" ".join(words[i:i+n]) for i in range(len(words) - n + 1)])
    
    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)
    
    if not ngrams1 or not ngrams2:
        return 0.0
    
    intersection = ngrams1.intersection(ngrams2)
    union = ngrams1.union(ngrams2)
    
    return len(intersection) / len(union)


class MetricCalculator:
    """
    A utility class for computing various metrics for model evaluation.
    """
    
    def __init__(
        self,
        model: Optional[PreTrainedModel] = None,
        tokenizer: Optional[PreTrainedTokenizer] = None,
    ):
        """
        Initialize the MetricCalculator.
        
        Args:
            model: Optional model for computing prediction error.
            tokenizer: Optional tokenizer for computing prediction error.
        """
        self.model = model
        self.tokenizer = tokenizer
    
    def compute_prediction_error(
        self,
        inputs: Union[str, List[str], torch.Tensor],
        labels: Optional[Union[str, List[str], torch.Tensor]] = None,
    ) -> float:
        """
        Compute prediction error using the internal model and tokenizer.
        
        Args:
            inputs: Input text(s) or tokenized inputs.
            labels: Optional target text(s) or tokenized labels.
            
        Returns:
            Average negative log-likelihood.
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model and tokenizer must be set to compute prediction error")
        
        return compute_prediction_error_proxy(self.model, self.tokenizer, inputs, labels)
    
    def compute_accuracy(
        self,
        predictions: List[int],
        ground_truth: List[int],
    ) -> float:
        """
        Compute classification accuracy.
        
        Args:
            predictions: List of predicted class indices.
            ground_truth: List of true class indices.
            
        Returns:
            Accuracy score (0.0 to 1.0).
        """
        if len(predictions) != len(ground_truth):
            raise ValueError("predictions and ground_truth must have the same length")
        
        correct = sum(p == g for p, g in zip(predictions, ground_truth))
        return correct / len(ground_truth) if ground_truth else 0.0
    
    def compute_loss(
        self,
        inputs: Union[str, List[str], torch.Tensor],
        labels: Optional[Union[str, List[str], torch.Tensor]] = None,
    ) -> float:
        """
        Alias for compute_prediction_error.
        
        Args:
            inputs: Input text(s) or tokenized inputs.
            labels: Optional target text(s) or tokenized labels.
            
        Returns:
            Average loss.
        """
        return self.compute_prediction_error(inputs, labels)


def main():
    """
    Main entry point for testing metrics.
    """
    # Test n-gram overlap
    text1 = "The quick brown fox"
    text2 = "The quick brown dog"
    overlap = compute_ngram_overlap(text1, text2, n=2)
    print(f"N-gram overlap: {overlap:.4f}")
    
    # Test calibration error
    probs = [0.9, 0.8, 0.3, 0.6, 0.1]
    labels = [1, 1, 0, 0, 0]
    ece = compute_calibration_error(probs, labels)
    print(f"Calibration error (ECE): {ece:.4f}")
    
    # Test accuracy
    preds = [1, 0, 1, 1, 0]
    truths = [1, 0, 1, 0, 0]
    acc = MetricCalculator().compute_accuracy(preds, truths)
    print(f"Accuracy: {acc:.4f}")


if __name__ == "__main__":
    main()