"""
Unit test for the injection schema validation (Task T005b).

The test loads ``contracts/injection.schema.yaml`` and a sample
``config/error_rates.yaml`` and asserts that the ``error_rates`` field is a
non‑empty list of floats.  The test deliberately does **not** check concrete
values – only the structural requirements, as required by the specification.
"""

import pathlib
import yaml
import pytest

# Paths are relative to the repository root
SCHEMA_PATH = pathlib.Path("contracts/injection.schema.yaml")
ERROR_RATES_PATH = pathlib.Path("config/error_rates.yaml")


def load_yaml(path: pathlib.Path):
    """Utility to read a YAML file."""
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_error_rates_structure():
    # Load and validate the schema – the schema itself is not programmatically
    # validated here; we only need the file to exist.
    assert SCHEMA_PATH.is_file(), f"{SCHEMA_PATH} does not exist"

    # Load the sample error‑rates configuration
    config = load_yaml(ERROR_RATES_PATH)
    assert "error_rates" in config, "Missing 'error_rates' key in config"

    error_rates = config["error_rates"]
    # Must be a list
    assert isinstance(error_rates, list), "'error_rates' must be a list"
    # Must contain at least one element
    assert len(error_rates) > 0, "'error_rates' list must not be empty"
    # Every element must be a float (or int that can be cast to float)
    for rate in error_rates:
        assert isinstance(rate, (float, int)), "All error rates must be numeric"
        # Normalise to float and ensure it is within a sensible range
        rate_f = float(rate)
        assert 0.0 <= rate_f <= 1.0, "Error rates must be between 0 and 1"
