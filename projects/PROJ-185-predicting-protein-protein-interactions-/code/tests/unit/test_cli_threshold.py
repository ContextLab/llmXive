"""
Unit tests for the CLI threshold validator.

The validator is expected to reject any threshold value lower than 0.75 by
raising an ``argparse.ArgumentError``. A valid threshold should pass without
raising an exception.
"""

import argparse

import pytest

# The validator lives in the ``src.cli.validator`` module.
from src.cli.validator import validate_threshold


def test_validator_rejects_low_threshold():
    """
    The validator must raise ``argparse.ArgumentError`` when the supplied
    threshold is below the allowed minimum (0.75).
    """
    # Create a namespace mimicking the result of argparse parsing.
    args = argparse.Namespace(threshold=0.70)

    # The validator should refuse this value.
    with pytest.raises(argparse.ArgumentError):
        validate_threshold(args)


def test_validator_accepts_valid_threshold():
    """
    A threshold equal to or above 0.75 should be accepted without error.
    """
    args = argparse.Namespace(threshold=0.80)

    # No exception should be raised.
    try:
        validate_threshold(args)
    except Exception as exc:
        pytest.fail(f"Validator raised an unexpected exception: {exc}")