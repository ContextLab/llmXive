import torch
from typing import List, Dict, Any

class MetricCalculator:
    """
    A utility class for calculating various metrics related to model performance.
    """

    def __init__(self):
        pass

    @staticmethod
    def compute_prediction_error_proxy(predictions: torch.Tensor, targets: torch.Tensor) -> float:
        """
        Computes a proxy for prediction error (e.g., mean absolute error).
        Args:
            predictions (torch.Tensor): The model's predictions.
            targets (torch.Tensor): The ground truth targets.

        Returns:
            float: The average absolute difference between predictions and targets.
        """
        return torch.mean(torch.abs(predictions - targets)).item()  # Convert to Python float

    @staticmethod
    def compute_calibration_error(probabilities: List[float], labels: List[int]) -> float:
        """
        Computes calibration error (e.g., expected calibration error).
        Args:
            probabilities (List[float]): Predicted probabilities for each sample.
            labels (List[int]): Ground truth labels for each sample.

        Returns:
            float: The calibration error score.  (Simple implementation - can be improved)
        """
        # Simple implementation: Calculate the average difference between predicted probability and actual label
        total_error = 0.0
        for prob, label in zip(probabilities, labels):
            total_error += abs(prob - label)
        return total_error / len(probabilities)

    @staticmethod
    def compute_ngram_overlap(reference: str, candidate: str, n: int = 1) -> float:
        """
        Computes the ngram overlap between two strings.
        Args:
            reference (str): The reference string.
            candidate (str): The candidate string.
            n (int): The ngram size.

        Returns:
            float: The ngram overlap score.
        """
        ref_ngrams = set([reference[i:i+n] for i in range(len(reference) - n + 1)])
        cand_ngrams = set([candidate[i:i+n] for i in range(len(candidate) - n + 1)])
        intersection = len(ref_ngrams.intersection(cand_ngrams))
        union = len(ref_ngrams.union(cand_ngrams))
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def compute_accuracy(predictions: torch.Tensor, targets: torch.Tensor) -> float:
      """Computes the accuracy of predictions."""
      _, predicted = torch.max(predictions, 1)
      total = targets.size(0)
      correct = (predicted == targets).sum().item()
      return correct / total

    @staticmethod
    def compute_loss(predictions: torch.Tensor, targets: torch.Tensor) -> float:
        """Computes the loss."""
        # Example using CrossEntropyLoss
        criterion = torch.nn.CrossEntropyLoss()
        loss = criterion(predictions, targets)
        return loss.item()

    def main(self):
        """Placeholder for potential future functionality or testing."""
        pass