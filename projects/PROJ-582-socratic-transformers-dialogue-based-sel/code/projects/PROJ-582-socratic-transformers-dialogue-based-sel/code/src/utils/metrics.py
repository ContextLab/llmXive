"""
Metric utility for standard accuracy and loss calculations.

Provides functions to compute accuracy and loss for model predictions,
compatible with the project's transformer-based pipeline.
"""
import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


def calculate_accuracy(
    predictions: Union[List[int], torch.Tensor],
    labels: Union[List[int], torch.Tensor],
    ignore_index: int = -100
) -> float:
    """
    Calculate accuracy between predictions and labels.
    
    Args:
        predictions: Model predictions (logits or token ids)
        labels: Ground truth labels
        ignore_index: Index to ignore in the calculation (default: -100)
        
    Returns:
        Accuracy as a float between 0.0 and 1.0
        
    Raises:
        ValueError: If predictions and labels have different shapes
    """
    if isinstance(predictions, torch.Tensor):
        if predictions.dim() > 1:
            # If logits, take argmax
            predictions = predictions.argmax(dim=-1)
        predictions = predictions.flatten()
    else:
        predictions = torch.tensor(predictions).flatten()
        
    if isinstance(labels, torch.Tensor):
        labels = labels.flatten()
    else:
        labels = torch.tensor(labels).flatten()
        
    if predictions.shape != labels.shape:
        raise ValueError(
            f"Predictions and labels must have the same shape. "
            f"Got {predictions.shape} and {labels.shape}"
        )
        
    # Mask out ignored indices
    mask = labels != ignore_index
    if not mask.any():
        return 0.0
        
    correct = (predictions[mask] == labels[mask]).sum().item()
    total = mask.sum().item()
    
    return correct / total if total > 0 else 0.0


def calculate_loss(
    logits: Union[torch.Tensor, List[List[float]]],
    labels: Union[torch.Tensor, List[int]],
    ignore_index: int = -100,
    reduction: str = 'mean'
) -> float:
    """
    Calculate cross-entropy loss between logits and labels.
    
    Args:
        logits: Model output logits of shape (batch_size, seq_len, vocab_size)
               or (batch_size, vocab_size)
        labels: Ground truth labels of shape (batch_size, seq_len) or (batch_size,)
        ignore_index: Index to ignore in the calculation (default: -100)
        reduction: 'mean', 'sum', or 'none'
        
    Returns:
        Loss value as a float
        
    Raises:
        ValueError: If inputs have incompatible shapes
    """
    if isinstance(logits, list):
        logits = torch.tensor(logits, dtype=torch.float32)
    if isinstance(labels, list):
        labels = torch.tensor(labels, dtype=torch.long)
        
    if logits.dim() == 2:
        # (batch_size, vocab_size)
        loss_fn = torch.nn.CrossEntropyLoss(
            ignore_index=ignore_index,
            reduction=reduction
        )
        loss = loss_fn(logits, labels)
    elif logits.dim() == 3:
        # (batch_size, seq_len, vocab_size) -> (batch_size * seq_len, vocab_size)
        batch_size, seq_len, vocab_size = logits.shape
        logits_flat = logits.view(-1, vocab_size)
        labels_flat = labels.view(-1)
        
        loss_fn = torch.nn.CrossEntropyLoss(
            ignore_index=ignore_index,
            reduction=reduction
        )
        loss = loss_fn(logits_flat, labels_flat)
        
        if reduction == 'mean':
            # Recalculate mean over non-ignored tokens
            mask = labels_flat != ignore_index
            if mask.sum() > 0:
                loss = loss * (logits_flat.shape[0] / mask.sum())
    else:
        raise ValueError(
            f"Logits must be 2D or 3D tensor. Got shape {logits.shape}"
        )
        
    if isinstance(loss, torch.Tensor):
        return loss.item()
    return float(loss)


class MetricCalculator:
    """
    A utility class for computing various metrics during training and evaluation.
    
    This class maintains state for running calculations and provides methods
    for batch-wise metric computation.
    """
    
    def __init__(self, ignore_index: int = -100):
        """
        Initialize the MetricCalculator.
        
        Args:
            ignore_index: Index to ignore in calculations (default: -100)
        """
        self.ignore_index = ignore_index
        self.total_correct = 0
        self.total_count = 0
        self.total_loss = 0.0
        self.loss_count = 0
        
    def reset(self):
        """Reset all accumulated metrics."""
        self.total_correct = 0
        self.total_count = 0
        self.total_loss = 0.0
        self.loss_count = 0
        
    def update_accuracy(
        self,
        predictions: Union[List[int], torch.Tensor],
        labels: Union[List[int], torch.Tensor]
    ) -> None:
        """
        Update accuracy metrics with a batch of predictions and labels.
        
        Args:
            predictions: Model predictions
            labels: Ground truth labels
        """
        correct = calculate_accuracy(predictions, labels, self.ignore_index)
        
        if isinstance(predictions, torch.Tensor):
            if predictions.dim() > 1:
                predictions = predictions.argmax(dim=-1)
            predictions = predictions.flatten()
        else:
            predictions = torch.tensor(predictions).flatten()
            
        if isinstance(labels, torch.Tensor):
            labels = labels.flatten()
        else:
            labels = torch.tensor(labels).flatten()
            
        mask = labels != self.ignore_index
        count = mask.sum().item()
        
        if count > 0:
            self.total_correct += correct * count
            self.total_count += count
            
    def update_loss(
        self,
        logits: Union[torch.Tensor, List[List[float]]],
        labels: Union[torch.Tensor, List[int]]
    ) -> None:
        """
        Update loss metrics with a batch of logits and labels.
        
        Args:
            logits: Model output logits
            labels: Ground truth labels
        """
        loss = calculate_loss(logits, labels, self.ignore_index, reduction='sum')
        
        if isinstance(logits, torch.Tensor):
            if logits.dim() == 2:
                count = logits.shape[0]
            elif logits.dim() == 3:
                mask = labels != self.ignore_index
                count = mask.sum().item() if isinstance(mask, torch.Tensor) else mask.sum()
            else:
                count = 1
        else:
            count = 1
            
        self.total_loss += loss
        self.loss_count += count
        
    def get_accuracy(self) -> float:
        """
        Get the current accuracy.
        
        Returns:
            Accuracy as a float, or 0.0 if no data has been seen
        """
        if self.total_count == 0:
            return 0.0
        return self.total_correct / self.total_count
        
    def get_loss(self) -> float:
        """
        Get the current average loss.
        
        Returns:
            Average loss as a float, or 0.0 if no data has been seen
        """
        if self.loss_count == 0:
            return 0.0
        return self.total_loss / self.loss_count
        
    def get_metrics(self) -> dict:
        """
        Get all current metrics.
        
        Returns:
            Dictionary containing 'accuracy' and 'loss'
        """
        return {
            'accuracy': self.get_accuracy(),
            'loss': self.get_loss()
        }
