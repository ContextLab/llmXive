"""
Contract test for robustness results schema (T019).

Validates that `data/processed/robustness_results.json` conforms to the
expected schema for User Story 3 (Robustness Checks and Sensitivity Analysis).

Expected structure:
{
  "subsample_results": {
    "<language>": {
      "author_count_coefficient": float,
      "author_count_se": float,
      "author_count_pvalue": float,
      "author_count_ci_lower": float,
      "author_count_ci_upper": float,
      "author_count_adj_pvalue": float,
      "controls": { ... },
      "offset_used": "log(kloc)",
      "n_samples": int,
      "convergence_status": bool
    }
  },
  "entropy_model": {
    "entropy_coefficient": float,
    "entropy_se": float,
    "entropy_pvalue": float,
    "entropy_ci_lower": float,
    "entropy_ci_upper": float,
    "entropy_adj_pvalue": float,
    "controls": { ... },
    "offset_used": "log(kloc)",
    "n_samples": int,
    "convergence_status": bool
  },
  "metadata": {
    "generated_at": "ISO8601",
    "methodology": "Negative-Binomial GLM with log(kloc) offset"
  }
}
"""
import json
import os
import pytest
from pathlib import Path

# Path to the expected output file
OUTPUT_PATH = Path("data/processed/robustness_results.json")

REQUIRED_TOP_LEVEL_KEYS = {
    "subsample_results",
    "entropy_model",
    "metadata"
}

REQUIRED_SUBSAMPLE_KEYS = {
    "author_count_coefficient",
    "author_count_se",
    "author_count_pvalue",
    "author_count_ci_lower",
    "author_count_ci_upper",
    "author_count_adj_pvalue",
    "controls",
    "offset_used",
    "n_samples",
    "convergence_status"
}

REQUIRED_ENTROPY_KEYS = {
    "entropy_coefficient",
    "entropy_se",
    "entropy_pvalue",
    "entropy_ci_lower",
    "entropy_ci_upper",
    "entropy_adj_pvalue",
    "controls",
    "offset_used",
    "n_samples",
    "convergence_status"
}

REQUIRED_METADATA_KEYS = {
    "generated_at",
    "methodology"
}

def load_robustness_results():
    """Load the robustness results JSON file."""
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(f"Output file not found: {OUTPUT_PATH}")
    
    with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.mark.contract
def test_robustness_results_schema_exists():
    """Test that the output file exists and is valid JSON."""
    try:
        data = load_robustness_results()
        assert isinstance(data, dict), "Root element must be a dictionary"
    except FileNotFoundError as e:
        pytest.fail(str(e))
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON format: {e}")

@pytest.mark.contract
def test_robustness_results_top_level_keys():
    """Test that all required top-level keys are present."""
    data = load_robustness_results()
    
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
    assert not missing_keys, f"Missing top-level keys: {missing_keys}"

@pytest.mark.contract
def test_robustness_results_subsample_structure():
    """Test that subsample_results contains valid language entries."""
    data = load_robustness_results()
    subsample_results = data.get("subsample_results", {})
    
    assert isinstance(subsample_results, dict), "subsample_results must be a dictionary"
    assert len(subsample_results) > 0, "subsample_results must contain at least one language"
    
    for lang, results in subsample_results.items():
        assert isinstance(results, dict), f"Results for {lang} must be a dictionary"
        
        missing_keys = REQUIRED_SUBSAMPLE_KEYS - set(results.keys())
        assert not missing_keys, f"Missing keys for language '{lang}': {missing_keys}"
        
        # Validate types
        assert isinstance(results.get("n_samples"), int), f"n_samples for {lang} must be int"
        assert isinstance(results.get("convergence_status"), bool), f"convergence_status for {lang} must be bool"
        assert results.get("offset_used") == "log(kloc)", f"offset_used for {lang} must be 'log(kloc)'"
        
        # Validate numeric fields
        numeric_fields = [
            "author_count_coefficient", "author_count_se", "author_count_pvalue",
            "author_count_ci_lower", "author_count_ci_upper", "author_count_adj_pvalue"
        ]
        for field in numeric_fields:
            val = results.get(field)
            assert val is not None, f"{field} for {lang} cannot be None"
            assert isinstance(val, (int, float)), f"{field} for {lang} must be numeric"

