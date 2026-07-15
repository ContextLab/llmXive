"""
Contract test for report schema (US3).

This test verifies that the final reporting pipeline produces a JSON output
containing the required statistical findings, visualization references, and
biological plausibility checks as defined in FR-009, SC-001, SC-005, and SC-006.

Prerequisites:
- T034: Reporting script generates final report JSON
- T035: Excluded species and data coverage metrics are included
- T036: Biological plausibility check is documented
"""
import json
import os
import pytest
from pathlib import Path
from typing import Any, Dict, Set

# Project root path (assuming tests/contract/ structure)
PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORT_OUTPUT_PATH = PROJECT_ROOT / "artifacts" / "reports" / "final_report.json"

# Required schema definition based on FR-009, SC-001, SC-005, SC-006
REQUIRED_TOP_LEVEL_KEYS: Set[str] = {
    "summary",
    "statistical_findings",
    "data_coverage",
    "visualization_references",
    "biological_plausibility",
    "metadata"
}

REQUIRED_SUMMARY_KEYS: Set[str] = {
    "associational_framing",
    "total_species_analyzed",
    "total_samples_analyzed",
    "excluded_species_count",
    "primary_conclusion"
}

REQUIRED_STATISTICAL_FINDINGS_KEYS: Set[str] = {
    "lmm_metrics",
    "rf_metrics",
    "r2_delta",
    "sc002_status",
    "p_values_adjusted",
    "significant_predictors"
}

REQUIRED_DATA_COVERAGE_KEYS: Set[str] = {
    "merge_success_rate",
    "species_distribution",
    "nutrient_coverage",
    "excluded_species_list"
}

REQUIRED_VISUALIZATION_KEYS: Set[str] = {
    "partial_dependence_plots",
    "total_size_mb",
    "size_constraint_met"
}

REQUIRED_BIOLOGICAL_PLAUSIBILITY_KEYS: Set[str] = {
    "checked_against_literature",
    "coefficient_directions_valid",
    "notes"
}

REQUIRED_METADATA_KEYS: Set[str] = {
    "timestamp",
    "pipeline_version",
    "data_sources"
}

