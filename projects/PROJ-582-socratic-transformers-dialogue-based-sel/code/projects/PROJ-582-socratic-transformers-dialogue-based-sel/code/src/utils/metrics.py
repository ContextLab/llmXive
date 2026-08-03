"""
Metric utility for standard accuracy and loss calculations.
"""
import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

class MetricCalculator:
    """Calculator for various evaluation metrics."""
    
    def __init__(self, model: Optional[PreTrainedModel] = None, tokenizer: Optional[PreTrainedTokenizer] = None):
        self.model = model
        self.tokenizer = tokenizer

    def compute_accuracy(self, predictions: List[int], labels: List[int]) -> float:
        """Compute accuracy between predictions and labels."""
        if len(predictions) != len(labels):
            raise ValueError("Predictions and labels must have the same length")
        
        correct = sum(p == l for p, l in zip(predictions, labels))
        return correct / len(labels) if len(labels) > 0 else 0.0

    def compute_loss(self, logits: torch.Tensor, labels: torch.Tensor) -> float:
        """Compute cross-entropy loss."""
        if logits.dim() == 2:
            # Single sequence
            loss_fct = torch.nn.CrossEntropyLoss()
            return loss_fct(logits.unsqueeze(0), labels.unsqueeze(0)).item()
        else:
            # Batch sequence
            loss_fct = torch.nn.CrossEntropyLoss()
            return loss_fct(logits.view(-1, logits.size(-1)), labels.view(-1)).item()

    def compute_prediction_error_proxy(self, generated: str, target: str) -> float:
        """
        Compute a proxy for prediction error based on string similarity.
        In a real implementation, this would use log-probabilities.
        """
        # Simple token overlap as a proxy
        gen_tokens = set(generated.split())
        target_tokens = set(target.split())
        
        if not target_tokens:
            return 1.0
        
        overlap = len(gen_tokens.intersection(target_tokens))
        return 1.0 - (overlap / len(target_tokens))

    def compute_calibration_error(self, probs: List[float], correct: List[bool]) -> float:
        """Compute expected calibration error."""
        if len(probs) != len(correct):
            raise ValueError("Probs and correct must have the same length")
        
        bins = 10
        bin_boundaries = [i / bins for i in range(bins + 1)]
        error = 0.0
        
        for i in range(bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]
            
            bin_probs = [p for p, c in zip(probs, correct) if bin_lower <= p < bin_upper]
            bin_correct = [c for p, c in zip(probs, correct) if bin_lower <= p < bin_upper]
            
            if bin_probs:
                avg_conf = sum(bin_probs) / len(bin_probs)
                avg_acc = sum(bin_correct) / len(bin_correct)
                error += len(bin_probs) * abs(avg_conf - avg_acc)
        
        return error / len(probs) if len(probs) > 0 else 0.0

    def compute_ngram_overlap(self, text1: str, text2: str, n: int = 2) -> float:
        """Compute n-gram overlap between two texts."""
        def get_ngrams(text, n):
            tokens = text.split()
            return set([" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)])
        
        ngrams1 = get_ngrams(text1, n)
        ngrams2 = get_ngrams(text2, n)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        overlap = len(ngrams1.intersection(ngrams2))
        return overlap / min(len(ngrams1), len(ngrams2))


def compute_prediction_error_proxy(generated: str, target: str) -> float:
    """Wrapper for MetricCalculator.compute_prediction_error_proxy."""
    calc = MetricCalculator()
    return calc.compute_prediction_error_proxy(generated, target)

def compute_calibration_error(probs: List[float], correct: List[bool]) -> float:
    """Wrapper for MetricCalculator.compute_calibration_error."""
    calc = MetricCalculator()
    return calc.compute_calibration_error(probs, correct)

def compute_ngram_overlap(text1: str, text2: str, n: int = 2) -> float:
    """Wrapper for MetricCalculator.compute_ngram_overlap."""
    calc = MetricCalculator()
    return calc.compute_ngram_overlap(text1, text2, n)
