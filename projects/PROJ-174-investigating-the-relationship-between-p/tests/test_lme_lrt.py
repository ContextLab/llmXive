import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add code to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.lme_model import (
    perform_likelihood_ratio_test,
    extract_model_summary,
    parse_dropped_predictor,
    run_lme_part3_lrt_and_output
)
import statsmodels.formula.api as smf

class TestLME_LRT:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        # Setup temporary directories for test artifacts
        self.original_cwd = os.getcwd()
        self.temp_dir = tmp_path
        os.chdir(self.temp_dir)
        
        # Create necessary directories
        Path("data/processed").mkdir(parents=True)
        Path("results").mkdir(parents=True)
        
        # Create a mock features.csv
        np.random.seed(42)
        n = 100
        data = {
            'subject': np.repeat(['S1', 'S2', 'S3'], n//3),
            'search_time': np.random.rand(n) * 10,
            'fixation_count': np.random.randint(1, 10, n),
            'target_salience': np.random.rand(n),
            'pupil_mean': np.random.rand(n) * 5
        }
        df = pd.DataFrame(data)
        df.to_csv("data/processed/features.csv", index=False)
        
        # Create a mock vif_report.log (no drop)
        with open("results/vif_report.log", "w") as f:
            f.write("VIF Check: All predictors < 5. No drop.")
        
        yield
        
        # Teardown
        os.chdir(self.original_cwd)
        # shutil.rmtree(self.temp_dir) # Optional: keep for debugging

    def test_parse_dropped_predictor_no_drop(self):
        report = "VIF Check: All predictors < 5. No drop."
        assert parse_dropped_predictor(report) is None

    def test_parse_dropped_predictor_with_drop(self):
        report = "INFO: DROPPING PREDICTOR: target_salience due to VIF > 5"
        assert parse_dropped_predictor(report) == "target_salience"

    def test_perform_likelihood_ratio_test(self):
        # Create simple nested models
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.random.randn(n),
            'group': np.repeat(['A', 'B'], n//2)
        })
        
        # Full model: y ~ x1 + x2
        full = smf.mixedlm("y ~ x1 + x2", df, groups=df["group"]).fit()
        # Reduced model: y ~ x1
        reduced = smf.mixedlm("y ~ x1", df, groups=df["group"]).fit()
        
        lrt = perform_likelihood_ratio_test(full, reduced)
        
        assert "statistic" in lrt
        assert "p_value" in lrt
        assert "df" in lrt
        assert lrt["df"] == 1  # Difference in params (x2)
        assert lrt["statistic"] > 0
        assert 0 <= lrt["p_value"] <= 1

    def test_extract_model_summary(self):
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'group': np.repeat(['A', 'B'], n//2)
        })
        
        model = smf.mixedlm("y ~ x1", df, groups=df["group"]).fit()
        summary = extract_model_summary(model, "test")
        
        assert len(summary) > 0
        assert any(row["parameter"] == "x1" for row in summary)
        assert any(row["parameter"] == "Intercept" for row in summary)
        for row in summary:
            assert "estimate" in row
            assert "std_error" in row
            assert "p_value" in row

    def test_run_lme_part3_integration(self):
        # This tests the full flow with the mock data created in fixture
        # It should not crash and should produce results/model_summary.csv
        try:
            run_lme_part3_lrt_and_output()
            assert Path("results/model_summary.csv").exists()
            df_out = pd.read_csv("results/model_summary.csv")
            assert len(df_out) > 0
            assert "estimate" in df_out.columns
            assert "dropped_predictor" in df_out.columns
        except Exception as e:
            # If it fails due to data shape or specific statsmodels version issues, log but don't fail test if logic is sound
            pytest.fail(f"LME Part 3 execution failed: {e}")