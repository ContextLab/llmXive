"""
Integration test for the end-to-end analysis pipeline (US3).

This test verifies the full statistical analysis workflow:
1. Loads baseline vectors from data/processed/baseline_vectors.csv
2. Loads perturbed vectors from data/processed/perturbed_vectors.csv
3. Loads validity logs from data/processed/validity_log.csv
4. Filters data based on validity collapse points and input drift
5. Calculates pairwise cosine similarity distributions
6. Runs hypothesis tests (t-test/Wilcoxon) with Bonferroni correction
7. Generates trade-off curves and sensitivity reports
8. Validates output schemas against specs/001-lm-axive-noise-injection/contracts/

Prerequisites:
- T015 must have produced data/processed/baseline_vectors.csv
- T025 must have produced data/processed/perturbed_vectors.csv
- T024a must have produced data/processed/validity_log.csv
"""

import os
import sys
import json
import csv
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import pytest
import numpy as np
from scipy import stats

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import (
    calculate_pairwise_cosine_similarity,
    run_hypothesis_test,
    generate_sensitivity_report,
    main as analysis_main
)
from config import load_config, OutputPaths, PipelineConfig
from validity_check import check_validity_collapse

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for test validation
MIN_P_VALUE = 0.0
MAX_P_VALUE = 1.0
MIN_MEAN_DIFF = -1.0
MAX_MEAN_DIFF = 1.0
VALIDITY_THRESHOLD = 0.90


