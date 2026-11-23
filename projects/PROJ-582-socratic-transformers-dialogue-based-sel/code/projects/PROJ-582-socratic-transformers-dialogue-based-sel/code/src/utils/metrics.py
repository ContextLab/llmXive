"""
Metric utility module for standard accuracy and loss calculations.

This module provides functions to calculate accuracy and loss for model
evaluation, compatible with the Socratic Transformers pipeline.
"""

import math
from typing import List, Optional, Tuple, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


def calculate_accuracy(
    predictions: Union[List[int], torch.Tensor],
    labels: Union[List[int], torch.Tensor]
) -> float:
    """
    Calculate accuracy between predictions and labels.

    Args:
        predictions: Model predictions (logits or token IDs).
        labels: Ground truth labels.

    Returns:
        Accuracy as a float between 0 and 1.
    """
    if len(predictions) != len(labels):
        raise ValueError("Predictions and labels must have the same length")

    if len(predictions) == 0:
        return 0.0

    # Convert to tensors if they are lists
    if isinstance(predictions, list):
        predictions = torch.tensor(predictions)
    if isinstance(labels, list):
        labels = torch.tensor(labels)

    # If predictions are logits, get the argmax
    if predictions.dim() > 1:
        predictions = predictions.argmax(dim=-1)

    # Calculate accuracy
    correct = (predictions == labels).sum().item()
    total = len(labels)

    return correct / total


def calculate_loss(
    model: PreTrainedModel,
    input_ids: torch.Tensor,
    attention_mask: Optional[torch.Tensor] = None,
    labels: Optional[torch.Tensor] = None
) -> float:
    """
    Calculate the loss for a given model and input.

    Args:
        model: The transformer model to evaluate.
        input_ids: Token IDs for the input sequence.
        attention_mask: Attention mask for padding.
        labels: Ground truth labels for loss calculation.

    Returns:
        The computed loss as a float.
    """
    model.eval()

    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        loss = outputs.loss

    return loss.item()


class MetricCalculator:
    """
    A utility class for calculating various metrics during model evaluation.
    """

    def __init__(self, model: Optional[PreTrainedModel] = None):
        """
        Initialize the MetricCalculator.

        Args:
            model: Optional pre-trained model for loss calculation.
        """
        self.model = model

    def set_model(self, model: PreTrainedModel) -> None:
        """
        Set the model for loss calculation.

        Args:
            model: The transformer model to use.
        """
        self.model = model

    def calculate_accuracy_batch(
        self,
        predictions: torch.Tensor,
        labels: torch.Tensor
    ) -> float:
        """
        Calculate accuracy for a batch of predictions.

        Args:
            predictions: Model predictions (logits or token IDs).
            labels: Ground truth labels.

        Returns:
            Accuracy as a float.
        """
        return calculate_accuracy(predictions, labels)

    def calculate_loss_batch(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None
    ) -> float:
        """
        Calculate loss for a batch of inputs.

        Args:
            input_ids: Token IDs for the input sequence.
            attention_mask: Attention mask for padding.
            labels: Ground truth labels.

        Returns:
            The computed loss.

        Raises:
            ValueError: If no model is set.
        """
        if self.model is None:
            raise ValueError("Model must be set before calculating loss")

        return calculate_loss(self.model, input_ids, attention_mask, labels)

    def evaluate_batch(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None
    ) -> Tuple[float, float]:
        """
        Evaluate both accuracy and loss for a batch.

        Args:
            input_ids: Token IDs for the input sequence.
            attention_mask: Attention mask for padding.
            labels: Ground truth labels.

        Returns:
            Tuple of (accuracy, loss).

        Raises:
            ValueError: If no model is set for loss calculation.
        """
        if self.model is None:
            raise ValueError("Model must be set before evaluating")

        # Forward pass
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            loss = outputs.loss.item()

            # Get predictions
            if hasattr(outputs, 'logits'):
                predictions = outputs.logits.argmax(dim=-1)
            else:
                raise ValueError("Model outputs do not contain logits")

            accuracy = calculate_accuracy(predictions, labels)

        return accuracy, loss

def main():
    """Main entry point for testing the metrics module."""
    print("Testing metrics module...")

    # Test accuracy calculation
    preds = [0, 1, 2, 3, 4]
    labels = [0, 1, 2, 3, 4]
    acc = calculate_accuracy(preds, labels)
    print(f"Perfect accuracy test: {acc}")
    assert acc == 1.0, "Perfect accuracy should be 1.0"

    # Test with mismatches
    labels_mismatch = [0, 0, 0, 0, 0]
    acc_mismatch = calculate_accuracy(preds, labels_mismatch)
    print(f"Mismatch accuracy test: {acc_mismatch}")
    assert acc_mismatch == 0.2, "Mismatch accuracy should be 0.2"

    print("All tests passed!")


if __name__ == "__main__":
    main()