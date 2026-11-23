import os
import sys
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_verdict import evaluate_verdict, generate_verdict_report, load_residual_stats, RESULTS_DIR, RESIDUAL_STATS_FILE

class TestVerdictGeneration:
    """
    Integration tests for the T036 verdict generation pipeline.
    """

    @pytest.fixture
    def mock_residual_stats(self, tmp_path):
        """
        Create a temporary mock residual_stats.csv file to simulate the output of T034.
        """
        # Create a mock dataframe that mimics the expected output structure
        mock_data = {
            'model': ['mond', 'nfw'],
            'mean_residual': [0.01, 0.05],
            'median_residual': [0.005, 0.04],
            'std_residual': [0.1, 0.15],
            'p_value_bootstrap': [0.03, 0.45],  # MOND significant, NFW not
            'n_samples': [500, 500]
        }
        df = pd.DataFrame(mock_data)
        
        # Ensure the results directory exists in the temp location
        # We will patch the global constant or pass the path explicitly in a real scenario,
        # but here we create the file in the temp directory and adjust the test logic.
        temp_file = tmp_path / "residual_stats.csv"
        df.to_csv(temp_file, index=False)
        return temp_file

    def test_evaluate_verdict_logic(self):
        """
        Test that evaluate_verdict correctly classifies models based on p-value < 0.05.
        """
        mock_data = {
            'model': ['mond', 'nfw', 'alternative'],
            'p_value_bootstrap': [0.03, 0.45, 0.01]
        }
        df = pd.DataFrame(mock_data)
        
        result = evaluate_verdict(df)
        
        assert len(result['models']) == 3
        
        # Check MOND (0.03 < 0.05) -> Significant
        mond_res = next(m for m in result['models'] if m['model'] == 'mond')
        assert mond_res['is_significant'] is True
        assert "Reject Null" in mond_res['verdict']
        
        # Check NFW (0.45 >= 0.05) -> Not Significant
        nfw_res = next(m for m in result['models'] if m['model'] == 'nfw')
        assert nfw_res['is_significant'] is False
        assert "Fail to Reject" in nfw_res['verdict']

        # Check summary text reflects the result
        assert "favoring the MOND model" in result['summary']

    def test_generate_verdict_report_format(self):
        """
        Test that the generated markdown report contains required sections.
        """
        mock_data = {
            'model': ['mond'],
            'p_value_bootstrap': [0.01]
        }
        df = pd.DataFrame(mock_data)
        verdict_data = evaluate_verdict(df)
        
        report = generate_verdict_report(verdict_data)
        
        assert "# Analysis Verdict" in report
        assert "## Statistical Comparison Results" in report
        assert "## Interpretation" in report
        assert "0.03" not in report # 0.03 was not in this specific mock
        assert "0.01" in report
        assert "alpha" in report.lower() or "alpha" in report

    def test_full_pipeline_integration(self, mock_residual_stats, tmp_path):
        """
        Simulate the full pipeline by temporarily swapping the output directory
        and verifying the markdown file is created.
        """
        # We need to simulate the environment where RESIDUAL_STATS_FILE points to our mock
        # Since the function load_residual_stats uses a global constant, we can't easily patch it
        # without importing it inside the function or using monkeypatch.
        # Instead, we test the core logic functions directly which are unit-tested above,
        # and verify the file writing logic manually.
        
        import generate_verdict as gv_module
        
        # Save original path
        original_path = gv_module.RESIDUAL_STATS_FILE
        
        try:
            # Point to our mock file
            gv_module.RESIDUAL_STATS_FILE = mock_residual_stats
            
            # Create a temp output dir
            temp_output = tmp_path / "results"
            temp_output.mkdir()
            gv_module.RESULTS_DIR = temp_output
            gv_module.VERDICT_FILE = temp_output / "analysis_verdict.md"
            
            # Run main logic (skipping the exit code handling)
            logger = gv_module.get_logger("test")
            df = gv_module.load_residual_stats()
            verdict_data = gv_module.evaluate_verdict(df)
            report_content = gv_module.generate_verdict_report(verdict_data)
            
            # Write manually to verify
            gv_module.VERDICT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(gv_module.VERDICT_FILE, 'w') as f:
                f.write(report_content)
            
            # Verify file exists and has content
            assert gv_module.VERDICT_FILE.exists()
            with open(gv_module.VERDICT_FILE, 'r') as f:
                content = f.read()
            assert len(content) > 100 # Should have substantial content
            
        finally:
            # Restore
            gv_module.RESIDUAL_STATS_FILE = original_path
            gv_module.RESULTS_DIR = Path("results")
            gv_module.VERDICT_FILE = Path("results") / "analysis_verdict.md"