def load_report_output() -> Dict[str, Any]:
    """Load the final report JSON file."""
    if not REPORT_OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Report output file not found at {REPORT_OUTPUT_PATH}. "
            "Ensure T034 has been executed successfully."
        )
    
    with open(REPORT_OUTPUT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_report_file_exists():
    """Contract Test: Verify the final report file exists."""
    assert REPORT_OUTPUT_PATH.exists(), (
        f"Report output file {REPORT_OUTPUT_PATH} does not exist. "
        "Run the reporting pipeline (T034) first."
    )

def test_report_schema_structure():
    """Contract Test: Verify top-level keys in the final report JSON."""
    data = load_report_output()
    
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
    assert not missing_keys, (
        f"Report JSON is missing required top-level keys: {missing_keys}. "
        f"Expected keys: {REQUIRED_TOP_LEVEL_KEYS}, Found: {set(data.keys())}"
    )

def test_summary_section_schema():
    """Contract Test: Verify summary section contains required fields."""
    data = load_report_output()
    summary = data.get("summary", {})
    
    assert isinstance(summary, dict), "summary must be a dictionary"
    
    missing_keys = REQUIRED_SUMMARY_KEYS - set(summary.keys())
    assert not missing_keys, (
        f"Summary missing required keys: {missing_keys}. "
        f"Expected: {REQUIRED_SUMMARY_KEYS}, Found: {set(summary.keys())}"
    )
    
    # Validate associational framing constraint (FR-009)
    assert summary.get("associational_framing") is True, (
        "Summary must explicitly state 'associational_framing': True"
    )

def test_statistical_findings_schema():
    """Contract Test: Verify statistical findings contain required metrics."""
    data = load_report_output()
    findings = data.get("statistical_findings", {})
    
    assert isinstance(findings, dict), "statistical_findings must be a dictionary"
    
    missing_keys = REQUIRED_STATISTICAL_FINDINGS_KEYS - set(findings.keys())
    assert not missing_keys, (
        f"Statistical findings missing required keys: {missing_keys}. "
        f"Expected: {REQUIRED_STATISTICAL_FINDINGS_KEYS}, Found: {set(findings.keys())}"
    )
    
    # Validate types
    assert isinstance(findings.get("r2_delta"), (int, float)), "r2_delta must be numeric"
    assert findings.get("sc002_status") in ["PASS", "FAIL"], (
        f"sc002_status must be 'PASS' or 'FAIL', got: {findings.get('sc002_status')}"
    )

def test_data_coverage_schema():
    """Contract Test: Verify data coverage metrics (SC-001, SC-005)."""
    data = load_report_output()
    coverage = data.get("data_coverage", {})
    
    assert isinstance(coverage, dict), "data_coverage must be a dictionary"
    
    missing_keys = REQUIRED_DATA_COVERAGE_KEYS - set(coverage.keys())
    assert not missing_keys, (
        f"Data coverage missing required keys: {missing_keys}. "
        f"Expected: {REQUIRED_DATA_COVERAGE_KEYS}, Found: {set(coverage.keys())}"
    )
    
    # Validate merge success rate (SC-001)
    assert "merge_success_rate" in coverage, "merge_success_rate is missing"
    merge_rate = coverage.get("merge_success_rate")
    assert isinstance(merge_rate, (int, float)) and 0 <= merge_rate <= 1, (
        f"merge_success_rate must be between 0 and 1, got: {merge_rate}"
    )
    
    # Validate excluded species list (SC-005)
    assert isinstance(coverage.get("excluded_species_list"), list), (
        "excluded_species_list must be a list"
    )

def test_visualization_references_schema():
    """Contract Test: Verify visualization references and size constraints (SC-004)."""
    data = load_report_output()
    viz = data.get("visualization_references", {})
    
    assert isinstance(viz, dict), "visualization_references must be a dictionary"
    
    missing_keys = REQUIRED_VISUALIZATION_KEYS - set(viz.keys())
    assert not missing_keys, (
        f"Visualization references missing required keys: {missing_keys}. "
        f"Expected: {REQUIRED_VISUALIZATION_KEYS}, Found: {set(viz.keys())}"
    )
    
    # Validate size constraint
    assert "total_size_mb" in viz, "total_size_mb is missing"
    assert isinstance(viz.get("total_size_mb"), (int, float)), "total_size_mb must be numeric"
    assert viz.get("size_constraint_met") is True, (
        "size_constraint_met must be True if total_size_mb <= 100"
    )
    
    # Check actual size constraint (SC-004)
    if viz.get("total_size_mb", 0) > 100:
        assert False, f"Total report size ({viz.get('total_size_mb')} MB) exceeds 100MB limit (SC-004)"

def test_biological_plausibility_schema():
    """Contract Test: Verify biological plausibility check (SC-006)."""
    data = load_report_output()
    bio = data.get("biological_plausibility", {})
    
    assert isinstance(bio, dict), "biological_plausibility must be a dictionary"
    
    missing_keys = REQUIRED_BIOLOGICAL_PLAUSIBILITY_KEYS - set(bio.keys())
    assert not missing_keys, (
        f"Biological plausibility missing required keys: {missing_keys}. "
        f"Expected: {REQUIRED_BIOLOGICAL_PLAUSIBILITY_KEYS}, Found: {set(bio.keys())}"
    )
    
    # Validate check status
    assert bio.get("checked_against_literature") is True, (
        "Biological plausibility must state 'checked_against_literature': True"
    )

def test_metadata_schema():
    """Contract Test: Verify metadata section contains required fields."""
    data = load_report_output()
    metadata = data.get("metadata", {})
    
    assert isinstance(metadata, dict), "metadata must be a dictionary"
    
    missing_keys = REQUIRED_METADATA_KEYS - set(metadata.keys())
    assert not missing_keys, (
        f"Metadata missing required keys: {missing_keys}. "
        f"Expected: {REQUIRED_METADATA_KEYS}, Found: {set(metadata.keys())}"
    )

def test_consistency_between_summary_and_coverage():
    """Contract Test: Verify consistency between summary and data coverage sections."""
    data = load_report_output()
    summary = data.get("summary", {})
    coverage = data.get("data_coverage", {})
    
    summary_excluded = summary.get("excluded_species_count", 0)
    coverage_excluded = len(coverage.get("excluded_species_list", []))
    
    assert summary_excluded == coverage_excluded, (
        f"Excluded species count mismatch: summary={summary_excluded}, "
        f"coverage_list_length={coverage_excluded}"
    )