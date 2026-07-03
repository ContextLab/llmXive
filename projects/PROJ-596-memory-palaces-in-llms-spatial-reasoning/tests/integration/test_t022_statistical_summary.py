import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.stats import calculate_cohens_d, holm_bonferroni_correction
from evaluation.statistical_summary import generate_statistical_summary

class TestT022StatisticalSummary:
    """
    Integration test for T022: Generate statistical summary report.
    
    This test verifies that:
    1. The script can read simulated accuracy data (since we can't run full training in unit tests).
    2. The statistical calculations (t-test, Cohen's d, correction) are performed correctly.
    3. The output JSON file is created with the correct structure.
    """

    def setup_method(self):
        """Setup temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir) / "artifacts" / "results"
        self.artifacts_dir.mkdir(parents=True)
        
        # Mock data for baseline and spatial models across 3 datasets
        self.baseline_data = {
            "babi": [0.80, 0.82, 0.79, 0.81, 0.83],
            "lambada": [0.65, 0.67, 0.64, 0.66, 0.68],
            "story_cloze": [0.72, 0.74, 0.71, 0.73, 0.75]
        }
        
        self.spatial_data = {
            "babi": [0.85, 0.87, 0.84, 0.86, 0.88], # Higher
            "lambada": [0.66, 0.68, 0.65, 0.67, 0.69], # Slightly higher
            "story_cloze": [0.72, 0.74, 0.71, 0.73, 0.75] # Same
        }

        # Write mock data to expected files
        with open(self.artifacts_dir / "baseline_accuracies.json", 'w') as f:
            json.dump(self.baseline_data, f)
        
        with open(self.artifacts_dir / "spatial_accuracies.json", 'w') as f:
            json.dump(self.spatial_data, f)

        # Patch the ARTIFACTS_DIR in the module
        import evaluation.statistical_summary as ss_module
        self.original_artifacts_dir = ss_module.ARTIFACTS_DIR
        ss_module.ARTIFACTS_DIR = self.artifacts_dir
        ss_module.RAW_RESULTS_DIR = self.artifacts_dir

    def teardown_method(self):
        """Cleanup temporary directory."""
        import shutil
        import evaluation.statistical_summary as ss_module
        ss_module.ARTIFACTS_DIR = self.original_artifacts_dir
        shutil.rmtree(self.temp_dir)

    def test_statistical_summary_generation(self):
        """Test that the summary is generated with correct keys and values."""
        result = generate_statistical_summary()
        
        output_file = self.artifacts_dir / "statistical_summary.json"
        assert output_file.exists(), "statistical_summary.json was not created"
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check top-level keys
        assert "datasets" in data
        assert "correction_method" in data
        assert data["correction_method"] == "holm_bonferroni"
        
        # Check dataset entries
        for ds in ["babi", "lambada", "story_cloze"]:
            assert ds in data["datasets"], f"Missing dataset {ds}"
            
            entry = data["datasets"][ds]
            
            # Check required keys
            required_keys = [
                "baseline_mean", "spatial_mean", "t_statistic", "p_value",
                "cohens_d", "cohens_d_ci_95", "p_value_corrected", "significance_corrected"
            ]
            for key in required_keys:
                assert key in entry, f"Missing key {key} in {ds}"
            
            # Validate types
            assert isinstance(entry["baseline_mean"], float)
            assert isinstance(entry["p_value"], float)
            assert isinstance(entry["cohens_d"], float)
            assert isinstance(entry["cohens_d_ci_95"], list)
            assert len(entry["cohens_d_ci_95"]) == 2
            
            # Validate logic: if spatial > baseline, Cohen's d should be positive
            if entry["spatial_mean"] > entry["baseline_mean"]:
                assert entry["cohens_d"] > 0, f"Cohen's d should be positive for {ds}"
            
            # Validate significance logic
            if entry["p_value_corrected"] < 0.05:
                assert entry["significance_corrected"] is True
            else:
                assert entry["significance_corrected"] is False

    def test_cohen_d_calculation(self):
        """Verify Cohen's d calculation logic."""
        # Use the same data as setup
        baseline = self.baseline_data["babi"]
        spatial = self.spatial_data["babi"]
        
        d = calculate_cohens_d(baseline, spatial)
        
        # Manually calculate expected d for sanity check
        # d = (mean2 - mean1) / pooled_std
        import numpy as np
        mean1, mean2 = np.mean(baseline), np.mean(spatial)
        std1, std2 = np.std(baseline, ddof=1), np.std(spatial, ddof=1)
        n1, n2 = len(baseline), len(spatial)
        
        # Pooled std dev
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        expected_d = (mean2 - mean1) / pooled_std
        
        assert abs(d - expected_d) < 1e-6, f"Cohen's d mismatch: {d} vs {expected_d}"

    def test_holm_bonferroni_correction(self):
        """Verify Holm-Bonferroni correction logic."""
        p_values = [0.01, 0.04, 0.06]
        corrected = holm_bonferroni_correction(p_values)
        
        # Sorted p-values: 0.01, 0.04, 0.06
        # m=3
        # 1: 0.01 * 3 = 0.03
        # 2: 0.04 * 2 = 0.08
        # 3: 0.06 * 1 = 0.06
        # Max cumulative: 
        # i=0: 0.03
        # i=1: max(0.03, 0.08) = 0.08
        # i=2: max(0.08, 0.06) = 0.08
        # Result: [0.03, 0.08, 0.08]
        
        expected = [0.03, 0.08, 0.08]
        
        for i, (c, e) in enumerate(zip(corrected, expected)):
            assert abs(c - e) < 1e-6, f"Correction mismatch at index {i}: {c} vs {e}"