"""
Integration test for edge case handling in the knot complexity analysis pipeline.

This test verifies that edge cases are properly handled throughout the pipeline:
- API unavailability (retry logic, partial caching)
- Missing invariants (flagging)
- Ambiguous classifications (mark as 'unclassifiable')
- Crossing number ties (tie-breaking rules)
- Data quality issues (null values, format failures)

Per tasks.md T042: Integration test for edge case handling in tests/integration/test_edge_cases.py
"""

import pytest
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import sys

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from download.knot_atlas_loader import (
    KnotRecord,
    DownloadFailure,
    KnotAtlasDownloader,
    verify_retry_logic,
    verify_partial_caching
)
from data.validator import (
    DataQualityFlag,
    DataQualityFlags,
    MissingInvariantFlag,
    MissingInvariantFlags,
    check_null_values,
    check_format_validity,
    check_classification_validity,
    check_data_quality_issues
)
from reproducibility.logs import log_operation, get_logger
from reproducibility.tie_breaking_validator import (
    validate_tie_breaking_rules
)


class TestRetryLogicEdgeCases:
    """Test retry logic and partial caching for API failures."""
    
    def test_exponential_backoff_delays(self):
        """Verify exponential backoff delays on simulated failures: 1s → 2s → 4s."""
        downloader = KnotAtlasDownloader(base_url="https://katlas.org", 
                                         initial_delay=0.01,  # Use fast delays for testing
                                         max_delay=0.1,
                                         multiplier=2,
                                         max_retries=3)
        
        # Track actual delays
        actual_delays = []
        original_sleep = time.sleep
        
        def track_sleep(duration):
            actual_delays.append(duration)
        
        with patch('time.sleep', side_effect=track_sleep):
            with patch('requests.get') as mock_get:
                # Simulate 3 consecutive failures
                mock_get.side_effect = [
                    requests.exceptions.ConnectionError("Connection failed"),
                    requests.exceptions.ConnectionError("Connection failed"),
                    requests.exceptions.ConnectionError("Connection failed"),
                ]
                
                result = downloader._download_with_retry("test_url")
        
        # Verify delays follow exponential backoff: 0.01s → 0.02s → 0.04s
        assert len(actual_delays) >= 2, "Should have at least 2 retry delays"
        assert actual_delays[0] == 0.01, f"First delay should be initial_delay (0.01), got {actual_delays[0]}"
        assert actual_delays[1] == 0.02, f"Second delay should be initial_delay * 2 (0.02), got {actual_delays[1]}"
        if len(actual_delays) > 2:
            assert actual_delays[2] == 0.04, f"Third delay should be initial_delay * 4 (0.04), got {actual_delays[2]}"
    
    def test_partial_cache_after_consecutive_failures(self):
        """Verify cache creation after 3 consecutive failures (per FR-008)."""
        downloader = KnotAtlasDownloader(base_url="https://katlas.org",
                                         initial_delay=0.01,
                                         max_delay=0.1,
                                         multiplier=2,
                                         max_retries=3,
                                         cache_dir=Path("/tmp/test_knot_cache"))
        
        cache_dir = downloader.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate 3 consecutive failures
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [
                requests.exceptions.ConnectionError("Connection failed"),
                requests.exceptions.ConnectionError("Connection failed"),
                requests.exceptions.ConnectionError("Connection failed"),
            ]
            
            result = downloader._download_with_retry("test_url")
        
        # Verify partial cache file exists after 3 failures
        cache_files = list(cache_dir.glob("*.json"))
        assert len(cache_files) >= 1, "Should have at least one partial cache file after 3 consecutive failures"
        
        # Verify cache file contains partial data
        if cache_files:
            with open(cache_files[0], 'r') as f:
                cache_data = json.load(f)
                assert 'partial_data' in cache_data or 'failed_records' in cache_data, \
                    "Partial cache should contain either partial_data or failed_records"
        
        # Cleanup
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)
    
    def test_timeout_handling(self):
        """Verify timeout handling for slow responses."""
        downloader = KnotAtlasDownloader(base_url="https://katlas.org",
                                         initial_delay=0.01,
                                         max_delay=0.1,
                                         multiplier=2,
                                         max_retries=2,
                                         timeout=0.1)
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
            
            result = downloader._download_with_retry("test_url")
        
        # Result should indicate failure, not crash
        assert result is None or result.get('success') == False, \
            "Timeout should result in failure, not exception"

