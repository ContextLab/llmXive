from __future__ import annotations
import torch
from code.diffusion import mask_future_tokens

def test_mask_fraction():
    seq_len = 20
    batch = torch.arange(seq_len).unsqueeze(0)  # shape (1, seq_len)
    rho = 0.5
    mask_token = -100  # typical ignore index
    masked, mask = mask_future_tokens(batch, rho, mask_token)

    # Exactly half (rounded) of the positions should be masked
    num_masked = mask.sum().item()
    expected = int(round(seq_len * (1 - rho)))
    assert num_masked == expected, f"Expected {expected} masked tokens, got {num_masked}"

    # Masked positions must contain the mask token
    assert (masked[mask] == mask_token).all()
    # Unmasked positions must retain original ids
    assert (masked[~mask] == batch[~mask]).all()