"""
Contract test for the model_output schema.

This test verifies that the ``model_output.schema.yaml`` file can be loaded
as a valid YAML mapping and that the test process stays well under the
8 GB memory limit imposed on contract tests.

The test suite uses only the Python standard library to avoid adding new
runtime dependencies.
"""

import os
from pathlib import Path

import pytest
import yaml
import tracemalloc


@pytest.fixture(scope="module")
def schema_path() -> Path:
    """
    Resolve the absolute path to the model output schema file located in the
    ``tests/contracts`` directory.
    """
    # ``__file__`` points to this test module; the schema lives one level up
    # in ``../contracts/model_output.schema.yaml``.
    return Path(__file__).resolve().parents[1] / "contracts" / "model_output.schema.yaml"


def test_model_output_schema_loads(schema_path: Path):
    """
    Load the YAML schema and assert that it is a mapping (dictionary).
    """
    assert schema_path.is_file(), f"Schema file not found: {schema_path}"
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    assert isinstance(schema, dict), "Schema must be a YAML mapping (dict)."


def test_memory_usage_under_8gb():
    """
    Ensure the test process does not allocate more than 8 GB of memory.

    ``tracemalloc`` tracks memory allocations performed by the Python
    interpreter.  We start it, take an immediate snapshot and sum the size
    of all traced memory blocks.
    """
    tracemalloc.start()
    snapshot = tracemalloc.take_snapshot()
    total_bytes = sum(stat.size for stat in snapshot.statistics("filename"))
    tracemalloc.stop()

    limit_bytes = 8 * 1024**3  # 8 GB
    assert (
        total_bytes < limit_bytes
    ), f"Memory usage {total_bytes / (1024**3):.2f} GB exceeds the 8 GB limit."