import os
import sys
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.update_power_analysis_with_literature import (
    load_json_file,
    update_power_analysis_with_literature,
    save_power_analysis
)

class TestUpdatePowerAnalysisWithLiterature:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_load_json_file_success(self, temp_dir):
        """Test loading a valid JSON file."""
        test_data = {"key": "value", "number": 42}
        file_path = temp_dir / "test.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(file_path)
        assert result == test_data
    
    def test_load_json_file_not_found(self, temp_dir):
        """Test loading a non-existent JSON file raises FileNotFoundError."""
        file_path = temp_dir / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_json_file(file_path)
    
    def test_update_power_analysis_with_variance(self):
        """Test updating power analysis with variance from literature."""
        current = {
            "expected_variance": 1.5,
            "effect_size": 0.5,
            "recommended_sample_size": 100,
            "variance_source": "theoretical"
        }
        literature = {
            "variance": 2.0,
            "effect_size": 0.5,
            "source": "arXiv:1234.5678"
        }
        
        result = update_power_analysis_with_literature(current, literature)
        
        assert result["expected_variance"] == 2.0
        assert result["variance_source"] == "empirical_literature"
        assert result["effect_size"] == 0.5  # Unchanged
        assert "recalculation_reason" in result
    
    def test_update_power_analysis_with_effect_size(self):
        """Test updating power analysis with effect size from literature."""
        current = {
            "expected_variance": 1.0,
            "effect_size": 0.3,
            "recommended_sample_size": 200
        }
        literature = {
            "variance": 1.0,
            "effect_size": 0.6,
            "source": "IEEE Xplore"
        }
        
        result = update_power_analysis_with_literature(current, literature)
        
        assert result["effect_size"] == 0.6
        assert result["expected_variance"] == 1.0  # Unchanged
        assert "recalculation_reason" in result
    
    def test_update_power_analysis_with_both(self):
        """Test updating power analysis with both variance and effect size."""
        current = {
            "expected_variance": 1.0,
            "effect_size": 0.5,
            "recommended_sample_size": 150,
            "variance_source": "theoretical"
        }
        literature = {
            "variance": 2.0,
            "effect_size": 0.8,
            "source": "Google Scholar"
        }
        
        result = update_power_analysis_with_literature(current, literature)
        
        assert result["expected_variance"] == 2.0
        assert result["effect_size"] == 0.8
        assert result["variance_source"] == "empirical_literature"
        assert result["recommended_sample_size"] != 150  # Should be recalculated
    
    def test_update_power_analysis_with_zero_effect_size(self):
        """Test behavior when literature effect size is zero."""
        current = {
            "expected_variance": 1.0,
            "effect_size": 0.5,
            "recommended_sample_size": 100
        }
        literature = {
            "variance": 1.5,
            "effect_size": 0.0,
            "source": "Test Source"
        }
        
        result = update_power_analysis_with_literature(current, literature)
        
        assert result["expected_variance"] == 1.5
        assert result["effect_size"] == 0.0
        # Sample size should not be recalculated if effect_size is zero
        assert "recalculation_reason" not in result or result.get("recalculation_reason") is None
    
    def test_save_power_analysis(self, temp_dir):
        """Test saving power analysis to a JSON file."""
        data = {
            "expected_variance": 1.5,
            "effect_size": 0.6,
            "recommended_sample_size": 250,
            "last_updated": "literature_update"
        }
        file_path = temp_dir / "output.json"
        
        save_power_analysis(data, file_path)
        
        assert file_path.exists()
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == data