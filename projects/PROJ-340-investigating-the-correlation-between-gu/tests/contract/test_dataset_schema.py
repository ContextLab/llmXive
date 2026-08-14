"""
Contract test for dataset schema validation.
Validates the existence and structure of schema files defined in T004a/b.
"""
import os
import yaml
import pytest
from pathlib import Path

SPEC_DIR = Path(__file__).parents[2] / "specs" / "001-gut-microbiome-sleep-architecture" / "contracts"

def test_required_variables_schema_exists():
    """Verify required_variables.yaml exists."""
    path = Path("data/config/required_variables.yaml")
    assert path.exists(), "required_variables.yaml must exist"
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    assert "required_predictors" in data
    assert "required_outcomes" in data

def test_dataset_schema_exists():
    """Verify dataset.schema.yaml exists."""
    path = SPEC_DIR / "dataset.schema.yaml"
    assert path.exists(), "dataset.schema.yaml must exist"

def test_output_schema_exists():
    """Verify output.schema.yaml exists."""
    path = SPEC_DIR / "output.schema.yaml"
    assert path.exists(), "output.schema.yaml must exist"
