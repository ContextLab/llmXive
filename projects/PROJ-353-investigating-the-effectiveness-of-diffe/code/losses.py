import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional

def cross_entropy_loss(
    logits: torch.Tensor,
    targets: torch.Tensor,
    ignore_index: int = -100
) -> torch.Tensor:
    """
    Compute standard Cross-Entropy loss for node classification.

    Args:
        logits: Model output logits of shape (N, num_classes).
        targets: Target class indices of shape (N,).
        ignore_index: Label to ignore (e.g., for padding or unlabeled nodes).

    Returns:
        Scalar tensor representing the mean loss.
    """
    return F.cross_entropy(logits, targets, ignore_index=ignore_index)


def info_nce_loss(
    query: torch.Tensor,
    key: torch.Tensor,
    temperature: float = 0.07,
    mask: Optional[torch.Tensor] = None
) -> torch.Tensor:
    """
    Compute InfoNCE (Noise Contrastive Estimation) loss for contrastive learning.

    This implements the standard NT-Xent style loss:
    L = -log( exp(sim(q, k_pos) / tau) / sum_j(exp(sim(q, k_j) / tau)) )

    Args:
        query: Query embeddings of shape (N, D).
        key: Key embeddings of shape (N, D). Assumes keys are paired with queries
             (e.g., augmented views of the same node).
        temperature: Scalar temperature parameter (tau).
        mask: Optional boolean mask of shape (N, N) indicating valid positive pairs.
              If None, assumes diagonal (i-th query matches i-th key).

    Returns:
        Scalar tensor representing the mean InfoNCE loss.
    """
    # Normalize embeddings to unit length
    query = F.normalize(query, p=2, dim=-1)
    key = F.normalize(key, p=2, dim=-1)

    # Compute similarity matrix (cosine similarity)
    # logits shape: (N, N)
    logits = torch.matmul(query, key.T) / temperature

    # Create labels: assume diagonal is positive (i matches i)
    labels = torch.arange(logits.size(0), device=logits.device)

    loss = F.cross_entropy(logits, labels)
    return loss


class LinearProbe(nn.Module):
    """
    A simple linear layer used as a probe to evaluate representation quality.
    
    In the context of InfoNCE training, the encoder learns representations.
    To measure accuracy (convergence), we attach a linear probe to the 
    frozen (or fine-tuned) encoder and train the probe on the downstream 
    classification task.
    """
    def __init__(self, in_features: int, num_classes: int):
        super().__init__()
        self.probe = nn.Linear(in_features, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input embeddings of shape (N, in_features).
        Returns:
            Logits of shape (N, num_classes).
        """
        return self.probe(x)

def compute_accuracy(
    logits: torch.Tensor,
    targets: torch.Tensor,
    topk: int = 1
) -> torch.Tensor:
    """
    Compute accuracy given logits and targets.

    Args:
        logits: Predicted logits of shape (N, num_classes).
        targets: Ground truth labels of shape (N,).
        topk: Number of top predictions to consider (default 1).

    Returns:
        Scalar tensor accuracy (0.0 to 1.0).
    """
    if topk == 1:
        _, predicted = torch.max(logits, 1)
        correct = (predicted == targets).sum().item()
    else:
        _, predicted = torch.topk(logits, topk, dim=1)
        correct = (predicted == targets.unsqueeze(1)).sum().item()
    
    total = targets.size(0)
    return torch.tensor(correct / total, device=logits.device, dtype=torch.float32)