@pytest.mark.contract
def test_robustness_results_entropy_structure():
    """Test that entropy_model contains valid structure."""
    data = load_robustness_results()
    entropy_model = data.get("entropy_model", {})
    
    assert isinstance(entropy_model, dict), "entropy_model must be a dictionary"
    
    missing_keys = REQUIRED_ENTROPY_KEYS - set(entropy_model.keys())
    assert not missing_keys, f"Missing keys in entropy_model: {missing_keys}"
    
    # Validate types
    assert isinstance(entropy_model.get("n_samples"), int), "n_samples must be int"
    assert isinstance(entropy_model.get("convergence_status"), bool), "convergence_status must be bool"
    assert entropy_model.get("offset_used") == "log(kloc)", "offset_used must be 'log(kloc)'"
    
    # Validate numeric fields
    numeric_fields = [
        "entropy_coefficient", "entropy_se", "entropy_pvalue",
        "entropy_ci_lower", "entropy_ci_upper", "entropy_adj_pvalue"
    ]
    for field in numeric_fields:
        val = entropy_model.get(field)
        assert val is not None, f"{field} cannot be None"
        assert isinstance(val, (int, float)), f"{field} must be numeric"

@pytest.mark.contract
def test_robustness_results_metadata_structure():
    """Test that metadata contains required fields."""
    data = load_robustness_results()
    metadata = data.get("metadata", {})
    
    assert isinstance(metadata, dict), "metadata must be a dictionary"
    
    missing_keys = REQUIRED_METADATA_KEYS - set(metadata.keys())
    assert not missing_keys, f"Missing keys in metadata: {missing_keys}"
    
    # Validate content
    assert metadata.get("methodology") is not None, "methodology cannot be None"
    assert "Negative-Binomial" in metadata.get("methodology", "") or "GLM" in metadata.get("methodology", ""), \
        "methodology should mention GLM or Negative-Binomial"
    
    # Validate ISO8601 format for generated_at (basic check)
    generated_at = metadata.get("generated_at", "")
    assert "T" in generated_at or " " in generated_at, "generated_at should contain a time separator"

@pytest.mark.contract
def test_robustness_results_numeric_ranges():
    """Test that numeric values are within plausible ranges."""
    data = load_robustness_results()
    
    # Check p-values are between 0 and 1
    subsample_results = data.get("subsample_results", {})
    for lang, results in subsample_results.items():
        pval = results.get("author_count_pvalue")
        adj_pval = results.get("author_count_adj_pvalue")
        assert 0 <= pval <= 1, f"p-value for {lang} out of range: {pval}"
        assert 0 <= adj_pval <= 1, f"adjusted p-value for {lang} out of range: {adj_pval}"
    
    entropy_model = data.get("entropy_model", {})
    pval = entropy_model.get("entropy_pvalue")
    adj_pval = entropy_model.get("entropy_adj_pvalue")
    assert 0 <= pval <= 1, f"entropy p-value out of range: {pval}"
    assert 0 <= adj_pval <= 1, f"entropy adjusted p-value out of range: {adj_pval}"
    
    # Check n_samples > 0
    for lang, results in subsample_results.items():
        assert results.get("n_samples", 0) > 0, f"n_samples for {lang} must be > 0"
    assert entropy_model.get("n_samples", 0) > 0, "entropy_model n_samples must be > 0"

@pytest.mark.contract
def test_robustness_results_controls_structure():
    """Test that controls dictionary exists and has expected structure."""
    data = load_robustness_results()
    
    # Check subsample controls
    subsample_results = data.get("subsample_results", {})
    for lang, results in subsample_results.items():
        controls = results.get("controls")
        assert isinstance(controls, dict), f"controls for {lang} must be a dictionary"
        # Basic check: controls should not be empty if model was fitted
        # (Some controls might be empty if no controls were used, but typically they exist)
    
    # Check entropy controls
    entropy_model = data.get("entropy_model", {})
    controls = entropy_model.get("controls")
    assert isinstance(controls, dict), "entropy_model controls must be a dictionary"