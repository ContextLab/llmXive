import pytest
from src.cli.run_pipeline import create_parser, validate_args

def test_cli_validator_rejects_low_threshold():
    """
    Ensure that the CLI argument validator raises an exception when
    ``--threshold`` is set below the minimum allowed value (0.75).
    """
    parser = create_parser()
    # Simulate a user providing an invalid threshold via the CLI.
    args = parser.parse_args(["--threshold", "0.70"])

    # The validator is expected to raise a ValueError for this case.
    with pytest.raises(ValueError) as excinfo:
        validate_args(args)

    # Optional: check that the error message mentions the threshold constraint.
    assert "--threshold must be >= 0.75" in str(excinfo.value)