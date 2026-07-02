"""
Unit tests for T016b: Fallback Pairing Analysis.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from code.fallback_pairing import (
    calculate_pairing_rates,
    load_pairing_log,
    run_fallback_pairing_analysis,
    LOGS_DIR,
    PAIRING_LOG_PATH,
    PAIRING_FALLBACK_LOG_PATH
)
from code.exceptions import E_PAIRING

class TestCalculatePairingRates:
    def test_sample_level_success(self):
        """Test when sample level pairing is high."""
        metadata = {
            "S1": {"condition": "Control"},
            "S2": {"condition": "Treatment"},
            "S3": {"condition": "Treatment"}
        }
        # Only S1 is mismatched (unmatched)
        mismatches = [{"sample_id": "S1"}]
        
        sample_rate, cond_rate, counts = calculate_pairing_rates(mismatches, metadata)
        
        # 2/3 matched
        assert sample_rate == pytest.approx(0.666, rel=0.01)
        assert cond_rate > 0.0 # Both conditions have at least one match
    
    def test_condition_aggregation(self):
        """Test condition level aggregation logic."""
        metadata = {
            "S1": {"condition": "Control"},
            "S2": {"condition": "Control"},
            "S3": {"condition": "Treatment"},
            "S4": {"condition": "Treatment"},
            "S5": {"condition": "Stress"}
        }
        # All Control matched, one Treatment matched, Stress unmatched
        mismatches = [
            {"sample_id": "S1"}, # Wait, let's say S1 is matched, S2 mismatched?
            # Let's define: S1, S3 matched. S2, S4, S5 mismatched.
        ]
        # Actually, let's just test the logic:
        # S1 (Control) matched
        # S2 (Control) mismatched
        # S3 (Treatment) matched
        # S4 (Treatment) mismatched
        # S5 (Stress) mismatched
        
        mismatches = [
            {"sample_id": "S2"},
            {"sample_id": "S4"},
            {"sample_id": "S5"}
        ]
        
        sample_rate, cond_rate, counts = calculate_pairing_rates(mismatches, metadata)
        
        # Sample: 2/5 matched = 0.4
        assert sample_rate == pytest.approx(0.4, rel=0.01)
        
        # Conditions:
        # Control: S1 matched -> count 1 -> included
        # Treatment: S3 matched -> count 1 -> included
        # Stress: S5 mismatched -> count 0 -> excluded
        # Total conditions included: 2
        assert len(counts) == 2
        assert counts.get("Control", 0) == 1
        assert counts.get("Treatment", 0) == 1

class TestRunFallbackPairingAnalysis:
    @pytest.fixture
    def temp_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_path = Path(tmpdir) / "logs"
            logs_path.mkdir()
            data_path = Path(tmpdir) / "data" / "raw"
            data_path.mkdir(parents=True)
            
            # Patch the global paths
            with patch('code.fallback_pairing.LOGS_DIR', logs_path):
                with patch('code.fallback_pairing.PAIRING_LOG_PATH', logs_path / "data_pairing.json"):
                    with patch('code.fallback_pairing.PAIRING_FALLBACK_LOG_PATH', logs_path / "pairing_fallback_summary.json"):
                        # Patch metadata loading to return specific test data
                        test_metadata = {
                            f"S{i}": {"condition": f"Cond{i % 10}"} for i in range(1, 35) # 34 samples, 10 conditions
                        }
                        with patch('code.fallback_pairing.load_sample_metadata', return_value=test_metadata):
                            yield logs_path

    def test_sample_level_pass(self, temp_dirs):
        """Test that it returns True if sample level is >= 95%."""
        # 34 samples, 0 mismatches -> 100%
        mismatches = []
        with open(temp_dirs / "data_pairing.json", 'w') as f:
            json.dump(mismatches, f)
        
        # Mock load_pairing_log to return empty
        with patch('code.fallback_pairing.load_pairing_log', return_value=[]):
            result = run_fallback_pairing_analysis()
            assert result is True

    def test_fallback_success(self, temp_dirs):
        """Test fallback when sample level < 95% but condition level n >= 28."""
        # Create 34 samples.
        # Make 20 mismatches. Sample rate = 14/34 = 41% (<95%)
        # Conditions: 34 samples distributed over 30 conditions (mostly 1 per condition)
        # If we have 30 conditions, and say 14 are matched, n=14 (<28) -> Fail
        # We need n >= 28.
        
        # Let's create 30 conditions, each with 2 samples (60 total).
        # Mismatch 30 samples (50% sample rate).
        # Match 30 samples (1 per condition).
        # Condition count = 30 (>=28). Should pass.
        
        test_metadata = {}
        for i in range(60):
            cond_name = f"Cond_{i//2}"
            test_metadata[f"S{i}"] = {"condition": cond_name}
        
        # Mismatches: S0, S2, S4... (even indices)
        mismatches = [{"sample_id": f"S{i}"} for i in range(0, 60, 2)]
        
        with open(temp_dirs / "data_pairing.json", 'w') as f:
            json.dump(mismatches, f)
        
        with patch('code.fallback_pairing.load_pairing_log', return_value=mismatches):
            with patch('code.fallback_pairing.load_sample_metadata', return_value=test_metadata):
                result = run_fallback_pairing_analysis()
                assert result is True
                # Check log file
                log_file = temp_dirs / "pairing_fallback_summary.json"
                assert log_file.exists()
                with open(log_file) as f:
                    log_data = json.load(f)
                    assert log_data["status"] == "SUCCESS"
                    assert log_data["n_conditional"] >= 28

    def test_fallback_fail(self, temp_dirs):
        """Test abort when condition level n < 28."""
        # 30 samples, 2 conditions.
        # Mismatch 10 samples. Match 20.
        # Sample rate = 20/30 = 66%
        # Condition count = 2 (since both conditions have matches)
        # n = 2 < 28 -> Fail
        
        test_metadata = {
            f"S{i}": {"condition": "A" if i < 15 else "B"} for i in range(30)
        }
        mismatches = [{"sample_id": f"S{i}"} for i in range(10)]
        
        with open(temp_dirs / "data_pairing.json", 'w') as f:
            json.dump(mismatches, f)
        
        with patch('code.fallback_pairing.load_pairing_log', return_value=mismatches):
            with patch('code.fallback_pairing.load_sample_metadata', return_value=test_metadata):
                with pytest.raises(E_PAIRING):
                    run_fallback_pairing_analysis()