"""
LocateAnythingSparsityWrapper

This wrapper adds a sparsity knob to a LocateAnything‑style model and
records per‑image inference metrics required by the integration test
`tests/unit/test_model_wrapper.py`.

The wrapper expects a model object that implements a callable interface
(e.g. ``model(image, text)``) returning a prediction dictionary or any
serialisable object.  The exact model implementation is outside the scope
of this repository – the tests provide a lightweight mock model.

The wrapper performs three duties:

1. Enforces the CPU‑only execution constraint by setting
   ``torch.set_num_threads(2)`` (FR‑006).  The test asserts that
   ``torch.get_num_threads()`` equals ``2`` after the wrapper is
   instantiated.
2. Applies a sparsity configuration (window size) to the underlying model.
   The concrete model may expose a ``set_sparsity_mask`` method; if it does
   not, the wrapper simply records the configuration for downstream
   analysis.
3. Executes a forward pass while measuring latency (in milliseconds) and
   returns a dictionary containing the raw ``prediction`` and the measured
   ``latency_ms`` key.

The implementation is deliberately lightweight and has no external
dependencies beyond ``torch`` (already required by the project) and the
existing ``SparsityConfig`` class.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict

import torch

from .sparsity import SparsityConfig

__all__ = ["LocateAnythingSparsityWrapper"]


class LocateAnythingSparsityWrapper:
    """
    Wrapper for a LocateAnything‑style model that injects a sparsity mask
    and records per‑image inference metrics.

    Parameters
    ----------
    model : Callable
        The underlying model.  It must be callable with the same signature
        used in the tests (e.g. ``model(image, text)``) and return a
        prediction object.
    sparsity_config : SparsityConfig
        Configuration describing the desired attention window size.
    """

    def __init__(self, model: Callable[..., Any], sparsity_config: SparsityConfig) -> None:
        # Enforce the CPU‑only thread limit as required by FR‑006.
        torch.set_num_threads(2)

        self.model = model
        self.sparsity_config = sparsity_config

        # If the wrapped model provides a hook to receive the mask, use it.
        # This keeps the wrapper generic – the mock model used in tests does
        # not implement the hook, which is fine.
        if hasattr(self.model, "set_sparsity_mask"):
            mask = self._generate_mask()
            self.model.set_sparsity_mask(mask)

    def _generate_mask(self) -> Any:
        """
        Generate a mask based on the provided ``SparsityConfig``.
        The concrete mask format is model‑specific; for the purposes of
        the tests we simply return the window size as a placeholder.
        """
        # ``window_size == 0`` denotes a global mask (no restriction).
        # Returning the integer directly makes the mask easily inspectable
        # in debugging sessions while satisfying the contract that a mask
        # is produced.
        return self.sparsity_config.window_size

    def forward(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Run a forward pass through the wrapped model while measuring latency.

        Returns
        -------
        dict
            ``{
                "prediction": <model output>,
                "latency_ms": <float>
            }``
        """
        start = time.time()
        # The underlying model may be a heavy PyTorch module; we run it
        # under ``torch.no_grad`` to avoid unnecessary gradient allocation.
        with torch.no_grad():
            prediction = self.model(*args, **kwargs)
        end = time.time()
        latency_ms = (end - start) * 1000.0

        return {"prediction": prediction, "latency_ms": latency_ms}
