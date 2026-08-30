"""
Unit tests for JSON Schema validation.
Ensures that the generated schemas are valid and can be loaded.
"""
import json
import os
import pytest
from pathlib import Path

# Path to the contracts directory
CONTRACTS_DIR = Path("contracts")

def load_schema(name: str) -> dict:
    """Load a schema from the contracts directory."""
    file_path = CONTRACTS_DIR / f"{name}.schema.json"
    if not file_path.exists():
        pytest.fail(f"Schema file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_paper_manifest_schema_exists():
    """Test that PaperManifest schema exists and is valid JSON."""
    schema = load_schema("PaperManifest")
    assert schema is not None
    assert "$schema" in schema
    assert schema["title"] == "PaperManifest"

def test_repro_result_schema_exists():
    """Test that ReproResult schema exists and is valid JSON."""
    schema = load_schema("ReproResult")
    assert schema is not None
    assert "$schema" in schema
    assert schema["title"] == "ReproResult"

def test_stat_summary_schema_exists():
    """Test that StatSummary schema exists and is valid JSON."""
    schema = load_schema("StatSummary")
    assert schema is not None
    assert "$schema" in schema
    assert schema["title"] == "StatSummary"

def test_paper_manifest_required_fields():
    """Test that PaperManifest schema has required fields."""
    schema = load_schema("PaperManifest")
    required_fields = ["doi", "repo_url", "dataset_name", "reported_metrics", "reaction_conditions"]
    for field in required_fields:
        assert field in schema["required"], f"Missing required field: {field}"

def test_repro_result_required_fields():
    """Test that ReproResult schema has required fields."""
    schema = load_schema("ReproResult")
    required_fields = ["doi", "reproduced_metrics", "deviations", "reproducibility_score", "status"]
    for field in required_fields:
        assert field in schema["required"], f"Missing required field: {field}"

def test_stat_summary_required_fields():
    """Test that StatSummary schema has required fields."""
    schema = load_schema("StatSummary")
    required_fields = ["total_papers", "successful_reproductions", "t_tests", "mixed_effects_model", "heterogeneity"]
    for field in required_fields:
        assert field in schema["required"], f"Missing required field: {field}"