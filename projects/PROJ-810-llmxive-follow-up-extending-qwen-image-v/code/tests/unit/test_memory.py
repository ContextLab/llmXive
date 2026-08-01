import json
import os
import tempfile
from pathlib import Path
import pytest
from src.utils.memory import (
    estimate_peak_ram_usage,
    calculate_max_samples,
    determine_chunk_size,
    estimate_runtime,
    run_runtime_fallback_logic
)

class TestMemoryUtils:
    def test_estimate_peak_ram_usage(self):
        """Test RAM estimation for different sample sizes."""
        # Small sample
        ram_small = estimate_peak_ram_usage(100)
        assert ram_small > 0
        assert ram_small < 5  # Should be reasonable for small N
        
        # Larger sample
        ram_large = estimate_peak_ram_usage(10000)
        assert ram_large > ram_small
        
    def test_calculate_max_samples(self):
        """Test max sample calculation."""
        max_samples = calculate_max_samples(7.0)
        assert max_samples >= 100
        assert max_samples > 0
        
        # Test with different RAM limits
        max_samples_4gb = calculate_max_samples(4.0)
        assert max_samples_4gb < max_samples
        
    def test_determine_chunk_size(self):
        """Test chunk size determination."""
        # Small dataset should use all samples
        chunk_small = determine_chunk_size(100, 7.0)
        assert chunk_small == 100
        
        # Large dataset should be chunked
        chunk_large = determine_chunk_size(100000, 7.0)
        assert chunk_large < 100000
        assert chunk_large >= 100
        
    def test_estimate_runtime(self):
        """Test runtime estimation."""
        runtime_0 = estimate_runtime(0)
        assert runtime_0 > 0  # Base overhead
        
        runtime_100 = estimate_runtime(100)
        assert runtime_100 > runtime_0
        
        runtime_1000 = estimate_runtime(1000)
        assert runtime_1000 > runtime_100
        
    def test_run_runtime_fallback_logic_pass(self, tmp_path):
        """Test runtime fallback when N fits within 6h."""
        # Create mock power analysis file
        power_data = {
            "N_required": 5000,
            "effect_size": 0.8,
            "power": 0.8,
            "N_audit": 50
        }
        power_file = tmp_path / "power_analysis.json"
        with open(power_file, 'w') as f:
            json.dump(power_data, f)
        
        output_file = tmp_path / "runtime_fallback.json"
        
        result = run_runtime_fallback_logic(str(power_file), str(output_file))
        
        assert result["status"] == "PASS"
        assert result["N_final"] == 5000
        assert not result["runtime_inconclusive"]
        assert result["estimated_runtime_hours"] < 6.0
        
        # Verify file was written
        assert output_file.exists()
        with open(output_file, 'r') as f:
            written_data = json.load(f)
        assert written_data["status"] == "PASS"
        
    def test_run_runtime_fallback_logic_inconclusive(self, tmp_path):
        """Test runtime fallback when N exceeds 6h."""
        # Create mock power analysis with very large N
        power_data = {
            "N_required": 1000000,  # Very large, should exceed 6h
            "effect_size": 0.8,
            "power": 0.8,
            "N_audit": 50
        }
        power_file = tmp_path / "power_analysis.json"
        with open(power_file, 'w') as f:
            json.dump(power_data, f)
        
        output_file = tmp_path / "runtime_fallback.json"
        
        result = run_runtime_fallback_logic(str(power_file), str(output_file))
        
        assert result["status"] == "INCONCLUSIVE"
        assert result["runtime_inconclusive"] is True
        assert result["N_final"] < power_data["N_required"]
        assert result["estimated_runtime_hours"] <= 6.0
        assert "limitation_text" in result
        assert result["limitation_text"] is not None
        
        # Verify file was written
        assert output_file.exists()
        
    def test_run_runtime_fallback_logic_missing_file(self, tmp_path):
        """Test error handling for missing power analysis file."""
        output_file = tmp_path / "runtime_fallback.json"
        
        with pytest.raises(FileNotFoundError):
            run_runtime_fallback_logic("/nonexistent/path.json", str(output_file))
        
    def test_run_runtime_fallback_logic_missing_n_required(self, tmp_path):
        """Test error handling for missing N_required in power analysis."""
        power_data = {
            "effect_size": 0.8,
            "power": 0.8
            # Missing N_required
        }
        power_file = tmp_path / "power_analysis.json"
        with open(power_file, 'w') as f:
            json.dump(power_data, f)
        
        output_file = tmp_path / "runtime_fallback.json"
        
        with pytest.raises(ValueError):
            run_runtime_fallback_logic(str(power_file), str(output_file))