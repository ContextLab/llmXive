"""
Sanity‑check script for the Counterfactual Consistency loss.

It creates identical logits for an original and a counterfactual video,
computes the CC loss and asserts that the loss is exactly zero.
"""
import torch

# Import the loss function from the module we just created.
from src.model.loss import counterfactual_consistency_loss

def main() -> None:
    # Create a batch of identical logits.
    logits = torch.randn(4, 10, dtype=torch.float32)

    # Compute the CC loss between the two identical tensors.
    cc = counterfactual_consistency_loss(logits, logits.clone())

    # The KL‑divergence between identical distributions should be zero.
    # Use ``torch.allclose`` with a tiny tolerance to guard against floating‑point noise.
    assert torch.allclose(
        cc, torch.tensor(0.0, dtype=cc.dtype, device=cc.device), atol=1e-6
    ), f"Counterfactual consistency loss is not zero (got {cc.item():.6f})"

    print("Sanity check passed – counterfactual consistency loss = 0.0")

if __name__ == "__main__":
    main()