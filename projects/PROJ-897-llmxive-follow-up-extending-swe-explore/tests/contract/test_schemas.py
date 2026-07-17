"""
Skeleton for contract tests for all schemas (T008).

This file serves as a placeholder and entry point for contract tests
verifying the consistency of data artifacts against the YAML schemas
defined in the `contracts/` directory.

Currently, it delegates to specific test modules:
- test_dataset_schema.py
- test_agent_log_schema.py
- test_result_schema.py
"""

import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def test_schema_structure_exists():
    """Verify that the contracts directory and expected schema files exist."""
    contracts_dir = PROJECT_ROOT / "contracts"
    assert contracts_dir.exists(), "Contracts directory missing"

    expected_schemas = [
        "dataset_schema.yaml",
        "agent_log_schema.yaml",
        "result_schema.yaml"
    ]

    for schema_name in expected_schemas:
        schema_path = contracts_dir / schema_name
        assert schema_path.exists(), f"Missing schema file: {schema_path}"

def test_pytest_discovery():
    """Simple sanity check that pytest can discover this file."""
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
