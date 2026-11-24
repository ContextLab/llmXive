from __future__ import annotations
import torch
from typing import Tuple

def mask_future_tokens(
    input_ids: torch.Tensor,
    rho_teacher: float,
    mask_token_id: int,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Apply the masked‑diffusion corruption schedule.

    A fraction ``1 - rho_teacher`` of *future* tokens is replaced by
    ``mask_token_id``.  For simplicity the implementation treats the whole
    sequence as “future” relative to the current step – this matches the
    discrete diffusion formulation used in the project (the trainer will
    later unmask tokens progressively).

    Parameters
    ----------
    input_ids: torch.Tensor
        Tensor of shape ``(..., seq_len)`` containing token IDs.
    rho_teacher: float
        Retaining ratio in ``[0.0, 1.0]``.  ``1.0`` means no masking,
        ``0.0`` means all tokens are masked.
    mask_token_id: int
        Token ID used to represent a masked position (e.g. the tokenizer's
        ``mask_token_id``).

    Returns
    -------
    Tuple[torch.Tensor, torch.Tensor]
        ``masked_input_ids`` – same shape as ``input_ids`` with masked
        positions replaced by ``mask_token_id``.
        ``mask`` – boolean tensor where ``True`` indicates a masked position.
    """
    if not (0.0 <= rho_teacher <= 1.0):
        raise ValueError("rho_teacher must be between 0.0 and 1.0")

    # Random uniform mask; positions with probability (1 - rho_teacher) are masked
    rand = torch.rand_like(input_ids.float())
    mask = rand >= rho_teacher  # True where we mask
    masked_input_ids = input_ids.clone()
    masked_input_ids[mask] = mask_token_id
    return masked_input_ids, mask
