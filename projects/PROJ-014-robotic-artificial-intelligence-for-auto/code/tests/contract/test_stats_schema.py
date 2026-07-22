import os
import json
import pytest
from pathlib import Path
from src.utils.config import get_path

# Schema definition for statistical report
# Expected structure based on T034 (Welch's ANOVA/Kruskal-Wallis) and T036 (Associational header)
REQUIRED_TOP_LEVEL_KEYS = {
    "header",
    "methodology",
    "descriptive_statistics",
    "statistical_tests",
    "post_hoc_tests",
    "conclusions",
    "metadata"
}

REQUIRED_HEADER_KEYS = {
    "warning",
    "disclaimer"
}

REQUIRED_METHODOLOGY_KEYS = {
    "test_type",
    "alpha_level",
    "assumptions_checked"
}

REQUIRED_DESCRIPTIVE_KEYS = {
    "rgb",
    "depth",
    "grid"
}

DESCRIPTIVE_SUB_KEYS = {
    "mean_auc",
    "std_auc",
    "mean_success_rate",
    "std_success_rate",
    "n_seeds"
}

REQUIRED_STATISTICAL_TESTS_KEYS = {
    "test_name",
    "statistic",
    "p_value",
    "degrees_of_freedom",
    "assumption_violations"
}

REQUIRED_POST_HOC_KEYS = {
    "test_name",
    "comparisons"
}

COMPARISON_KEYS = {
    "group_1",
    "group_2",
    "p_value",
    "significant"
}

def load_statistical_report():
    """Load the statistical report from the expected path."""
    report_path = get_path("results/statistical_report.json")
    if not os.path.exists(report_path):
        # If the report doesn't exist yet, this is a test environment issue
        # but for the contract test, we assert the path exists
        pytest.fail(f"Statistical report not found at {report_path}. "
                    "Ensure T031/T034 have been executed to generate the report.")
    
    with open(report_path, 'r') as f:
        return json.load(f)

def test_report_file_exists():
    """Verify that the statistical report file exists."""
    report_path = get_path("results/statistical_report.json")
    assert os.path.exists(report_path), f"Report file {report_path} does not exist"

def test_report_schema_has_required_keys():
    """Verify the report contains all required top-level keys."""
    report = load_statistical_report()
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(report.keys())
    assert not missing_keys, f"Missing required top-level keys: {missing_keys}"

def test_report_header_schema():
    """Verify the header section contains required warning and disclaimer."""
    report = load_statistical_report()
    assert "header" in report, "Missing 'header' section"
    missing_header_keys = REQUIRED_HEADER_KEYS - set(report["header"].keys())
    assert not missing_header_keys, f"Missing header keys: {missing_header_keys}"
    
    # Verify the warning is about associational nature (FR-007)
    warning_text = report["header"].get("warning", "").lower()
    assert "associational" in warning_text or "correlational" in warning_text, \
        "Header warning must state findings are associational"

def test_report_methodology_schema():
    """Verify methodology section contains test details."""
    report = load_statistical_report()
    assert "methodology" in report, "Missing 'methodology' section"
    missing_method_keys = REQUIRED_METHODOLOGY_KEYS - set(report["methodology"].keys())
    assert not missing_method_keys, f"Missing methodology keys: {missing_method_keys}"
    
    # Verify test type is one of the expected statistical tests
    test_type = report["methodology"].get("test_type", "").lower()
    assert "anova" in test_type or "kruskal" in test_type or "welch" in test_type, \
        f"Invalid test type: {test_type}"

def test_report_descriptive_statistics_schema():
    """Verify descriptive statistics for all three modalities."""
    report = load_statistical_report()
    assert "descriptive_statistics" in report, "Missing 'descriptive_statistics' section"
    desc_stats = report["descriptive_statistics"]
    
    missing_modalities = REQUIRED_DESCRIPTIVE_KEYS - set(desc_stats.keys())
    assert not missing_modalities, f"Missing modality stats: {missing_modalities}"
    
    for modality in REQUIRED_DESCRIPTIVE_KEYS:
        mod_data = desc_stats[modality]
        missing_sub_keys = DESCRIPTIVE_SUB_KEYS - set(mod_data.keys())
        assert not missing_sub_keys, \
            f"Missing descriptive keys for {modality}: {missing_sub_keys}"
        
        # Validate types
        assert isinstance(mod_data["mean_auc"], (int, float)), f"{modality} mean_auc must be numeric"
        assert isinstance(mod_data["std_auc"], (int, float)), f"{modality} std_auc must be numeric"
        assert isinstance(mod_data["n_seeds"], int), f"{modality} n_seeds must be integer"

def test_report_statistical_tests_schema():
    """Verify the main statistical test results."""
    report = load_statistical_report()
    assert "statistical_tests" in report, "Missing 'statistical_tests' section"
    
    tests = report["statistical_tests"]
    # Should be a list of test results (e.g., ANOVA, Kruskal-Wallis)
    assert isinstance(tests, list), "statistical_tests must be a list"
    assert len(tests) > 0, "statistical_tests list cannot be empty"
    
    for test_entry in tests:
        missing_keys = REQUIRED_STATISTICAL_TESTS_KEYS - set(test_entry.keys())
        assert not missing_keys, f"Missing keys in statistical test entry: {missing_keys}"
        
        # Validate types
        assert isinstance(test_entry["p_value"], (int, float)), "p_value must be numeric"
        assert 0 <= test_entry["p_value"] <= 1, "p_value must be between 0 and 1"

def test_report_post_hoc_schema():
    """Verify post-hoc test results (Tukey/Dunn)."""
    report = load_statistical_report()
    assert "post_hoc_tests" in report, "Missing 'post_hoc_tests' section"
    
    post_hocs = report["post_hoc_tests"]
    assert isinstance(post_hocs, list), "post_hoc_tests must be a list"
    
    for post_hoc in post_hocs:
        missing_keys = REQUIRED_POST_HOC_KEYS - set(post_hoc.keys())
        assert not missing_keys, f"Missing keys in post-hoc entry: {missing_keys}"
        
        comparisons = post_hoc.get("comparisons", [])
        assert isinstance(comparisons, list), "comparisons must be a list"
        
        for comp in comparisons:
            missing_comp_keys = COMPARISON_KEYS - set(comp.keys())
            assert not missing_comp_keys, f"Missing keys in comparison: {missing_comp_keys}"
            
            assert isinstance(comp["p_value"], (int, float)), "comparison p_value must be numeric"
            assert isinstance(comp["significant"], bool), "comparison significant must be boolean"

def test_report_metadata_schema():
    """Verify metadata section exists and contains basic info."""
    report = load_statistical_report()
    assert "metadata" in report, "Missing 'metadata' section"
    
    metadata = report["metadata"]
    assert "generated_at" in metadata, "Missing 'generated_at' in metadata"
    assert "script_version" in metadata, "Missing 'script_version' in metadata"