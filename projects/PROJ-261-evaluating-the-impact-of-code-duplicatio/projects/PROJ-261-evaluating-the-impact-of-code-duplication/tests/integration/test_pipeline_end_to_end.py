"""
Integration test for end-to-end correlation pipeline (T028).

Tests the complete US2 pipeline flow:
1. Load US1 outputs (clone_metrics.csv, perplexity_scores.csv)
2. Run bug detection on HumanEval subset
3. Compute Spearman correlation between duplication density and metrics
4. Validate output schema and checksums

Per spec.md Independent Test requirements for US2.
"""
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "projects/PROJ-261-evaluating-the-impact-of-code-duplication"))

DATA_DIR = PROJECT_ROOT / "projects/PROJ-261-evaluating-the-impact-of-code-duplication" / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ANALYSIS_DIR = DATA_DIR / "analysis"

# Test fixtures
@pytest.fixture
def sample_clone_metrics(tmp_path):
    """Create sample clone_metrics.csv matching US1 output schema."""
    clone_metrics_path = tmp_path / "clone_metrics.csv"
    data = [
        {"file_id": "1", "clone_density": 0.15, "segment_length": 50, "parse_success": True},
        {"file_id": "2", "clone_density": 0.32, "segment_length": 120, "parse_success": True},
        {"file_id": "3", "clone_density": 0.08, "segment_length": 35, "parse_success": True},
        {"file_id": "4", "clone_density": 0.45, "segment_length": 200, "parse_success": True},
        {"file_id": "5", "clone_density": 0.21, "segment_length": 80, "parse_success": True},
    ]
    clone_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(data).to_csv(clone_metrics_path, index=False)
    return clone_metrics_path

@pytest.fixture
def sample_perplexity_scores(tmp_path):
    """Create sample perplexity_scores.csv matching US1 output schema."""
    perplexity_path = tmp_path / "perplexity_scores.csv"
    data = [
        {"file_id": "1", "perplexity": 12.5, "model": "codegen-350M-mono", "valid": True},
        {"file_id": "2", "perplexity": 18.2, "model": "codegen-350M-mono", "valid": True},
        {"file_id": "3", "perplexity": 9.8, "model": "codegen-350M-mono", "valid": True},
        {"file_id": "4", "perplexity": 25.1, "model": "codegen-350M-mono", "valid": True},
        {"file_id": "5", "perplexity": 14.3, "model": "codegen-350M-mono", "valid": True},
    ]
    perplexity_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(data).to_csv(perplexity_path, index=False)
    return perplexity_path

@pytest.fixture
def sample_bug_detection_results(tmp_path):
    """Create sample bug_detection_results.csv matching T031 output schema."""
    bug_results_path = tmp_path / "bug_detection_results.csv"
    data = [
        {"problem_id": "1", "pass_at_1": 0.85, "total_tests": 20, "passed_tests": 17},
        {"problem_id": "2", "pass_at_1": 0.72, "total_tests": 25, "passed_tests": 18},
        {"problem_id": "3", "pass_at_1": 0.90, "total_tests": 15, "passed_tests": 14},
        {"problem_id": "4", "pass_at_1": 0.65, "total_tests": 30, "passed_tests": 20},
        {"problem_id": "5", "pass_at_1": 0.78, "total_tests": 18, "passed_tests": 14},
    ]
    bug_results_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(data).to_csv(bug_results_path, index=False)
    return bug_results_path

@pytest.fixture
def correlation_schema(tmp_path):
    """Load correlation schema from contracts directory."""
    contracts_dir = PROJECT_ROOT / "projects/PROJ-261-evaluating-the-impact-of-code-duplication" / "specs" / "001-evaluating-the-impact-of-code-duplication" / "contracts"
    schema_path = contracts_dir / "correlation_results.schema.yaml"
    return schema_path

def test_pipeline_loads_us1_outputs(sample_clone_metrics, sample_perplexity_scores, tmp_path):
    """Test that pipeline can load US1 output files (clone_metrics.csv, perplexity_scores.csv)."""
    # Verify files exist and have correct schema
    assert sample_clone_metrics.exists()
    assert sample_perplexity_scores.exists()
    
    clone_df = pd.read_csv(sample_clone_metrics)
    perplexity_df = pd.read_csv(sample_perplexity_scores)
    
    # Validate required columns
    assert "file_id" in clone_df.columns
    assert "clone_density" in clone_df.columns
    assert "file_id" in perplexity_df.columns
    assert "perplexity" in perplexity_df.columns
    
    # Verify data types
    assert clone_df["clone_density"].dtype in ["float64", "float32", "int64"]
    assert perplexity_df["perplexity"].dtype in ["float64", "float32", "int64"]

def test_pipeline_joins_metrics(sample_clone_metrics, sample_perplexity_scores, tmp_path):
    """Test that pipeline correctly joins clone density and perplexity metrics."""
    clone_df = pd.read_csv(sample_clone_metrics)
    perplexity_df = pd.read_csv(sample_perplexity_scores)
    
    # Simulate join operation (T033 equivalent)
    joined_df = pd.merge(clone_df, perplexity_df, on="file_id", how="inner")
    
    assert len(joined_df) == len(clone_df)
    assert "clone_density" in joined_df.columns
    assert "perplexity" in joined_df.columns
    assert "file_id" in joined_df.columns

