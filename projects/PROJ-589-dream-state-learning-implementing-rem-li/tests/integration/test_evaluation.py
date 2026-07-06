"""
Integration test for User Story 2: Comparative Evaluation Baseline.

This test compares two dummy models (Experimental vs Baseline) to verify
the statistical comparison pipeline (Wilcoxon signed-rank test) works correctly.

It does NOT train real models (too expensive for integration test). Instead,
it simulates the *output* of the evaluation phase (accuracy scores) for
multiple seeds to test the statistical analysis logic end-to-end.

Prerequisites:
- T020 (Unit test for wilcoxon_test) must pass.
- code/eval/metrics.py must implement wilcoxon_test.
"""

import pytest
import numpy as np
from pathlib import Path
import json

# Ensure we can import from the code directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from eval.metrics import wilcoxon_test
from utils.logger import get_logger

# Setup logger for integration test
logger = get_logger("test_evaluation_integration")

class DummyModelExperimental:
    """
    Simulates the Experimental model (Dream-State Learning).
    Returns a list of accuracy scores across seeds.
    In a real scenario, this would run the full training loop.
    """
    def __init__(self, seed_base=42):
        self.seed_base = seed_base
        # Simulate slightly higher accuracy with some variance
        # Mean ~0.85, Std ~0.02
        np.random.seed(seed_base)
        self.scores = np.random.normal(0.85, 0.02, 5).tolist()
        # Clamp to [0, 1]
        self.scores = [max(0.0, min(1.0, s)) for s in self.scores]

    def run_evaluation(self, num_seeds=5):
        logger.info(f"Running experimental model evaluation for {num_seeds} seeds...")
        # In a real implementation, this would loop over seeds, train, eval.
        # Here we return pre-generated dummy scores that represent the outcome.
        return self.scores

class DummyModelBaseline:
    """
    Simulates the Baseline model (Continuous SFT).
    Returns a list of accuracy scores across seeds.
    In a real scenario, this would run continuous training.
    """
    def __init__(self, seed_base=42):
        self.seed_base = seed_base
        # Simulate slightly lower accuracy with some variance
        # Mean ~0.82, Std ~0.02
        np.random.seed(seed_base)
        self.scores = np.random.normal(0.82, 0.02, 5).tolist()
        # Clamp to [0, 1]
        self.scores = [max(0.0, min(1.0, s)) for s in self.scores]

    def run_evaluation(self, num_seeds=5):
        logger.info(f"Running baseline model evaluation for {num_seeds} seeds...")
        return self.scores

def test_comparative_evaluation_pipeline():
    """
    Integration test:
    1. Instantiate Experimental and Baseline dummy models.
    2. Run evaluation (simulated) to get accuracy lists.
    3. Perform statistical comparison (Wilcoxon).
    4. Verify the result structure and that the test runs without error.
    5. (Optional) Write results to data/results/ for verification.
    """
    logger.info("Starting comparative evaluation integration test...")
    
    # 1. Setup models
    exp_model = DummyModelExperimental(seed_base=12345)
    base_model = DummyModelBaseline(seed_base=12345)
    
    # 2. Run evaluations
    exp_scores = exp_model.run_evaluation(num_seeds=5)
    base_scores = base_model.run_evaluation(num_seeds=5)
    
    logger.info(f"Experimental scores: {exp_scores}")
    logger.info(f"Baseline scores: {base_scores}")
    
    # 3. Statistical comparison
    result = wilcoxon_test(exp_scores, base_scores, alternative='greater')
    
    logger.info(f"Statistical test result: {result}")
    
    # 4. Assertions
    assert result is not None, "wilcoxon_test returned None"
    assert 'statistic' in result, "Result missing 'statistic'"
    assert 'pvalue' in result, "Result missing 'pvalue'"
    assert isinstance(result['statistic'], (int, float)), "Statistic must be numeric"
    assert isinstance(result['pvalue'], (int, float)), "P-value must be numeric"
    
    # Verify p-value is in valid range [0, 1]
    assert 0.0 <= result['pvalue'] <= 1.0, f"P-value {result['pvalue']} out of range"
    
    # 5. Write results to data/results/ (as per T026 spec, though T026 is not done yet,
    #    we ensure the directory exists and we can write a file)
    results_dir = Path(__file__).parent.parent.parent / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = results_dir / "integration_test_comparison.json"
    report_data = {
        "experimental_scores": exp_scores,
        "baseline_scores": base_scores,
        "statistical_test": result,
        "method": "Wilcoxon signed-rank test",
        "alpha": 0.05
    }
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Comparison report written to {report_path}")
    
    # 6. Final check: Ensure the file exists and contains valid JSON
    assert report_path.exists(), "Report file was not created"
    with open(report_path, 'r') as f:
        loaded = json.load(f)
        assert loaded['statistical_test']['pvalue'] == result['pvalue']
    
    logger.info("Integration test PASSED.")

if __name__ == "__main__":
    test_comparative_evaluation_pipeline()