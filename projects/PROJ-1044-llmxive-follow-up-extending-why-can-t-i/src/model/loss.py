"""
Counterfactual Consistency loss utilities.

This module provides:
* `cross_entropy_loss` – a standard ``torch.nn.CrossEntropyLoss`` instance.
* `counterfactual_consistency_loss(pred_orig, pred_cf)` – KL‑divergence between the
  prediction distributions of an original video and its counterfactual counterpart.
* `total_loss(ce_loss, cc_loss, lambda_)` – combined loss used during training.
"""
import torch
import torch.nn.functional as F

# Standard cross‑entropy loss for the primary classification task.
cross_entropy_loss = torch.nn.CrossEntropyLoss()

def counterfactual_consistency_loss(
    pred_orig: torch.Tensor, pred_cf: torch.Tensor
) -> torch.Tensor:
    """
    Compute the Counterfactual Consistency (CC) loss.

    Parameters
    ----------
    pred_orig : torch.Tensor
        Logits (unnormalised scores) for the original video. Shape ``(B, C)``.
    pred_cf : torch.Tensor
        Logits for the counterfactual video. Shape ``(B, C)``.

    Returns
    -------
    torch.Tensor
        The KL‑divergence ``KL(p_orig || p_cf)`` averaged over the batch
        (``reduction='batchmean'``). The result is a scalar tensor.
    """
    # Convert logits to log‑probabilities and probabilities.
    log_prob_orig = F.log_softmax(pred_orig, dim=-1)
    prob_cf = F.softmax(pred_cf, dim=-1)

    # KL‑divergence expects (log_prob, prob). Use batch‑mean reduction.
    return F.kl_div(log_prob_orig, prob_cf, reduction="batchmean")

def total_loss(
    ce_loss: torch.Tensor, cc_loss: torch.Tensor, lambda_: float
) -> torch.Tensor:
    """
    Combine the classification (CE) loss with the Counterfactual Consistency loss.

    Parameters
    ----------
    ce_loss : torch.Tensor
        Cross‑entropy loss (scalar).
    cc_loss : torch.Tensor
        Counterfactual consistency loss (scalar).
    lambda_ : float
        Weight for the CC term.

    Returns
    -------
    torch.Tensor
        The total loss ``ce + lambda * cc``.
    """
    return ce_loss + lambda_ * cc_loss