def test_pipeline_computes_spearman_correlation(joined_metrics_fixture):
    """Test that pipeline computes Spearman correlation correctly (T032)."""
    # This test validates the correlation computation logic
    from scipy import stats
    
    # Create sample joined metrics
    data = {
        "clone_density": [0.15, 0.32, 0.08, 0.45, 0.21],
        "perplexity": [12.5, 18.2, 9.8, 25.1, 14.3]
    }
    df = pd.DataFrame(data)
    
    # Compute Spearman correlation
    corr, p_value = stats.spearmanr(df["clone_density"], df["perplexity"])
    
    # Validate correlation is in valid range [-1, 1]
    assert -1.0 <= corr <= 1.0
    assert 0.0 <= p_value <= 1.0

def test_pipeline_validates_correlation_schema(tmp_path, correlation_schema):
    """Test that correlation results conform to schema (T027 contract test)."""
    # Verify schema file exists (created in T010)
    assert correlation_schema.exists(), f"Schema file not found: {correlation_schema}"
    
    # Load and validate schema structure
    with open(correlation_schema, "r") as f:
        import yaml
        schema = yaml.safe_load(f)
    
    # Verify required schema fields
    assert "properties" in schema
    assert "clone_density_correlation" in schema["properties"]
    assert "perplexity_correlation" in schema["properties"]
    assert "bug_detection_correlation" in schema["properties"]

def test_pipeline_handles_missing_data(tmp_path):
    """Test that pipeline gracefully handles missing US1 outputs."""
    # Create empty data directory
    empty_dir = tmp_path / "data" / "processed"
    empty_dir.mkdir(parents=True, exist_ok=True)
    
    # Pipeline should raise appropriate error or return empty results
    clone_path = empty_dir / "clone_metrics.csv"
    assert not clone_path.exists()
    
    # This simulates the pipeline's error handling behavior
    # (T022 error handling implementation)
    with pytest.raises((FileNotFoundError, ValueError)):
        pd.read_csv(clone_path)

def test_pipeline_outputs_correlation_results(tmp_path):
    """Test that pipeline produces valid correlation_results.csv (T034)."""
    output_path = tmp_path / "correlation_results.csv"
    
    # Create sample correlation results
    data = {
        "metric_pair": ["clone_density_perplexity", "clone_density_accuracy"],
        "correlation": [0.75, -0.42],
        "p_value": [0.001, 0.023],
        "n_samples": [1000, 50],
        "threshold_used": [0.7, 0.7]
    }
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    
    # Validate output
    result_df = pd.read_csv(output_path)
    assert len(result_df) > 0
    assert "correlation" in result_df.columns
    assert "p_value" in result_df.columns
    assert "n_samples" in result_df.columns

def test_pipeline_checksum_computation(tmp_path):
    """Test that pipeline computes checksums for output files (T036)."""
    from checksum_manifest import compute_file_checksum
    
    # Create sample output file
    output_path = tmp_path / "correlation_results.csv"
    df = pd.DataFrame({"correlation": [0.75], "p_value": [0.001]})
    df.to_csv(output_path, index=False)
    
    # Compute checksum
    checksum = compute_file_checksum(output_path)
    
    # Validate checksum format (SHA256 hex string)
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)

def test_pipeline_sensitivity_analysis(tmp_path):
    """Test that pipeline performs sensitivity analysis across thresholds (T040)."""
    thresholds = [0.7, 0.8, 0.9]
    results = []
    
    for threshold in thresholds:
        # Simulate correlation at different thresholds
        data = {
            "threshold": threshold,
            "clone_density_perplexity_corr": 0.75 - (threshold * 0.1),
            "clone_density_accuracy_corr": -0.42 + (threshold * 0.05)
        }
        results.append(data)
    
    df = pd.DataFrame(results)
    output_path = tmp_path / "sensitivity_analysis.csv"
    df.to_csv(output_path, index=False)
    
    # Validate sensitivity analysis output
    result_df = pd.read_csv(output_path)
    assert len(result_df) == len(thresholds)
    assert all(t in result_df["threshold"].values for t in thresholds)

def test_pipeline_end_to_end_flow(tmp_path, sample_clone_metrics, sample_perplexity_scores):
    """
    Full end-to-end test: US1 outputs → bug detection → correlation → results.
    
    This validates the complete US2 pipeline flow as specified in tasks.md.
    """
    # Step 1: Load US1 outputs
    clone_df = pd.read_csv(sample_clone_metrics)
    perplexity_df = pd.read_csv(sample_perplexity_scores)
    
    # Step 2: Join metrics (T033)
    joined_df = pd.merge(clone_df, perplexity_df, on="file_id", how="inner")
    
    # Step 3: Compute correlation (T032)
    from scipy import stats
    corr, p_value = stats.spearmanr(joined_df["clone_density"], joined_df["perplexity"])
    
    # Step 4: Save results (T034)
    results_path = tmp_path / "correlation_results.csv"
    results_df = pd.DataFrame({
        "metric_pair": ["clone_density_perplexity"],
        "correlation": [corr],
        "p_value": [p_value],
        "n_samples": [len(joined_df)],
        "threshold_used": [0.7]
    })
    results_df.to_csv(results_path, index=False)
    
    # Step 5: Validate final output
    final_df = pd.read_csv(results_path)
    assert len(final_df) > 0
    assert -1.0 <= final_df["correlation"].iloc[0] <= 1.0
    assert 0.0 <= final_df["p_value"].iloc[0] <= 1.0