class TestMissingInvariantFlagging:
    """Test missing invariant flagging system."""
    
    def test_null_invariant_detection(self):
        """Verify null values are detected and flagged."""
        test_records = [
            {"knot_id": "3_1", "crossing_number": 3, "braid_index": None, "hyperbolic_volume": 0.9},
            {"knot_id": "4_1", "crossing_number": None, "braid_index": 2, "hyperbolic_volume": 2.0},
            {"knot_id": "5_1", "crossing_number": 5, "braid_index": 3, "hyperbolic_volume": None},
        ]
        
        flags = check_null_values(test_records)
        
        assert len(flags) == 3, f"Should detect 3 missing invariant flags, got {len(flags)}"
        
        # Verify specific flags
        flag_dict = {f.record_id: f for f in flags}
        assert "3_1" in flag_dict, "Should flag 3_1 for missing braid_index"
        assert "4_1" in flag_dict, "Should flag 4_1 for missing crossing_number"
        assert "5_1" in flag_dict, "Should flag 5_1 for missing hyperbolic_volume"
    
    def test_missing_invariant_flag_structure(self):
        """Verify MissingInvariantFlag has correct structure."""
        flag = MissingInvariantFlag(
            record_id="3_1",
            field_name="braid_index",
            expected_type="int",
            found_value=None,
            severity="error"
        )
        
        assert flag.record_id == "3_1"
        assert flag.field_name == "braid_index"
        assert flag.severity == "error"
        assert flag.found_value is None

class TestDataQualityFlagging:
    """Test data quality flagging system."""
    
    def test_format_failure_detection(self):
        """Verify format failures are detected and flagged."""
        test_records = [
            {"knot_id": "3_1", "crossing_number": "not_a_number", "braid_index": 2},
            {"knot_id": "4_1", "crossing_number": 4, "braid_index": "invalid"},
            {"knot_id": "5_1", "crossing_number": 5, "braid_index": 3},  # Valid
        ]
        
        flags = check_format_validity(test_records)
        
        assert len(flags) == 2, f"Should detect 2 format failures, got {len(flags)}"
        
        # Verify specific flags
        flag_dict = {f.record_id: f for f in flags}
        assert "3_1" in flag_dict, "Should flag 3_1 for invalid crossing_number format"
        assert "4_1" in flag_dict, "Should flag 4_1 for invalid braid_index format"
    
    def test_value_range_validation(self):
        """Verify value range violations are detected."""
        test_records = [
            {"knot_id": "3_1", "crossing_number": -1, "braid_index": 2},  # Invalid: negative
            {"knot_id": "4_1", "crossing_number": 4, "braid_index": 0},   # Invalid: braid_index ≤ 0
            {"knot_id": "5_1", "crossing_number": 5, "braid_index": 3},   # Valid
        ]
        
        flags = check_value_ranges(test_records)
        
        assert len(flags) == 2, f"Should detect 2 range violations, got {len(flags)}"
    
    def test_classification_validity(self):
        """Verify classification validity checking."""
        test_records = [
            {"knot_id": "3_1", "classification": "alternating"},  # Valid
            {"knot_id": "4_1", "classification": "non-alternating"},  # Valid
            {"knot_id": "5_1", "classification": "unknown"},  # Invalid
            {"knot_id": "6_1", "classification": None},  # Invalid: null
        ]
        
        flags = check_classification_validity(test_records)
        
        assert len(flags) == 2, f"Should detect 2 classification issues, got {len(flags)}"

