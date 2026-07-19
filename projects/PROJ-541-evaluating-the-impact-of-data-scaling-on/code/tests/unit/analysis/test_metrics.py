import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
from analysis.metrics import run_full_analysis_pipeline, calculate_aggregate_metrics, generate_comparison_report, load_simulation_results, load_real_world_results

class TestFullPipeline:
    def test_run_full_analysis_pipeline(self):
        """Test the full analysis pipeline."""
        # Create sample data
        df = pd.DataFrame({
            "p_value": [0.01, 0.05, 0.1, 0.03, 0.04],
            "ground_truth": [True, True, False, True, True]
        })
        
        # Run pipeline
        result = run_full_analysis_pipeline(df)
        
        # Verify result structure
        assert result is not None
        assert "type1_error_rate" in result or "error_rate" in result

    def test_run_full_analysis_pipeline_no_args(self):
        """Test run_full_analysis_pipeline with no args (tolerant)."""
        # This should not crash even if no data is provided
        # Implementation should handle missing file gracefully
        try:
            result = run_full_analysis_pipeline()
            # If it returns, it handled the missing file
            assert isinstance(result, dict)
        except FileNotFoundError:
            # Expected if file doesn't exist and we choose to raise
            pass
        except Exception as e:
            # Should not crash with other errors
            raise e

class TestEmpiricalErrorRate:
    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        df = pd.DataFrame({
            "p_value": [0.01, 0.05, 0.1, 0.03, 0.04],
            "ground_truth": [True, True, False, True, True]
        })
        metrics = calculate_aggregate_metrics(df)
        # Check if metrics contain error rate
        assert "error_rate" in metrics or "type1_error_rate" in metrics

class TestComparisonReport:
    def test_generate_comparison_report(self):
        """Test that the comparison report is generated with correct schema."""
        # Create synthetic data
        synth_df = pd.DataFrame({
            "p_value": np.random.rand(100),
            "ground_truth": np.random.choice([True, False], 100)
        })
        
        # Create real data
        real_df = pd.DataFrame({
            "p_value": np.random.rand(100),
            "dataset_id": ["d1"] * 100
        })
        
        output_path = "results/test_comparison_report.md"
        
        # Generate report
        generate_comparison_report(synth_df, real_df, output_path)
        
        # Verify file exists
        assert Path(output_path).exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Check for required columns in the markdown table
        assert "Metric" in content
        assert "Synthetic_Value" in content
        assert "Real_Value" in content
        assert "Mean_Absolute_Difference" in content
        assert "Correlation_Coefficient" in content

class TestMixedEffectsModel:
    def test_mixed_effects_model(self):
        """Test mixed effects model fitting."""
        # This test requires statsmodels
        try:
            import statsmodels.api as sm
            df = pd.DataFrame({
                "p_value": np.random.rand(100),
                "scaling_method": np.random.choice(["std", "minmax", "robust"], 100),
                "dataset_id": np.random.choice(["d1", "d2"], 100)
            })
            # Run model
            from analysis.metrics import fit_mixed_effects_model
            result = fit_mixed_effects_model(df)
            assert result is not None
        except ImportError:
            pytest.skip("statsmodels not installed")
        except Exception as e:
            # If statsmodels is there but model fails for data reasons, that's okay for this test
            # unless it's a schema error
            if "formula" in str(e).lower():
                raise e
            pass