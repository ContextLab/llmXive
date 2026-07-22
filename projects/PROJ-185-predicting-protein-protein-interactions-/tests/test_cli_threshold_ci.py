"""
CI test for the CLI argument validator.

This test ensures that the pipeline's CLI rejects a ``--threshold`` value
lower than the minimum allowed value of 0.75.  The validator lives in
``src.cli.run_pipeline.validate_args`` and is exercised directly via the
parser created by ``src.cli.run_pipeline.create_parser``.
"""

import pytest

# Import the parser factory and the validator function from the pipeline CLI.
from src.cli.run_pipeline import create_parser, validate_args


def test_cli_validator_rejects_low_threshold():
    """
    Verify that providing a threshold below 0.75 causes the validator to raise
    an exception.

    The parser is used to construct a namespace with a deliberately low
    threshold.  ``validate_args`` should raise an exception (ValueError,
    argparse.ArgumentError, or SystemExit) to indicate the invalid input.
    """
    # Build a parser and supply a minimal set of required arguments.
    # ``--species`` is required by the CLI; we use a placeholder name.
    parser = create_parser()
    args = parser.parse_args(
        [
            "--threshold",
            "0.7",          # Below the allowed minimum.
            "--species",
            "arabidopsis",  # Minimal required argument for the parser.
        ]
    )

    # The validator must reject the low threshold.  The exact exception type
    # is not mandated by the specification, so we accept any exception.
    with pytest.raises(Exception):
        validate_args(args)