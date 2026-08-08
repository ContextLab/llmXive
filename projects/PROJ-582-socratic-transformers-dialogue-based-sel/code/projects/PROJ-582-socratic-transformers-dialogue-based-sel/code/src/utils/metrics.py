"""
Metric utility for standard accuracy and loss calculations.

Implements:
- MetricCalculator: Class for computing accuracy, loss, and related metrics.
- compute_prediction_error_proxy: Proxy metric for prediction error analysis.
- compute_calibration_error: Calibration error estimation.
- compute_ngram_overlap: N-gram overlap between texts.
"""
import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


class MetricCalculator:
    """
    A utility class for computing various evaluation metrics.
    
    Attributes:
        model (PreTrainedModel): The model to use for loss computation.
        tokenizer (PreTrainedTokenizer): The tokenizer to use for text processing.
        device (torch.device): The device to run computations on.
    """
    
    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        device: Optional[Union[str, torch.device]] = None
    ):
        """
        Initialize the MetricCalculator.
        
        Args:
            model: The transformer model.
            tokenizer: The transformer tokenizer.
            device: Device to use (e.g., 'cpu', 'cuda'). Defaults to model's device.
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device or next(model.parameters()).device
        self.model.eval()
    
    def compute_accuracy(
        self,
        predictions: Union[List[int], torch.Tensor],
        labels: Union[List[int], torch.Tensor]
    ) -> float:
        """
        Compute accuracy between predictions and labels.
        
        Args:
            predictions: Predicted token IDs.
            labels: Ground truth token IDs.
            
        Returns:
            Accuracy as a float between 0 and 1.
        """
        if isinstance(predictions, list):
            predictions = torch.tensor(predictions)
        if isinstance(labels, list):
            labels = torch.tensor(labels)
        
        predictions = predictions.to(self.device)
        labels = labels.to(self.device)
        
        # Handle different shapes (e.g., sequence vs single prediction)
        if predictions.dim() > 1:
            predictions = predictions.argmax(dim=-1)
        
        # Mask out padding tokens if present (assuming -100 is the ignore index)
        mask = labels != -100
        
        if mask.sum() == 0:
            return 0.0
        
        correct = (predictions[mask] == labels[mask]).sum().item()
        total = mask.sum().item()
        
        return correct / total if total > 0 else 0.0
    
    def compute_loss(
        self,
        input_ids: torch.Tensor,
        labels: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> float:
        """
        Compute the loss for a given input.
        
        Args:
            input_ids: Input token IDs.
            labels: Target token IDs (use -100 for ignore index).
            attention_mask: Optional attention mask.
            
        Returns:
            Loss value as a float.
        """
        input_ids = input_ids.to(self.device)
        labels = labels.to(self.device)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                labels=labels,
                attention_mask=attention_mask
            )
            loss = outputs.loss
        
        return loss.item()
    
    def compute_error_proxy(
        self,
        predictions: Union[List[str], List[int]],
        labels: Union[List[str], List[int]]
    ) -> float:
        """
        Compute a proxy metric for prediction error.
        
        This is a simplified metric that estimates error based on 
        token-level disagreement when inputs are token IDs, 
        or string-level disagreement when inputs are text.
        
        Args:
            predictions: Predicted tokens or text.
            labels: Ground truth tokens or text.
            
        Returns:
            Error proxy value (higher is worse).
        """
        if isinstance(predictions[0], str):
            # Text-based comparison
            mismatches = sum(1 for p, l in zip(predictions, labels) if p != l)
            return mismatches / len(labels) if labels else 0.0
        else:
            # Token-based comparison
            return 1.0 - self.compute_accuracy(predictions, labels)


def compute_prediction_error_proxy(
    predictions: List[Union[str, int]],
    labels: List[Union[str, int]]
) -> float:
    """
    Compute a proxy for prediction error without requiring a model instance.
    
    Args:
        predictions: List of predictions (strings or token IDs).
        labels: List of ground truth labels (strings or token IDs).
        
    Returns:
        Error proxy value between 0 and 1.
    """
    if not predictions or not labels:
        return 0.0
    
    if len(predictions) != len(labels):
        raise ValueError("Predictions and labels must have the same length")
    
    if isinstance(predictions[0], str):
        mismatches = sum(1 for p, l in zip(predictions, labels) if p != l)
        return mismatches / len(labels)
    else:
        # Token-based comparison
        mismatches = sum(1 for p, l in zip(predictions, labels) if p != l)
        return mismatches / len(labels)


def compute_calibration_error(
    model: PreTrainedModel,
    input_ids: torch.Tensor,
    labels: torch.Tensor,
    num_bins: int = 10,
    device: Optional[torch.device] = None
) -> float:
    """
    Compute the Expected Calibration Error (ECE).
    
    Args:
        model: The transformer model.
        input_ids: Input token IDs.
        labels: Ground truth token IDs.
        num_bins: Number of bins for calibration histogram.
        device: Device to run computations on.
        
    Returns:
        Expected Calibration Error as a float.
    """
    device = device or next(model.parameters()).device
    model.eval()
    
    input_ids = input_ids.to(device)
    labels = labels.to(device)
    
    with torch.no_grad():
        outputs = model(input_ids=input_ids, labels=labels)
        logits = outputs.logits
        
        # Get probabilities and predicted classes
        probs = torch.softmax(logits, dim=-1)
        confidences, predictions = torch.max(probs, dim=-1)
        
        # Get correctness
        if labels.dim() == 1:
            # Single token per position
            correct = (predictions == labels).float()
        else:
            # Sequence case: align predictions with labels
            predictions = predictions.view(-1)
            labels = labels.view(-1)
            mask = labels != -100
            correct = (predictions[mask] == labels[mask]).float()
            confidences = confidences.view(-1)[mask]
        
        # Compute ECE
        bin_boundaries = torch.linspace(0, 1, num_bins + 1, device=device)
        ece = 0.0
        total_samples = len(confidences)
        
        if total_samples == 0:
            return 0.0
        
        for i in range(num_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]
            
            # Find samples in this bin
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            bin_size = in_bin.sum().item()
            
            if bin_size > 0:
                avg_confidence = confidences[in_bin].mean().item()
                avg_accuracy = correct[in_bin].mean().item()
                ece += (bin_size / total_samples) * abs(avg_accuracy - avg_confidence)
    
    return ece


def compute_ngram_overlap(
    text1: str,
    text2: str,
    n: int = 2
) -> float:
    """
    Compute the n-gram overlap (Jaccard similarity) between two texts.
    
    Args:
        text1: First text string.
        text2: Second text string.
        n: N-gram size (default: 2 for bigrams).
        
    Returns:
        Jaccard similarity score between 0 and 1.
    """
    def get_ngrams(text: str, n: int) -> set:
        words = text.lower().split()
        if len(words) < n:
            return set()
        return set(
            ' '.join(words[i:i + n]) 
            for i in range(len(words) - n + 1)
        )
    
    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)
    
    if not ngrams1 or not ngrams2:
        return 0.0
    
    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2
    
    return len(intersection) / len(union) if union else 0.0
