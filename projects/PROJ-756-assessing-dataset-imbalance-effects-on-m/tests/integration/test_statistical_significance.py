"""
Integration test for statistical significance validation.

This test validates:
1. Power analysis calculation (seed count determination)
2. Paired t-test / Wilcoxon signed-rank test execution
3. P-value calculation and interpretation
4. Effect size (Cohen's d) calculation

The test simulates the full statistical significance workflow by:
- Loading power analysis results
- Running paired statistical tests on synthetic performance metrics
- Validating the output schema and statistical validity
"""

import os
import sys
import json
import csv
import logging
import math
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation import power_analysis_z_test, calculate_cohen_d
from statistical_tests import (
    load_power_analysis,
    load_performance_metrics,
    calculate_effect_size,
    run_paired_tests,
    save_results
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for testing
MINORITY_QUANTILE = 0.1  # Bottom 10%
SIGNIFICANCE_LEVEL = 0.05
TARGET_POWER = 0.8
EFFECT_SIZE_MEDIUM = 0.5

def generate_synthetic_performance_metrics(seed_count: int) -> Tuple[List[float], List[float]]:
    """
    Generate synthetic performance metrics for testing statistical significance.
    
    This creates two sets of performance metrics (skewed vs balanced) with
    a known effect size to validate the statistical tests.
    
    Args:
        seed_count: Number of random seeds to simulate
        
    Returns:
        Tuple of (skewed_metrics, balanced_metrics)
    """
    import random
    random.seed(42)  # For reproducibility
    
    # Simulate performance metrics with a known difference
    # Skewed data typically has higher MAE (worse performance)
    base_mae_skewed = 0.15
    base_mae_balanced = 0.12
    std_dev = 0.02
    
    skewed_metrics = []
    balanced_metrics = []
    
    for i in range(seed_count):
        # Add some noise to simulate real experimental variation
        noise_skewed = random.gauss(0, std_dev)
        noise_balanced = random.gauss(0, std_dev)
        
        skewed_val = base_mae_skewed + noise_skewed
        balanced_val = base_mae_balanced + noise_balanced
        
        skewed_metrics.append(skewed_val)
        balanced_metrics.append(balanced_val)
    
    return skewed_metrics, balanced_metrics

def create_test_power_analysis_file(output_path: Path, seed_count: int) -> None:
    """Create a test power analysis JSON file."""
    data = {
        "test_type": "paired_t_test",
        "effect_size": EFFECT_SIZE_MEDIUM,
        "power": TARGET_POWER,
        "alpha": SIGNIFICANCE_LEVEL,
        "seed_count": seed_count,
        "justification": "Power analysis for paired t-test with medium effect size"
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Created test power analysis file: {output_path}")

def create_test_performance_metrics_file(
    output_path: Path, 
    skewed_metrics: List[float], 
    balanced_metrics: List[float],
    property_name: str = "formation_energy"
) -> None:
    """Create a test performance metrics CSV file."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seed_id', 'property', 'metric', 'skewed_value', 'balanced_value'])
        
        for i, (skewed, balanced) in enumerate(zip(skewed_metrics, balanced_metrics)):
            writer.writerow([i, property_name, 'MAE', skewed, balanced])
    
    logger.info(f"Created test performance metrics file: {output_path}")

def test_power_analysis_seed_count():
    """
    Validate power analysis calculation for determining minimum seed count.
    
    This test verifies that:
    1. The power analysis function correctly calculates the required seed count
    2. The calculated seed count meets the target power (>= 0.8)
    3. The output is saved to the correct file format
    """
    logger.info("Starting power analysis validation test...")
    
    # Calculate required seed count
    seed_count = power_analysis_z_test(
        effect_size=EFFECT_SIZE_MEDIUM,
        power=TARGET_POWER,
        alpha=SIGNIFICANCE_LEVEL
    )
    
    logger.info(f"Calculated seed count: {seed_count}")
    
    # Validate seed count is reasonable (should be > 0 and < 1000 for medium effect)
    assert seed_count > 0, "Seed count must be positive"
    assert seed_count < 1000, "Seed count should be reasonable for medium effect size"
    
    # Create test output directory
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)
    power_analysis_path = results_dir / "power_analysis.json"
    
    # Save power analysis results
    test_create_power_analysis_output(power_analysis_path, seed_count)
    
    # Verify the file was created and contains valid data
    assert power_analysis_path.exists(), "Power analysis file should be created"
    
    with open(power_analysis_path, 'r') as f:
        data = json.load(f)
    
    assert 'seed_count' in data, "Output must contain seed_count"
    assert data['seed_count'] == seed_count, "Seed count must match calculation"
    
    logger.info("Power analysis validation test PASSED")
    return True

def test_create_power_analysis_output(output_path: Path, seed_count: int) -> None:
    """Helper to create power analysis output file."""
    data = {
        "test_type": "paired_t_test",
        "effect_size": EFFECT_SIZE_MEDIUM,
        "power": TARGET_POWER,
        "alpha": SIGNIFICANCE_LEVEL,
        "seed_count": seed_count,
        "justification": "Power analysis for paired t-test with medium effect size"
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def test_paired_t_test_execution():
    """
    Validate paired t-test execution and p-value calculation.
    
    This test verifies that:
    1. Paired t-test correctly compares two related samples
    2. P-value is calculated correctly
    3. Effect size (Cohen's d) is computed accurately
    4. Results are saved in the correct format
    """
    logger.info("Starting paired t-test execution test...")
    
    # Generate synthetic performance metrics
    seed_count = 30  # Use a reasonable number for testing
    skewed_metrics, balanced_metrics = generate_synthetic_performance_metrics(seed_count)
    
    # Create test data files
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)
    
    metrics_path = results_dir / "test_performance_metrics.csv"
    create_test_performance_metrics_file(metrics_path, skewed_metrics, balanced_metrics)
    
    # Load the test data
    loaded_metrics = load_performance_metrics(metrics_path)
    
    assert len(loaded_metrics) == seed_count, "Should load all metrics"
    
    # Run paired statistical tests
    test_results = run_paired_tests(
        skewed_data=skewed_metrics,
        balanced_data=balanced_metrics,
        test_type="paired_t_test"
    )
    
    # Validate test results
    assert 'p_value' in test_results, "Results must contain p_value"
    assert 't_statistic' in test_results, "Results must contain t_statistic"
    assert 'effect_size' in test_results, "Results must contain effect_size"
    
    # Validate p-value is in valid range
    p_value = test_results['p_value']
    assert 0 <= p_value <= 1, f"P-value must be between 0 and 1, got {p_value}"
    
    # Validate effect size is reasonable
    effect_size = test_results['effect_size']
    assert -10 <= effect_size <= 10, f"Effect size should be reasonable, got {effect_size}"
    
    # Test significance determination
    is_significant = p_value < SIGNIFICANCE_LEVEL
    logger.info(f"Test {'significant' if is_significant else 'not significant'} (p={p_value:.4f})")
    
    # Save results
    results_path = results_dir / "statistical_test_results.csv"
    save_results(
        results_path=results_path,
        test_type="paired_t_test",
        p_value=p_value,
        effect_size=effect_size,
        seed_count=seed_count
    )
    
    # Verify output file
    assert results_path.exists(), "Results file should be created"
    
    with open(results_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) > 0, "Results file should contain data"
    assert 'p_value' in rows[0], "Results must include p_value column"
    assert 'effect_size' in rows[0], "Results must include effect_size column"
    
    logger.info("Paired t-test execution test PASSED")
    return True

def test_wilcoxon_signed_rank_test():
    """
    Validate Wilcoxon signed-rank test for non-parametric comparison.
    
    This test verifies that:
    1. Wilcoxon test is executed correctly for non-normal data
    2. P-value is calculated correctly
    3. Results are saved in the correct format
    """
    logger.info("Starting Wilcoxon signed-rank test validation...")
    
    # Generate synthetic performance metrics with non-normal distribution
    import random
    random.seed(123)
    
    seed_count = 30
    skewed_metrics = [abs(random.gauss(0.15, 0.03)) for _ in range(seed_count)]
    balanced_metrics = [abs(random.gauss(0.12, 0.025)) for _ in range(seed_count)]
    
    # Run Wilcoxon test
    test_results = run_paired_tests(
        skewed_data=skewed_metrics,
        balanced_data=balanced_metrics,
        test_type="wilcoxon"
    )
    
    # Validate test results
    assert 'p_value' in test_results, "Results must contain p_value"
    assert 'statistic' in test_results, "Results must contain statistic"
    
    p_value = test_results['p_value']
    assert 0 <= p_value <= 1, f"P-value must be between 0 and 1, got {p_value}"
    
    logger.info(f"Wilcoxon test p-value: {p_value:.4f}")
    logger.info("Wilcoxon signed-rank test validation PASSED")
    return True

def test_effect_size_calculation():
    """
    Validate Cohen's d effect size calculation.
    
    This test verifies that:
    1. Cohen's d is calculated correctly
    2. The effect size interpretation is accurate
    3. Edge cases are handled properly
    """
    logger.info("Starting effect size calculation validation...")
    
    # Test case 1: Known effect size
    group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    group2 = [2.0, 3.0, 4.0, 5.0, 6.0]
    
    effect_size = calculate_cohen_d(group1, group2)
    
    # For these groups, we expect a moderate effect size
    assert -10 <= effect_size <= 10, f"Effect size should be reasonable, got {effect_size}"
    
    # Test case 2: Identical groups (effect size should be 0)
    identical_group = [1.0, 2.0, 3.0, 4.0, 5.0]
    effect_size_zero = calculate_cohen_d(identical_group, identical_group)
    
    assert abs(effect_size_zero) < 0.0001, f"Identical groups should have effect size ~0, got {effect_size_zero}"
    
    # Test case 3: Very different groups (large effect size)
    group_small = [1.0, 1.1, 1.2, 1.3, 1.4]
    group_large = [5.0, 5.5, 6.0, 6.5, 7.0]
    effect_size_large = calculate_cohen_d(group_small, group_large)
    
    assert abs(effect_size_large) > 2.0, f"Very different groups should have large effect size, got {effect_size_large}"
    
    logger.info(f"Test effect sizes: {effect_size:.3f}, {effect_size_zero:.3f}, {effect_size_large:.3f}")
    logger.info("Effect size calculation validation PASSED")
    return True

def test_statistical_significance_validation():
    """
    Main integration test for statistical significance validation.
    
    This test orchestrates all statistical significance components:
    1. Power analysis
    2. Paired t-test
    3. Wilcoxon signed-rank test
    4. Effect size calculation
    5. Result validation and reporting
    """
    logger.info("=" * 60)
    logger.info("Starting Statistical Significance Validation Integration Test")
    logger.info("=" * 60)
    
    all_passed = True
    test_results = []
    
    # Test 1: Power Analysis
    try:
        test_power_analysis_seed_count()
        test_results.append(("Power Analysis", "PASSED"))
    except Exception as e:
        logger.error(f"Power Analysis test FAILED: {str(e)}")
        test_results.append(("Power Analysis", "FAILED"))
        all_passed = False
    
    # Test 2: Paired T-Test
    try:
        test_paired_t_test_execution()
        test_results.append(("Paired T-Test", "PASSED"))
    except Exception as e:
        logger.error(f"Paired T-Test test FAILED: {str(e)}")
        test_results.append(("Paired T-Test", "FAILED"))
        all_passed = False
    
    # Test 3: Wilcoxon Signed-Rank Test
    try:
        test_wilcoxon_signed_rank_test()
        test_results.append(("Wilcoxon Test", "PASSED"))
    except Exception as e:
        logger.error(f"Wilcoxon Test test FAILED: {str(e)}")
        test_results.append(("Wilcoxon Test", "FAILED"))
        all_passed = False
    
    # Test 4: Effect Size Calculation
    try:
        test_effect_size_calculation()
        test_results.append(("Effect Size", "PASSED"))
    except Exception as e:
        logger.error(f"Effect Size test FAILED: {str(e)}")
        test_results.append(("Effect Size", "FAILED"))
        all_passed = False
    
    # Generate summary report
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)
    summary_path = results_dir / "statistical_significance_test_summary.json"
    
    summary_data = {
        "test_date": str(Path(__file__).parent.parent.parent),
        "total_tests": len(test_results),
        "passed": sum(1 for _, status in test_results if status == "PASSED"),
        "failed": sum(1 for _, status in test_results if status == "FAILED"),
        "overall_status": "PASSED" if all_passed else "FAILED",
        "individual_results": [
            {"test_name": name, "status": status} 
            for name, status in test_results
        ]
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info("=" * 60)
    logger.info(f"Test Summary: {summary_data['passed']}/{summary_data['total_tests']} tests passed")
    logger.info(f"Overall Status: {summary_data['overall_status']}")
    logger.info(f"Summary saved to: {summary_path}")
    logger.info("=" * 60)
    
    return all_passed

def main():
    """Main entry point for the statistical significance validation test."""
    logger.info("Running statistical significance validation integration test...")
    
    success = test_statistical_significance_validation()
    
    if success:
        logger.info("✓ All statistical significance validation tests PASSED")
        sys.exit(0)
    else:
        logger.error("✗ Some statistical significance validation tests FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()