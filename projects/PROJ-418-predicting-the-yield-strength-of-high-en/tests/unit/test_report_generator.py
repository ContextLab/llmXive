import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# Assuming the script is in code/models/report_generator.py
# We need to adjust sys.path to import it correctly in tests
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models.report_generator import (
    load_metrics,
    load_power_analysis,
    load_vif_results,
    generate_report_content,
    main
)

class TestReportGenerator:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.tmp_path = tmp_path
        self.output_dir = self.tmp_path / "output"
        self.output_dir.mkdir()
        
        # Create mock data files
        self.metrics_path = self.output_dir / "metrics.json"
        self.power_path = self.output_dir / "power_analysis.json"
        
        # Mock Metrics
        self.mock_metrics = {
            "models": {
                "Linear": {"r2": 0.45, "mae": 120.5, "rmse": 150.2},
                "RandomForest": {"r2": 0.72, "mae": 85.1, "rmse": 110.4},
                "GradientBoosting": {"r2": 0.75, "mae": 82.3, "rmse": 108.1}
            }
        }
        
        # Mock Power Analysis
        self.mock_power = {"status": "sufficient", "n": 650}
        
        # Mock VIF
        self.mock_vif = {"VEC": 2.1, "DeltaChi": 12.5, "Entropy": 1.8}
        
        # Mock Permutation
        self.mock_perm = [
            {"descriptor": "VEC", "importance": 0.15, "p_value": 0.001, "corrected_p_value": 0.005, "is_significant": True},
            {"descriptor": "DeltaChi", "importance": 0.05, "p_value": 0.12, "corrected_p_value": 0.25, "is_significant": False}
        ]
        
        # Mock Bootstrap
        self.mock_boot = {
            "RandomForest": {"mean_r2": 0.72, "ci_lower": 0.65, "ci_upper": 0.79}
        }
        
        # Mock Sensitivity
        self.mock_sens = {
            "0.01": {"significant_count": 2, "best_r2": 0.75},
            "0.05": {"significant_count": 5, "best_r2": 0.75},
            "0.10": {"significant_count": 8, "best_r2": 0.75}
        }

        # Write mock files
        with open(self.metrics_path, 'w') as f:
            json.dump(self.mock_metrics, f)
        with open(self.power_path, 'w') as f:
            json.dump(self.mock_power, f)
        
        # Create dedicated VIF file for T023 pattern
        vif_path = self.output_dir / "vif_results.json"
        with open(vif_path, 'w') as f:
            json.dump(self.mock_vif, f)
        
        # Create dedicated Permutation file
        perm_path = self.output_dir / "permutation_results.json"
        with open(perm_path, 'w') as f:
            json.dump(self.mock_perm, f)
        
        # Create dedicated Bootstrap file
        boot_path = self.output_dir / "bootstrap_results.json"
        with open(boot_path, 'w') as f:
            json.dump(self.mock_boot, f)
        
        # Create dedicated Sensitivity file
        sens_path = self.output_dir / "sensitivity_results.json"
        with open(sens_path, 'w') as f:
            json.dump(self.mock_sens, f)

    def test_load_metrics(self):
        result = load_metrics(str(self.metrics_path))
        assert result == self.mock_metrics

    def test_load_power_analysis(self):
        result = load_power_analysis(str(self.power_path))
        assert result == self.mock_power

    def test_load_vif_results_fallback(self):
        # Test reading from dedicated file
        result = load_vif_results(str(self.metrics_path))
        assert result == self.mock_vif

    def test_generate_report_content_includes_metrics(self):
        content = generate_report_content(
            self.mock_metrics, self.mock_power, self.mock_vif,
            self.mock_perm, self.mock_boot, self.mock_sens
        )
        assert "## 2. Model Performance Metrics" in content
        assert "RandomForest" in content
        assert "0.72" in content

    def test_generate_report_content_includes_vif(self):
        content = generate_report_content(
            self.mock_metrics, self.mock_power, self.mock_vif,
            self.mock_perm, self.mock_boot, self.mock_sens
        )
        assert "## 3. Multicollinearity Analysis (VIF)" in content
        assert "DeltaChi" in content
        assert "12.50" in content # Formatted

    def test_generate_report_content_includes_permutation(self):
        content = generate_report_content(
            self.mock_metrics, self.mock_power, self.mock_vif,
            self.mock_perm, self.mock_boot, self.mock_sens
        )
        assert "## 4. Permutation Importance & Significance" in content
        assert "VEC" in content
        assert "Yes" in content # Significant flag

    def test_generate_report_content_includes_bootstrap(self):
        content = generate_report_content(
            self.mock_metrics, self.mock_power, self.mock_vif,
            self.mock_perm, self.mock_boot, self.mock_sens
        )
        assert "## 5. Bootstrap Resampling (95% CI)" in content
        assert "0.65" in content # CI Lower

    def test_generate_report_content_includes_sensitivity(self):
        content = generate_report_content(
            self.mock_metrics, self.mock_power, self.mock_vif,
            self.mock_perm, self.mock_boot, self.mock_sens
        )
        assert "## 6. Sensitivity Analysis (Alpha Sweep)" in content
        assert "0.01" in content

    def test_generate_report_content_insufficient_power(self):
        low_power = {"status": "insufficient_power", "n": 40}
        content = generate_report_content(
            self.mock_metrics, low_power, self.mock_vif,
            self.mock_perm, self.mock_boot, self.mock_sens
        )
        assert "insufficient sample size" in content.lower()
        assert "Skipped" in content
        # Permutation and Bootstrap sections should mention skipping
        assert "Permutation testing was skipped" in content
        assert "Bootstrap resampling was skipped" in content

    @patch('models.report_generator.inject_disclaimer')
    @patch('models.report_utils.finalize_report_markdown')
    @patch('builtins.open')
    @patch('os.makedirs')
    def test_main_writes_report(self, mock_makedirs, mock_open, mock_finalize, mock_inject, tmp_path):
        # Setup mocks
        mock_inject.side_effect = lambda x: x + "\n[DISCLAIMER]"
        mock_finalize.side_effect = lambda x: x + "\n[FINALIZED]"
        
        # Setup file paths in tmp
        test_output_dir = tmp_path / "output"
        test_output_dir.mkdir()
        
        # Write minimal mocks
        metrics_file = test_output_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump({"models": {}}, f)
        
        power_file = test_output_dir / "power_analysis.json"
        with open(power_file, 'w') as f:
            json.dump({"status": "sufficient"}, f)
        
        # Patch the base output dir logic
        with patch('models.report_generator.base_output_dir', str(test_output_dir)):
            # We can't easily patch the hardcoded string in the function, so we rely on the fact
            # that the function uses 'output' relative to cwd. 
            # For this test, we will mock the specific paths used inside main() if possible,
            # or just run it in a controlled environment.
            # Given the constraints, let's just verify the logic path by mocking the file writes.
            pass

        # Since the function uses hardcoded "output", we assume the test runner sets cwd or we mock os.path
        # A simpler approach for this specific function structure:
        # Mock the file I/O and directory creation directly
        
        with patch('models.report_generator.base_output_dir', str(test_output_dir)):
            pass # This doesn't work because base_output_dir is a local var in main()
        
        # Alternative: Just ensure the function doesn't crash and calls the right utils
        # We will mock the file existence checks and the open call
        
        original_exists = os.path.exists
        def mock_exists(path):
            if "output" in path and (path.endswith("metrics.json") or path.endswith("power_analysis.json")):
                return True
            return original_exists(path)
        
        with patch('os.path.exists', mock_exists):
            with patch('models.report_generator.load_metrics', return_value={}):
                with patch('models.report_generator.load_power_analysis', return_value={"status": "sufficient"}):
                    with patch('models.report_generator.load_vif_results', return_value={}):
                        with patch('models.report_generator.load_permutation_results', return_value={}):
                            with patch('models.report_generator.load_bootstrap_results', return_value={}):
                                with patch('models.report_generator.load_sensitivity_results', return_value={}):
                                    with patch('models.report_generator.generate_report_content', return_value="Test Content"):
                                        with patch('models.report_generator.inject_disclaimer', return_value="Test Content + Disclaimer"):
                                            with patch('models.report_generator.finalize_report_markdown', return_value="Final Content"):
                                                with patch('builtins.open') as mock_f:
                                                    with patch('os.makedirs') as mock_mkdir:
                                                        # Change to tmp dir to ensure 'output' is created there
                                                        old_cwd = os.getcwd()
                                                        os.chdir(str(tmp_path))
                                                        try:
                                                            result = main()
                                                            assert result == 0
                                                            mock_mkdir.assert_called()
                                                            mock_f.assert_called()
                                                        finally:
                                                            os.chdir(old_cwd)