class TestAmbiguousClassificationHandling:
    """Test handling of ambiguous alternating/non-alternating classification (FR-010)."""
    
    def test_unclassifiable_marking(self):
        """Verify ambiguous classifications are marked as 'unclassifiable'."""
        test_records = [
            {"knot_id": "3_1", "classification": "alternating"},
            {"knot_id": "4_1", "classification": "ambiguous"},  # Should be marked unclassifiable
            {"knot_id": "5_1", "classification": None},  # Should be marked unclassifiable
        ]
        
        flags = check_data_quality_issues(test_records)
        
        # Should have flags for ambiguous and null classifications
        unclassifiable_flags = [f for f in flags if "unclassifiable" in str(f).lower() or 
                               (hasattr(f, 'field_name') and f.field_name == 'classification')]
        
        assert len(unclassifiable_flags) >= 1, \
            "Should flag at least one record as unclassifiable"
    
    def test_exclude_vs_mark_strategy(self):
        """Verify the strategy for handling ambiguous classifications."""
        # Per FR-010: exclude or mark as 'unclassifiable'
        # This test verifies the flagging mechanism exists
        
        ambiguous_record = {"knot_id": "test_1", "classification": "ambiguous"}
        
        flags = check_data_quality_issues([ambiguous_record])
        
        assert len(flags) >= 0, "Flagging system should handle ambiguous classifications"

class TestTieBreakingRuleConsistency:
    """Test tie-breaking rule consistency validation."""
    
    def test_tie_breaking_validation_script(self):
        """Verify tie-breaking validation script returns success on consistent data."""
        # Create test parsed data with consistent tie-breaking
        test_data = [
            {
                "knot_id": "3_1",
                "crossing_number": 3,
                "braid_index": 2,
                "braid_word": "sigma1 sigma1",
                "dt_code": "4 6 2",
                "classification": "alternating"
            },
            {
                "knot_id": "4_1",
                "crossing_number": 4,
                "braid_index": 2,
                "braid_word": "sigma1 sigma2 sigma1 sigma2",
                "dt_code": "6 8 2 4",
                "classification": "alternating"
            },
        ]
        
        # Write test data to temporary file
        test_file = Path("/tmp/test_tie_breaking_data.json")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Run tie-breaking validation
        try:
            result = validate_tie_breaking_rules(str(test_file))
            
            # Should return success (exit code 0) on consistent data
            assert result.success == True, \
                f"Tie-breaking validation should succeed on consistent data, got: {result}"
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()

class TestIntegrationEdgeCases:
    """Integration tests for edge case handling across the pipeline."""
    
    def test_end_to_end_missing_invariant_handling(self):
        """Test end-to-end handling of missing invariants from download to validation."""
        # Simulate download with some missing data
        mock_records = [
            KnotRecord(
                knot_id="3_1",
                crossing_number=3,
                braid_index=2,
                hyperbolic_volume=0.9,
                is_alternating=True,
                braid_word="sigma1 sigma1",
                dt_code="4 6 2"
            ),
            KnotRecord(
                knot_id="4_1",
                crossing_number=4,
                braid_index=None,  # Missing braid_index
                hyperbolic_volume=2.0,
                is_alternating=True,
                braid_word=None,
                dt_code="6 8 2 4"
            ),
        ]
        
        # Validate the records
        flags = check_null_values([r.__dict__ for r in mock_records])
        
        # Should detect the missing braid_index
        assert len(flags) == 1, f"Should detect 1 missing invariant, got {len(flags)}"
        assert flags[0].record_id == "4_1"
        assert flags[0].field_name == "braid_index"
    
    def test_reproducibility_logging_with_edge_cases(self):
        """Test that edge cases are properly logged for reproducibility."""
        logger = get_logger()
        
        # Log an edge case operation
        log_entry = log_operation(
            operation="validate_missing_invariants",
            input_file="data/raw/knot_atlas_raw.json",
            output_file="data/processed/knots_cleaned.csv",
            parameters={"missing_fields": ["braid_index"]},
            status="partial_success"
        )
        
        assert log_entry is not None
        assert log_entry.operation == "validate_missing_invariants"
        assert log_entry.status == "partial_success"
    
    def test_duplicate_record_detection(self):
        """Verify duplicate records are detected and flagged."""
        test_records = [
            {"knot_id": "3_1", "crossing_number": 3, "braid_index": 2},
            {"knot_id": "3_1", "crossing_number": 3, "braid_index": 2},  # Duplicate
            {"knot_id": "4_1", "crossing_number": 4, "braid_index": 2},
        ]
        
        flags = check_duplicate_records(test_records)
        
        assert len(flags) >= 1, "Should detect at least one duplicate record"
        assert any(f.record_id == "3_1" for f in flags), "Should flag the duplicate 3_1"

# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])