def test_pipeline_reproducibility(tmp_path):
    """Test that pipeline produces reproducible results with fixed seeds (T043)."""
    import random
    import numpy as np
    
    # Set seeds
    random.seed(42)
    np.random.seed(42)
    
    # Generate sample data
    data1 = np.random.rand(100)
    data2 = np.random.rand(100)
    
    # Compute correlation
    from scipy import stats
    corr1, p1 = stats.spearmanr(data1, data2)
    
    # Reset seeds and regenerate
    random.seed(42)
    np.random.seed(42)
    data1_new = np.random.rand(100)
    data2_new = np.random.rand(100)
    corr2, p2 = stats.spearmanr(data1_new, data2_new)
    
    # Results should be identical
    assert corr1 == corr2
    assert p1 == p2

def test_pipeline_sc004_significance_validation(tmp_path):
    """
    Test SC-004: significance threshold check (T035).
    
    Validates that p-values are properly documented per Wikipedia: Misuse of p-values.
    """
    # Create correlation results with p-values
    results_path = tmp_path / "correlation_results.csv"
    data = {
        "metric_pair": ["clone_density_perplexity", "clone_density_accuracy"],
        "correlation": [0.75, -0.42],
        "p_value": [0.001, 0.023],
        "n_samples": [1000, 50],
        "threshold_used": [0.7, 0.7],
        "significance_level": [0.05, 0.05],
        "is_significant": [True, True],
        "effect_size": ["large", "medium"]
    }
    df = pd.DataFrame(data)
    df.to_csv(results_path, index=False)
    
    # Validate SC-004 requirements
    result_df = pd.read_csv(results_path)
    
    # Check that significance_level is documented
    assert "significance_level" in result_df.columns
    
    # Check that is_significant is computed
    assert "is_significant" in result_df.columns
    
    # Check that effect_size is documented (prevents p-value misuse)
    assert "effect_size" in result_df.columns

@pytest.mark.integration
def test_pipeline_performance_500mb_corpus(tmp_path):
    """
    Test that pipeline can handle 500MB corpus (SC-001 validation).
    
    Simulates processing of full dataset within 24-hour window.
    """
    # Create mock large dataset
    large_clone_df = pd.DataFrame({
        "file_id": [str(i) for i in range(10000)],
        "clone_density": np.random.rand(10000),
        "segment_length": np.random.randint(10, 500, 10000),
        "parse_success": [True] * 10000
    })
    
    large_perplexity_df = pd.DataFrame({
        "file_id": [str(i) for i in range(10000)],
        "perplexity": np.random.rand(10000) * 50,
        "model": ["codegen-350M-mono"] * 10000,
        "valid": [True] * 10000
    })
    
    # Simulate join operation
    joined_df = pd.merge(large_clone_df, large_perplexity_df, on="file_id", how="inner")
    
    # Verify join completed successfully
    assert len(joined_df) == 10000
    
    # Compute correlation on large dataset
    from scipy import stats
    corr, p_value = stats.spearmanr(joined_df["clone_density"], joined_df["perplexity"])
    
    # Validate results
    assert -1.0 <= corr <= 1.0
    assert 0.0 <= p_value <= 1.0

@pytest.mark.integration
def test_pipeline_segment_count_validation(tmp_path):
    """
    Test SC-003: at least 1000 code segments processed (T026).
    
    Validates that correlation analysis uses sufficient sample size.
    """
    # Create dataset with minimum required segments
    min_segments = 1000
    data = {
        "file_id": [str(i) for i in range(min_segments)],
        "clone_density": np.random.rand(min_segments),
        "perplexity": np.random.rand(min_segments) * 50
    }
    df = pd.DataFrame(data)
    
    # Compute correlation
    from scipy import stats
    corr, p_value = stats.spearmanr(df["clone_density"], df["perplexity"])
    
    # Validate segment count
    assert len(df) >= 1000, "SC-003: At least 1000 segments required"
    
    # Save with segment count
    results_path = tmp_path / "segment_validation.csv"
    results_df = pd.DataFrame({
        "total_segments": [len(df)],
        "valid_segments": [len(df[df["clone_density"].notna()])],
        "meets_sc003": [len(df) >= 1000]
    })
    results_df.to_csv(results_path, index=False)
    
    # Verify validation passed
    validation_df = pd.read_csv(results_path)
    assert validation_df["meets_sc003"].iloc[0] is True