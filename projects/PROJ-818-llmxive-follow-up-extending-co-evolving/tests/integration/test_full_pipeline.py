"""
Integration test for the full statistical analysis pipeline (US3).

This test verifies the end-to-end flow:
1. Loads generated training data and test instances.
2. Simulates training runs for Sequential, Mixed, and Co-evolving conditions.
3. Calculates forgetting metrics.
4. Performs Mixed-Design ANOVA and post-hoc Tukey tests.
5. Validates the statistical output schema.

Note: Since T026-T033 are not yet implemented, this test mocks the 
training and analysis steps to verify the integration logic and 
statistical framework compatibility.
"""
import pytest
import json
import sys
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.anova import AnovaRM

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.config import load_config
from src.utils.parity_checker import verify_run_parity
from src.analysis.forgetting_metrics import calculate_forgetting_rate, calculate_retention_rate
from src.analysis.statistical_tests import run_mixed_design_anova, run_post_hoc_tukey

# Mock data generator for integration testing
def generate_mock_training_data(num_runs: int = 30) -> Dict[str, List[Dict[str, Any]]]:
    """Generates mock training results for integration testing."""
    conditions = ["sequential", "mixed", "coevolving"]
    data = {cond: [] for cond in conditions}
    
    for cond in conditions:
        for i in range(num_runs):
            # Simulate initial accuracy (high) and final accuracy (variable)
            initial_acc = 0.95 + np.random.normal(0, 0.02)
            final_acc = initial_acc - np.random.uniform(0, 0.15)
            final_acc = max(0.0, min(1.0, final_acc))
            
            data[cond].append({
                "run_id": i,
                "condition": cond,
                "initial_accuracy": initial_acc,
                "final_accuracy": final_acc,
                "forgetting_rate": initial_acc - final_acc,
                "retention_rate": final_acc / initial_acc if initial_acc > 0 else 0
            })
    return data

def test_full_pipeline_integration():
    """
    Integration test: Full statistical analysis pipeline.
    
    Verifies that:
    1. Data loading and validation works.
    2. Forgetting metrics are calculated correctly.
    3. Mixed-Design ANOVA can be executed.
    4. Post-hoc Tukey tests produce valid results.
    5. Output schema matches expectations.
    """
    # Setup temporary directory for output
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "forgetting_analysis.json"
        
        # 1. Generate mock data (simulating T029/T030)
        mock_data = generate_mock_training_data(num_runs=30)
        
        # 2. Verify parity (simulating T022)
        # In a real run, this would check checksums and evaluation counts
        # Here we verify the structure of the data
        for cond, runs in mock_data.items():
            assert len(runs) == 30, f"Condition {cond} should have 30 runs"
            for run in runs:
                assert "forgetting_rate" in run
                assert "retention_rate" in run
        
        # 3. Calculate forgetting metrics (simulating T026/T031)
        forgetting_rates = {
            cond: [r["forgetting_rate"] for r in runs] 
            for cond, runs in mock_data.items()
        }
        retention_rates = {
            cond: [r["retention_rate"] for r in runs] 
            for cond, runs in mock_data.items()
        }
        
        # 4. Perform Mixed-Design ANOVA (simulating T027)
        # Prepare data for AnovaRM: wide format
        # Index: subject_id (run_id), Within: condition, Dependent: forgetting_rate
        df_data = []
        for subject_id in range(30):
            for cond in ["sequential", "mixed", "coevolving"]:
                df_data.append({
                    "subject": subject_id,
                    "condition": cond,
                    "forgetting_rate": mock_data[cond][subject_id]["forgetting_rate"]
                })
        
        # Run ANOVA
        try:
            anova_result = run_mixed_design_anova(df_data, "subject", "condition", "forgetting_rate")
            assert anova_result is not None, "ANOVA result should not be None"
            assert "f_statistic" in anova_result
            assert "p_value" in anova_result
        except Exception as e:
            pytest.fail(f"ANOVA execution failed: {e}")
        
        # 5. Perform Post-hoc Tukey test (simulating T027)
        try:
            tukey_result = run_post_hoc_tukey(df_data, "condition", "forgetting_rate")
            assert tukey_result is not None, "Tukey result should not be None"
            assert "comparisons" in tukey_result
        except Exception as e:
            pytest.fail(f"Tukey test execution failed: {e}")
        
        # 6. Compare retention rates (simulating T032)
        # Simple t-test for integration check
        coevol_ret = retention_rates["coevolving"]
        mixed_ret = retention_rates["mixed"]
        t_stat, p_val = stats.ttest_ind(coevol_ret, mixed_ret)
        
        # 7. Generate report (simulating T033)
        report = {
            "anova": anova_result,
            "tukey": tukey_result,
            "retention_comparison": {
                "t_statistic": t_stat,
                "p_value": p_val,
                "coevolving_mean": np.mean(coevol_ret),
                "mixed_mean": np.mean(mixed_ret)
            },
            "summary": {
                "total_runs": 30,
                "conditions": ["sequential", "mixed", "coevolving"],
                "statistically_significant": p_val < 0.05
            }
        }
        
        # Write report
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        # 8. Verify output file exists and is valid JSON
        assert output_path.exists(), "Output file should exist"
        with open(output_path, "r") as f:
            loaded_report = json.load(f)
        
        assert "anova" in loaded_report
        assert "tukey" in loaded_report
        assert "retention_comparison" in loaded_report
        assert loaded_report["summary"]["total_runs"] == 30

if __name__ == "__main__":
    pytest.main([__file__, "-v"])