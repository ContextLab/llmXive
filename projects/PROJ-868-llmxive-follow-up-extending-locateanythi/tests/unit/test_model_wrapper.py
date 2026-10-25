"""
Integration test for the LocateAnything sparsity wrapper.

The test constructs a dummy ``LocateAnythingSparsityWrapper`` with a
``window_size`` of 32, runs a forward pass on a synthetic image tensor,
and checks that the expected keys are present in the output dictionary.
It also verifies that the CPU thread limit is correctly set to 2.
"""

import torch

from code.model.locateany import LocateAnythingSparsityWrapper
from code.model.sparsity import SparsityConfig

def test_wrapper_forward_pass():
    # Create a dummy input – a batch of 1 image with 3 channels,
    # height and width of 224 (standard Vision Transformer size).
    dummy_image = torch.randn(1, 3, 224, 224)

    # Initialise the wrapper with a 32‑patch window.
    config = SparsityConfig(window_size=32)
    wrapper = LocateAnythingSparsityWrapper(sparsity_config=config)

    # Run forward – the wrapper returns a dict with prediction, latency, etc.
    output = wrapper.forward(dummy_image)

    # Expected keys.
    assert isinstance(output, dict)
    for key in ["prediction", "latency_ms"]:
        assert key in output

    # Ensure the thread limit is honoured.
    assert torch.get_num_threads() == 2
