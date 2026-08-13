"""
Unit tests for validating that hyper-parameter values defined in ``src.config`` are
within reasonable bounds.

The configuration module is expected to define at least the following attributes:
    - ``LEARNING_RATE``: float, must satisfy ``0 < LEARNING_RATE <= 1``
    - ``BATCH_SIZE``: int, must be ``> 0``
    - ``EPOCHS``: int, must be ``> 0``

If any of these attributes are missing, the test will fail with a clear assertion
message indicating the missing configuration key.
"""

import pytest

# Import the configuration module. The project structure places ``config.py`` inside
# the ``src`` package, so we import it as ``src.config``.
from src import config


def _get_attr(name):
    """Helper to fetch an attribute from ``src.config`` and raise a clear error if missing."""
    if not hasattr(config, name):
        pytest.fail(f"Configuration is missing required attribute '{name}'.")
    return getattr(config, name)


def test_learning_rate_bounds():
    """Check that ``LEARNING_RATE`` is in the interval (0, 1]."""
    lr = _get_attr("LEARNING_RATE")
    assert isinstance(lr, (float, int)), "LEARNING_RATE must be a numeric type."
    assert 0 < lr <= 1, f"LEARNING_RATE should be > 0 and <= 1, got {lr}."


def test_batch_size_positive():
    """Check that ``BATCH_SIZE`` is a positive integer."""
    bs = _get_attr("BATCH_SIZE")
    assert isinstance(bs, int), "BATCH_SIZE must be an integer."
    assert bs > 0, f"BATCH_SIZE should be > 0, got {bs}."


def test_epochs_positive():
    """Check that ``EPOCHS`` is a positive integer."""
    epochs = _get_attr("EPOCHS")
    assert isinstance(epochs, int), "EPOCHS must be an integer."
    assert epochs > 0, f"EPOCHS should be > 0, got {epochs}."