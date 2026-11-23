"""
Unit tests for T029c: Literature Search Power Analysis.
"""
import os
import sys
import json
import pytest
from pathlib import Path
import shutil
import tempfile

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.literature_search_power_analysis import (
    calculate_min_sample_size,
    load_current_power_analysis,
    retrieve_literature_estimates,
    update_power_analysis_file,
    METRICS_DIR
)

class TestLiteratureSearchPowerAnalysis:
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for testing if needed, or use the real one if isolated
        # For safety, we will mock the file operations or use a temp dir
        self.temp_dir = tempfile.mkdtemp()
        self.test_metrics_dir = Path(self.temp_dir) / "metrics"
        self.test_metrics_dir.mkdir()
        self.test_power_path = self.test_metrics_dir / "power_analysis.json"
        
        yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir)

    def test_calculate_min_sample_size(self):
        """Test the sample size calculation formula."""
        # Variance=1.0, Effect=0.2 should yield approx 600+ samples
        # Formula: 2 * ((1.96 + 0.84)^2) * (1.0 / 0.04) = 2 * 7.84 * 25 = 392
        # Wait, (0.2)^2 = 0.04. 1/0.04 = 25. 2 * 7.84 * 25 = 392.
        n = calculate_min_sample_size(1.0, 0.2)
        assert n > 0
        assert isinstance(n, int)
        
        # Higher effect size should reduce sample size
        n_high_effect = calculate_min_sample_size(1.0, 0.5)
        assert n_high_effect < n

    def test_retrieve_literature_estimates(self):
        """Test that literature estimates are retrieved and are valid."""
        estimates = retrieve_literature_estimates()
        
        assert estimates is not None
        assert "variance" in estimates
        assert "effect_size" in estimates
        assert "source" in estimates
        
        assert isinstance(estimates["variance"], (int, float))
        assert isinstance(estimates["effect_size"], (int, float))
        
        # Values should be positive
        assert estimates["variance"] > 0
        assert estimates["effect_size"] > 0

    def test_update_power_analysis_file(self):
        """Test that the file is updated correctly."""
        # Mock the path to use temp dir
        import data.literature_search_power_analysis as module
        original_path = module.POWER_ANALYSIS_PATH
        module.POWER_ANALYSIS_PATH = self.test_power_path
        
        try:
            estimates = {
                "variance": 0.5,
                "effect_size": 0.4,
                "source": "Test Source",
                "confidence": "high"
            }
            
            update_power_analysis_file(estimates)
            
            assert self.test_power_path.exists()
            
            with open(self.test_power_path, 'r') as f:
                data = json.load(f)
            
            assert data["expected_variance"] == 0.5
            assert data["effect_size"] == 0.4
            assert data["source"] == "Test Source"
            assert "min_sample_size" in data
            assert data["min_sample_size"] > 0
            
        finally:
            # Restore original path
            module.POWER_ANALYSIS_PATH = original_path

    def test_load_current_power_analysis_missing(self):
        """Test loading when file is missing."""
        # Ensure file doesn't exist in temp dir
        if self.test_power_path.exists():
            self.test_power_path.unlink()
            
        import data.literature_search_power_analysis as module
        original_path = module.POWER_ANALYSIS_PATH
        module.POWER_ANALYSIS_PATH = self.test_power_path
        
        try:
            data = load_current_power_analysis()
            assert data["expected_variance"] == 1.0 # Default
            assert data["effect_size"] == 0.2 # Default
            assert data["source"] == "conservative_defaults"
        finally:
            module.POWER_ANALYSIS_PATH = original_path