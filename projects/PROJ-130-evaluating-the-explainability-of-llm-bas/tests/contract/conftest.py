"""Pytest configuration for contract tests."""
import os
import sys
from pathlib import Path

# Ensure the project root is in the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Constants for schema paths
CONTRACTS_DIR = project_root / "specs" / "001-evaluating-the-explainability-of-llm-bas" / "contracts"

# Schema file paths
DATASET_SCHEMA = CONTRACTS_DIR / "dataset.schema.yaml"
PATCH_SCHEMA = CONTRACTS_DIR / "patch.schema.yaml"
CORRECTNESS_SCHEMA = CONTRACTS_DIR / "correctness.schema.yaml"
EXPLAINABILITY_SCHEMA = CONTRACTS_DIR / "explainability.schema.yaml"
STATISTICAL_SCHEMA = CONTRACTS_DIR / "statistical.schema.yaml"