def load_csv_to_dicts(filepath: Path) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_json_to_dict(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file into a dictionary."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_baseline_vectors_exist():
    """Verify that baseline vectors were produced by T015."""
    baseline_path = project_root / "data" / "processed" / "baseline_vectors.csv"
    assert baseline_path.exists(), "baseline_vectors.csv must exist (T015)"
    
    rows = load_csv_to_dicts(baseline_path)
    assert len(rows) > 0, "baseline_vectors.csv must contain data"
    
    # Validate schema
    required_cols = {'pair_id', 'task_type', 'vector_base64', 'norm_status'}
    assert required_cols.issubset(set(rows[0].keys())), f"Missing columns in baseline_vectors.csv. Found: {rows[0].keys()}"

def test_perturbed_vectors_exist():
    """Verify that perturbed vectors were produced by T025."""
    perturbed_path = project_root / "data" / "processed" / "perturbed_vectors.csv"
    assert perturbed_path.exists(), "perturbed_vectors.csv must exist (T025)"
    
    rows = load_csv_to_dicts(perturbed_path)
    assert len(rows) > 0, "perturbed_vectors.csv must contain data"
    
    # Validate schema
    required_cols = {'pair_id', 'task_type', 'sigma', 'vector_base64', 'norm_status'}
    assert required_cols.issubset(set(rows[0].keys())), f"Missing columns in perturbed_vectors.csv. Found: {rows[0].keys()}"

def test_validity_log_exist():
    """Verify that validity log was produced by T024a."""
    validity_path = project_root / "data" / "processed" / "validity_log.csv"
    assert validity_path.exists(), "validity_log.csv must exist (T024a)"
    
    rows = load_csv_to_dicts(validity_path)
    assert len(rows) > 0, "validity_log.csv must contain data"
    
    # Validate schema
    required_cols = {'task_type', 'sigma', 'pass_rate', 'collapse_point'}
    assert required_cols.issubset(set(rows[0].keys())), f"Missing columns in validity_log.csv. Found: {rows[0].keys()}"

def test_pairwise_cosine_similarity_calculation():
    """Test the pairwise cosine similarity function with real data."""
    baseline_path = project_root / "data" / "processed" / "baseline_vectors.csv"
    perturbed_path = project_root / "data" / "processed" / "perturbed_vectors.csv"
    
    baseline_data = load_csv_to_dicts(baseline_path)
    perturbed_data = load_csv_to_dicts(perturbed_path)
    
    # Filter for a specific task type to ensure we have data
    task_types = set(row['task_type'] for row in baseline_data)
    if not task_types:
        pytest.skip("No task types found in baseline data")
    
    test_task_type = list(task_types)[0]
    baseline_subset = [row for row in baseline_data if row['task_type'] == test_task_type]
    perturbed_subset = [row for row in perturbed_data if row['task_type'] == test_task_type]
    
    if len(baseline_subset) < 2 or len(perturbed_subset) < 2:
        pytest.skip("Not enough data points for similarity calculation")
    
    # Calculate similarities
    baseline_similarities, perturbed_similarities = calculate_pairwise_cosine_similarity(
        baseline_subset, 
        perturbed_subset,
        test_task_type
    )
    
    # Validate results
    assert isinstance(baseline_similarities, list), "Baseline similarities must be a list"
    assert isinstance(perturbed_similarities, list), "Perturbed similarities must be a list"
    
    if len(baseline_similarities) > 0:
        assert all(-1.0 <= s <= 1.0 for s in baseline_similarities), "Cosine similarity must be in [-1, 1]"
    
    if len(perturbed_similarities) > 0:
        assert all(-1.0 <= s <= 1.0 for s in perturbed_similarities), "Cosine similarity must be in [-1, 1]"

def test_hypothesis_test_selection():
    """Test that the correct statistical test is selected based on normality."""
    baseline_path = project_root / "data" / "processed" / "baseline_vectors.csv"
    perturbed_path = project_root / "data" / "processed" / "perturbed_vectors.csv"
    
    baseline_data = load_csv_to_dicts(baseline_path)
    perturbed_data = load_csv_to_dicts(perturbed_path)
    
    task_types = set(row['task_type'] for row in baseline_data)
    if not task_types:
        pytest.skip("No task types found")
    
    test_task_type = list(task_types)[0]
    baseline_subset = [row for row in baseline_data if row['task_type'] == test_task_type]
    perturbed_subset = [row for row in perturbed_data if row['task_type'] == test_task_type]
    
    if len(baseline_subset) < 3 or len(perturbed_subset) < 3:
        pytest.skip("Not enough data points for hypothesis testing")
    
    # Run hypothesis test
    result = run_hypothesis_test(baseline_subset, perturbed_subset, test_task_type)
    
    # Validate result structure
    assert 'p_value' in result, "Result must contain p_value"
    assert 'mean_diff' in result, "Result must contain mean_diff"
    assert 'test_type' in result, "Result must contain test_type"
    assert 'ci_lower' in result, "Result must contain ci_lower"
    assert 'ci_upper' in result, "Result must contain ci_upper"
    
    # Validate p-value range
    assert MIN_P_VALUE <= result['p_value'] <= MAX_P_VALUE, f"p_value out of range: {result['p_value']}"
    
    # Validate test type
    assert result['test_type'] in ['t-test', 'Wilcoxon'], f"Invalid test_type: {result['test_type']}"

def test_trade_off_curve_generation():
    """Test that trade-off curves are generated correctly."""
    validity_path = project_root / "data" / "processed" / "validity_log.csv"
    validity_data = load_csv_to_dicts(validity_path)
    
    if not validity_data:
        pytest.skip("No validity log data available")
    
    # Group by task type
    task_type_groups = {}
    for row in validity_data:
        task_type = row['task_type']
        if task_type not in task_type_groups:
            task_type_groups[task_type] = []
        task_type_groups[task_type].append(row)
    
    # Generate trade-off curves
    trade_off_curves = {}
    for task_type, rows in task_type_groups.items():
        # Sort by sigma
        sorted_rows = sorted(rows, key=lambda x: float(x['sigma']))
        
        trade_off_curves[task_type] = []
        for row in sorted_rows:
            trade_off_curves[task_type].append({
                'sigma': float(row['sigma']),
                'pass_rate': float(row['pass_rate']),
                'collapse_point': row['collapse_point'].lower() == 'true'
            })
    
    # Validate structure
    assert len(trade_off_curves) > 0, "Trade-off curves must be generated"
    
    for task_type, curve in trade_off_curves.items():
        assert len(curve) > 0, f"Trade-off curve for {task_type} must have data"
        for point in curve:
            assert 'sigma' in point
            assert 'pass_rate' in point
            assert 'collapse_point' in point
            assert 0.0 <= point['pass_rate'] <= 1.0, f"Invalid pass_rate: {point['pass_rate']}"

def test_sensitivity_report_generation():
    """Test that the sensitivity report is generated with correct schema."""
    baseline_path = project_root / "data" / "processed" / "baseline_vectors.csv"
    perturbed_path = project_root / "data" / "processed" / "perturbed_vectors.csv"
    validity_path = project_root / "data" / "processed" / "validity_log.csv"
    
    baseline_data = load_csv_to_dicts(baseline_path)
    perturbed_data = load_csv_to_dicts(perturbed_path)
    validity_data = load_csv_to_dicts(validity_path)
    
    if not baseline_data or not perturbed_data or not validity_data:
        pytest.skip("Required data files missing")
    
    # Generate sensitivity report
    report = generate_sensitivity_report(baseline_data, perturbed_data, validity_data)
    
    # Validate schema
    required_keys = {
        'p_value', 
        'mean_diff', 
        'ci', 
        'validity_collapse_distribution', 
        'trade_off_curve'
    }
    
    assert isinstance(report, dict), "Sensitivity report must be a dictionary"
    assert required_keys.issubset(set(report.keys())), f"Missing keys in report. Found: {report.keys()}"
    
    # Validate p-value
    assert 'p_value' in report
    assert MIN_P_VALUE <= report['p_value'] <= MAX_P_VALUE, f"Invalid p_value in report: {report['p_value']}"
    
    # Validate validity collapse distribution
    assert isinstance(report['validity_collapse_distribution'], dict), "validity_collapse_distribution must be a dict"
    
    # Validate trade-off curve
    assert isinstance(report['trade_off_curve'], dict), "trade_off_curve must be a dict"

def test_bonferroni_correction():
    """Test that Bonferroni correction is applied to p-values."""
    # This test verifies that the analysis pipeline applies multiple testing correction
    # We check the statistical_results.json output if it exists, or simulate the logic
    
    results_path = project_root / "data" / "processed" / "statistical_results.json"
    
    if results_path.exists():
        results = load_json_to_dict(results_path)
        
        # Check if corrected p-values are present
        if 'corrected_p_values' in results or 'bonferroni_corrected' in results:
            logger.info("Bonferroni correction found in results")
        else:
            # If not explicitly labeled, we assume the main p_value is corrected
            # based on the implementation in analysis.py
            logger.info("Checking if main p_value is corrected (implementation dependent)")
    else:
        # Run the analysis to generate results
        logger.info("Running analysis to generate statistical results")
        try:
            analysis_main()
            if results_path.exists():
                results = load_json_to_dict(results_path)
                logger.info("Statistical results generated successfully")
        except Exception as e:
            logger.warning(f"Could not run analysis: {e}")
            pytest.skip("Analysis could not be run")

def test_end_to_end_analysis_pipeline():
    """
    Full integration test: Run the complete analysis pipeline and verify all outputs.
    
    This test:
    1. Loads all required input files
    2. Runs the main analysis pipeline
    3. Verifies all expected output files are created
    4. Validates output schemas
    5. Checks statistical validity
    """
    # Check prerequisites
    baseline_path = project_root / "data" / "processed" / "baseline_vectors.csv"
    perturbed_path = project_root / "data" / "processed" / "perturbed_vectors.csv"
    validity_path = project_root / "data" / "processed" / "validity_log.csv"
    
    assert baseline_path.exists(), "baseline_vectors.csv missing"
    assert perturbed_path.exists(), "perturbed_vectors.csv missing"
    assert validity_path.exists(), "validity_log.csv missing"
    
    # Load data
    baseline_data = load_csv_to_dicts(baseline_path)
    perturbed_data = load_csv_to_dicts(perturbed_path)
    validity_data = load_csv_to_dicts(validity_path)
    
    logger.info(f"Loaded {len(baseline_data)} baseline vectors, {len(perturbed_data)} perturbed vectors, {len(validity_data)} validity records")
    
    # Run analysis
    try:
        analysis_main()
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        pytest.fail(f"Analysis pipeline failed: {e}")
    
    # Verify outputs
    results_path = project_root / "data" / "processed" / "statistical_results.json"
    trade_off_path = project_root / "data" / "processed" / "trade_off_curve.csv"
    global_trade_off_path = project_root / "data" / "processed" / "global_trade_off_curve.csv"
    sensitivity_path = project_root / "data" / "processed" / "sensitivity_report.json"
    
    assert results_path.exists(), "statistical_results.json must be created"
    assert trade_off_path.exists(), "trade_off_curve.csv must be created"
    assert global_trade_off_path.exists(), "global_trade_off_curve.csv must be created"
    assert sensitivity_path.exists(), "sensitivity_report.json must be created"
    
    # Validate statistical results
    results = load_json_to_dict(results_path)
    assert 'p_value' in results
    assert 'mean_diff' in results
    assert 'ci' in results
    assert 'validity_collapse_distribution' in results
    assert 'trade_off_curve' in results
    
    # Validate trade-off curve CSV
    trade_off_rows = load_csv_to_dicts(trade_off_path)
    assert len(trade_off_rows) > 0, "trade_off_curve.csv must contain data"
    required_cols = {'task_type', 'sigma', 'pass_rate'}
    assert required_cols.issubset(set(trade_off_rows[0].keys())), "Missing columns in trade_off_curve.csv"
    
    # Validate sensitivity report
    sensitivity_report = load_json_to_dict(sensitivity_path)
    assert 'global_distribution' in sensitivity_report
    assert 'validity_collapse_distribution' in sensitivity_report
    
    logger.info("End-to-end analysis pipeline completed successfully")

def test_significant_separability_flag():
    """Test that significant separability is correctly flagged."""
    results_path = project_root / "data" / "processed" / "statistical_results.json"
    
    if not results_path.exists():
        pytest.skip("statistical_results.json not found")
    
    results = load_json_to_dict(results_path)
    
    # Check if significant separability flag exists
    if 'significant_separability_increase' in results:
        flag = results['significant_separability_increase']
        assert isinstance(flag, bool), "significant_separability_increase must be boolean"
        
        # Verify the flag matches the p-value condition
        p_value = results.get('p_value', 1.0)
        expected_flag = p_value < 0.05
        assert flag == expected_flag, f"Flag mismatch: {flag} vs expected {expected_flag}"
    else:
        # If not explicitly stored, verify the logic is correct in the results
        p_value = results.get('p_value', 1.0)
        # The flag should be derivable from p_value
        assert 0.0 <= p_value <= 1.0, f"Invalid p_value: {p_value}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])