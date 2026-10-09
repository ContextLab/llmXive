"""
Tests for the GFM wrapper in Differentiable Gradient-Check Mode (T006-diff).

Checks that gradients flow through inputs but not through weights.
"""
import os
import sys
import unittest

import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.gfm_wrapper import GFMWrapper


WEIGHTS_PATH = os.path.join("data", "raw", "gfm_weights.pt")


class TestGFMDiffMode(unittest.TestCase):
    """Gradient-flow checks for the differentiable mode."""

    def _make_wrapper(self, **kwargs):
        # Missing weights file only triggers a warning + random init,
        # which is sufficient for gradient-flow structure checks.
        return GFMWrapper(WEIGHTS_PATH, latent_dim=8, obs_dim=16,
                          action_dim=4, **kwargs)

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            self._make_wrapper(mode="bogus")

    def test_weights_frozen_in_diff_mode(self):
        wrapper = self._make_wrapper(mode="diff")
        for param in wrapper.parameters():
            self.assertFalse(param.requires_grad)

    def test_gradients_flow_through_inputs(self):
        wrapper = self._make_wrapper(mode="diff")
        x = torch.randn(2, 16)
        actions = wrapper(x)
        self.assertTrue(actions.requires_grad)
        loss = actions.sum()
        loss.backward()
        self.assertIsNotNone(wrapper.encoder[0].weight.grad is None)
        # Input gradient must exist and be non-zero.
        # The wrapper enables requires_grad on the input internally,
        # so re-run explicitly to inspect the input tensor.
        x2 = torch.randn(2, 16, requires_grad=True)
        latents = wrapper.encode(x2)
        latents.sum().backward()
        self.assertIsNotNone(x2.grad)
        self.assertTrue(torch.any(x2.grad != 0))

    def test_no_gradient_through_weights(self):
        wrapper = self._make_wrapper(mode="diff")
        x = torch.randn(2, 16, requires_grad=True)
        actions = wrapper(x)
        actions.sum().backward()
        for name, param in wrapper.named_parameters():
            self.assertTrue(
                param.grad is None or torch.all(param.grad == 0),
                f"Weight '{name}' received a non-zero gradient",
            )

    def test_verify_gradient_flow_helper(self):
        wrapper = self._make_wrapper(mode="diff")
        result = wrapper.verify_gradient_flow(torch.randn(3, 16))
        self.assertTrue(result["input_grad_nonzero"])
        self.assertTrue(result["weights_frozen"])

    def test_frozen_mode_has_no_input_grad(self):
        wrapper = self._make_wrapper(mode="frozen")
        x = torch.randn(2, 16)
        actions = wrapper(x)
        self.assertFalse(actions.requires_grad)

    def test_verify_requires_diff_mode(self):
        wrapper = self._make_wrapper(mode="frozen")
        with self.assertRaises(RuntimeError):
            wrapper.verify_gradient_flow(torch.randn(1, 16))


if __name__ == "__main__":
    unittest.main()