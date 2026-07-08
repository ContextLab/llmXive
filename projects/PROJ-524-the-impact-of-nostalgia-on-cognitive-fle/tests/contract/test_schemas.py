"""
Contract tests for generated schemas.

Verifies that the generated YAML schemas are valid and contain
expected structural elements as defined in the project plan.
"""
import os
import yaml
import pytest
from pathlib import Path

# Paths relative to project root
CONTRACTS_DIR = Path("contracts")
DATASET_SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"

@pytest.fixture(scope="module")
def dataset_schema():
    """Load the dataset schema."""
    if not DATASET_SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found: {DATASET_SCHEMA_PATH}. Run T007 first.")
    with open(DATASET_SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def output_schema():
    """Load the output schema."""
    if not OUTPUT_SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found: {OUTPUT_SCHEMA_PATH}. Run T007 first.")
    with open(OUTPUT_SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestDatasetSchema:
    def test_schema_exists(self, dataset_schema):
        """Test that the dataset schema is not empty."""
        assert dataset_schema is not None
        assert "properties" in dataset_schema

    def test_required_top_level_properties(self, dataset_schema):
        """Test that required top-level properties exist."""
        required = ["metadata", "participants"]
        for prop in required:
            assert prop in dataset_schema["properties"], f"Missing property: {prop}"

    def test_participant_fields(self, dataset_schema):
        """Test that participant items have required fields."""
        participants = dataset_schema["properties"]["participants"]["items"]["properties"]
        required_fields = ["participant_id", "stimulus_type", "age", "perseverative_errors", "categories_completed"]
        for field in required_fields:
            assert field in participants, f"Missing participant field: {field}"

    def test_stimulus_type_enum(self, dataset_schema):
        """Test that stimulus_type is restricted to valid values."""
        stimulus_type_def = dataset_schema["properties"]["participants"]["items"]["properties"]["stimulus_type"]
        assert "enum" in stimulus_type_def
        assert set(stimulus_type_def["enum"]) == {"nostalgia", "control"}

    def test_age_minimum(self, dataset_schema):
        """Test that age has a minimum constraint of 65."""
        age_def = dataset_schema["properties"]["participants"]["items"]["properties"]["age"]
        assert age_def.get("minimum") == 65

    def test_mmse_score_optional(self, dataset_schema):
        """Test that MMSE score is nullable."""
        mmse_def = dataset_schema["properties"]["participants"]["items"]["properties"]["mmse_score"]
        assert mmse_def.get("nullable") is True

class TestOutputSchema:
    def test_schema_exists(self, output_schema):
        """Test that the output schema is not empty."""
        assert output_schema is not None
        assert "properties" in output_schema

    def test_required_sections(self, output_schema):
        """Test that required report sections exist."""
        required = ["statistical_report", "sensitivity_report", "final_report"]
        for section in required:
            assert section in output_schema["properties"], f"Missing section: {section}"

    def test_statistical_report_structure(self, output_schema):
        """Test statistical report has expected metrics."""
        stats_props = output_schema["properties"]["statistical_report"]["properties"]
        assert "comparisons" in stats_props
        assert "power_analysis" in stats_props

    def test_effect_size_fields(self, output_schema):
        """Test that effect size includes Cohen's d and CI."""
        comparison_items = output_schema["properties"]["statistical_report"]["properties"]["comparisons"]["items"]["properties"]
        effect_size_def = comparison_items["effect_size"]["properties"]
        assert "cohens_d" in effect_size_def
        assert "ci_95_lower" in effect_size_def
        assert "ci_95_upper" in effect_size_def

    def test_sensitivity_thresholds(self, output_schema):
        """Test that sensitivity report tracks thresholds."""
        sensitivity_props = output_schema["properties"]["sensitivity_report"]["properties"]
        assert "thresholds_tested" in sensitivity_props
        assert "robustness_flags" in sensitivity_props

    def test_validity_status_enum(self, output_schema):
        """Test that final report validity status has correct enum."""
        final_report_props = output_schema["properties"]["final_report"]["properties"]
        validity_def = final_report_props["validity_status"]
        assert "enum" in validity_def
        expected = {"validated", "partial", "simulation_only"}
        assert set(validity_def["enum"]) == expected