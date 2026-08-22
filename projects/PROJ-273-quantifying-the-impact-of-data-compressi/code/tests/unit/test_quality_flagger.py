"""
Unit tests for compression quality flagging (T023)
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.compression.quality_flagger import (
    flag_compression_quality,
    process_quality_flags_for_event,
    aggregate_quality_report,
    SNR_DEGRADATION_THRESHOLD
)


class TestFlagCompressionQuality:
    """Tests for the flag_compression_quality function"""

    def test_flag_acceptable_snr_degradation(self):
        """Test that SNR degradation below threshold is marked acceptable"""
        metrics_data = {
            "event_id": "test_event_001",
            "compression_results": [
                {
                    "method": "gzip",
                    "level": 9,
                    "snr_degradation_db": 2.5
                }
            ]
        }
        
        result = flag_compression_quality(metrics_data)
        
        assert len(result["quality_flags"]["acceptable_levels"]) == 1
        assert len(result["quality_flags"]["unacceptable_levels"]) == 0
        assert result["quality_flags"]["summary"]["acceptable"] == 1
        assert result["quality_flags"]["summary"]["unacceptable"] == 0

    def test_flag_unacceptable_snr_degradation(self):
        """Test that SNR degradation above threshold is marked unacceptable"""
        metrics_data = {
            "event_id": "test_event_001",
            "compression_results": [
                {
                    "method": "jpeg2000",
                    "level": "high",
                    "snr_degradation_db": 7.5
                }
            ]
        }
        
        result = flag_compression_quality(metrics_data)
        
        assert len(result["quality_flags"]["unacceptable_levels"]) == 1
        assert len(result["quality_flags"]["acceptable_levels"]) == 0
        assert result["quality_flags"]["summary"]["acceptable"] == 0
        assert result["quality_flags"]["summary"]["unacceptable"] == 1
        
        # Check the reason message
        unacceptable = result["quality_flags"]["unacceptable_levels"][0]
        assert unacceptable["reason"].startswith("SNR degradation")
        assert "exceeds threshold" in unacceptable["reason"]

    def test_flag_mixed_results(self):
        """Test flagging with a mix of acceptable and unacceptable results"""
        metrics_data = {
            "event_id": "test_event_002",
            "compression_results": [
                {"method": "gzip", "level": 1, "snr_degradation_db": 0.5},
                {"method": "gzip", "level": 9, "snr_degradation_db": 3.2},
                {"method": "jpeg2000", "level": "medium", "snr_degradation_db": 5.1},
                {"method": "wavelet", "level": "low", "snr_degradation_db": 4.9},
                {"method": "quantization", "level": 4, "snr_degradation_db": 8.0}
            ]
        }
        
        result = flag_compression_quality(metrics_data)
        
        assert result["quality_flags"]["summary"]["acceptable"] == 3
        assert result["quality_flags"]["summary"]["unacceptable"] == 2

    def test_flag_exact_threshold_boundary(self):
        """Test that exactly 5.0 dB is acceptable (not > 5.0)"""
        metrics_data = {
            "event_id": "test_event_003",
            "compression_results": [
                {"method": "test", "level": 1, "snr_degradation_db": 5.0}
            ]
        }
        
        result = flag_compression_quality(metrics_data)
        
        assert result["quality_flags"]["summary"]["acceptable"] == 1
        assert result["quality_flags"]["summary"]["unacceptable"] == 0

    def test_flag_just_above_threshold(self):
        """Test that 5.0001 dB is unacceptable"""
        metrics_data = {
            "event_id": "test_event_004",
            "compression_results": [
                {"method": "test", "level": 1, "snr_degradation_db": 5.0001}
            ]
        }
        
        result = flag_compression_quality(metrics_data)
        
        assert result["quality_flags"]["summary"]["acceptable"] == 0
        assert result["quality_flags"]["summary"]["unacceptable"] == 1

    def test_custom_threshold(self):
        """Test using a custom threshold value"""
        metrics_data = {
            "event_id": "test_event_005",
            "compression_results": [
                {"method": "test", "level": 1, "snr_degradation_db": 3.0}
            ]
        }
        
        # With default threshold (5.0), this is acceptable
        result_default = flag_compression_quality(metrics_data)
        assert result_default["quality_flags"]["summary"]["acceptable"] == 1
        
        # With custom threshold (2.5), this is unacceptable
        result_custom = flag_compression_quality(metrics_data, threshold=2.5)
        assert result_custom["quality_flags"]["summary"]["unacceptable"] == 1

    def test_empty_results(self):
        """Test handling of empty compression results"""
        metrics_data = {
            "event_id": "test_event_006",
            "compression_results": []
        }
        
        result = flag_compression_quality(metrics_data)
        
        assert result["quality_flags"]["summary"]["acceptable"] == 0
        assert result["quality_flags"]["summary"]["unacceptable"] == 0

    def test_missing_metrics_structure(self):
        """Test handling of invalid metrics data"""
        invalid_data = {"wrong_key": "value"}
        
        result = flag_compression_quality(invalid_data)
        
        assert result["quality_flags"]["summary"]["acceptable"] == 0
        assert result["quality_flags"]["summary"]["unacceptable"] == 0

class TestProcessQualityFlagsForEvent:
    """Tests for the process_quality_flags_for_event function"""

    def test_process_and_save_file(self):
        """Test processing metrics and saving to file"""
        metrics_data = {
            "event_id": "test_event_007",
            "compression_results": [
                {"method": "gzip", "level": 9, "snr_degradation_db": 2.0},
                {"method": "jpeg2000", "level": "high", "snr_degradation_db": 6.0}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            metrics_file = tmpdir_path / "metrics.json"
            output_file = tmpdir_path / "flags.json"
            
            # Write test metrics
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f)
            
            # Process
            result = process_quality_flags_for_event(metrics_file, output_file)
            
            # Verify output file exists
            assert output_file.exists()
            
            # Verify content
            with open(output_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["event_id"] == "test_event_007"
            assert saved_data["quality_flags"]["summary"]["acceptable"] == 1
            assert saved_data["quality_flags"]["summary"]["unacceptable"] == 1

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing metrics file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "output.json"
            non_existent = Path(tmpdir) / "non_existent.json"
            
            with pytest.raises(FileNotFoundError):
                process_quality_flags_for_event(non_existent, output_file)

class TestAggregateQualityReport:
    """Tests for the aggregate_quality_report function"""

    def test_aggregate_multiple_events(self):
        """Test aggregation across multiple event metrics files"""
        metrics_data_list = [
            {
                "event_id": "evt_001",
                "compression_results": [
                    {"method": "gzip", "level": 9, "snr_degradation_db": 1.0}
                ]
            },
            {
                "event_id": "evt_002",
                "compression_results": [
                    {"method": "jpeg2000", "level": "high", "snr_degradation_db": 7.0}
                ]
            },
            {
                "event_id": "evt_003",
                "compression_results": [
                    {"method": "wavelet", "level": "low", "snr_degradation_db": 3.0},
                    {"method": "quantization", "level": 4, "snr_degradation_db": 9.0}
                ]
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Write metrics files
            for i, data in enumerate(metrics_data_list):
                metrics_file = tmpdir_path / f"metrics_{i}.json"
                with open(metrics_file, 'w') as f:
                    json.dump(data, f)
            
            output_file = tmpdir_path / "aggregate_report.json"
            
            # Aggregate
            report = aggregate_quality_report(tmpdir_path, output_file)
            
            # Verify report structure
            assert report["total_events_processed"] == 3
            assert report["total_compression_tests"] == 4
            assert report["overall_summary"]["acceptable"] == 2
            assert report["overall_summary"]["unacceptable"] == 2
            
            # Verify acceptance rate calculation
            expected_rate = 2 / 4
            assert abs(report["overall_summary"]["acceptance_rate"] - expected_rate) < 0.001
            
            # Verify output file exists
            assert output_file.exists()

    def test_aggregate_empty_directory(self):
        """Test aggregation with no metrics files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_file = tmpdir_path / "report.json"
            
            report = aggregate_quality_report(tmpdir_path, output_file)
            
            assert report["total_events_processed"] == 0
            assert report["overall_summary"]["acceptable"] == 0
            assert report["overall_summary"]["unacceptable"] == 0

    def test_directory_not_found(self):
        """Test that FileNotFoundError is raised for missing metrics directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "report.json"
            non_existent = Path(tmpdir) / "non_existent_dir"
            
            with pytest.raises(FileNotFoundError):
                aggregate_quality_report(non_existent, output_file)