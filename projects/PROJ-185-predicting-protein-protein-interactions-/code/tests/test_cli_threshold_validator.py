"""
Unit tests for the ``--threshold`` CLI argument validator.

The tests cover two scenarios:
1. Parsing a value below the allowed minimum should cause ``argparse`` to
   exit with a ``SystemExit`` error (the standard behaviour when a custom
   ``type`` raises ``ArgumentTypeError``).
2. Directly invoking ``validate_args`` with a manually‑constructed
   ``argparse.Namespace`` that violates the rule should raise ``ValueError``.
"""

import argparse
import pytest

from src.cli.run_pipeline import create_parser, validate_args


def test_parser_rejects_low_threshold():
    """
    ``argparse`` should abort parsing when ``--threshold`` is less than 0.75.
    """
    parser = create_parser()
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--threshold", "0.5"])
    # ``argparse`` exits with code 2 for user errors.
    assert excinfo.value.code == 2


def test_validate_args_raises_on_invalid_namespace():
    """
    ``validate_args`` must raise ``ValueError`` when called with an invalid
    ``Namespace`` object (e.g., constructed programmatically in tests).
    """
    args = argparse.Namespace(threshold=0.6, norm_method="TPM", seed=42, species="arabidopsis")
    with pytest.raises(ValueError, match="--threshold must be >= 0.75"):
        validate_args(args)