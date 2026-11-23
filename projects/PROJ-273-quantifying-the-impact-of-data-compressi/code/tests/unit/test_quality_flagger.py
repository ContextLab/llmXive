"""
Unit tests for the quality flagging module.
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add code to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from src.compression.quality_flagger import (
    flag_compression_quality,
    process_quality_flags_for_event,
    aggregate_quality_report,
    SNR_DEGRADATION_THRESHOLD_DB
)

class TestFlagCompressionQuality:
    """Tests for flag_compression_quality function."""

    def test_acceptable_snr_degradation(self):
        """Test that SNR degradation below threshold is flagged as acceptable."""
        result = flag_compression_quality(
            snr_degradation_db=3.0,
            method="quantization",
            level="16-bit",
            event_id="evt_001"
        )
        
        assert result["status"] == "acceptable"
        assert result["snr_degradation_db"] == 3.0
        assert result["threshold_db"] == SNR_DEGRADATION_THRESHOLD_DB
        assert "within" in result["reason"]

    def test_unacceptable_snr_degradation(self):
        """Test that SNR degradation above threshold is flagged as unacceptable."""
        result = flag_compression_quality(
            snr_degradation_db=6.5,
            method="jpeg2000",
            level="50",
            event_id="evt_002"
        )
        
        assert result["status"] == "unacceptable"
        assert result["snr_degradation_db"] == 6.5
        assert "exceeds" in result["reason"]

    def test_exact_threshold_boundary(self):
        """Test that SNR degradation exactly at threshold is acceptable."""
        result = flag_compression_quality(
            snr_degradation_db=SNR_DEGRADATION_THRESHOLD_DB,
            method="wavelet",
            level="0.01",
            event_id="evt_003"
        )
        
        assert result["status"] == "acceptable"

    def test_slightly_above_threshold(self):
        """Test that SNR degradation slightly above threshold is unacceptable."""
        result = flag_compression_quality(
            snr_degradation_db=SNR_DEGRADATION_THRESHOLD_DB + 0.1,
            method="quantization",
            level="8-bit",
            event_id="evt_004"
        )
        
        assert result["status"] == "unacceptable"

class TestProcessQualityFlagsForEvent:
    """Tests for process_quality_flags_for_event function."""

    @pytest.fixture
    def temp_compression_results(self, tmp_path):
        """Create a temporary compression results file."""
        results = {
            "event_id": "evt_test_001",
            "compression_results": [
                {
                    "method": "quantization",
                    "level": "16-bit",
                    "snr_degradation_db": 2.5
                },
                {
                    "method": "quantization",
                    "level": "4-bit",
                    "snr_degradation_db": 8.0
                },
                {
                    "method": "jpeg2000",
                    "level": "90",
                    "snr_degradation_db": 4.2
                },
                {
                    "method": "jpeg2000",
                    "level": "50",
                    "snr_degradation_db": 12.5
                }
            ]
        }
        
        file_path = tmp_path / "event_evt_test_001.json"
        with open(file_path, 'w') as f:
            json.dump(results, f)
        
        return file_path

    def test_process_single_event(self, temp_compression_results, tmp_path):
        """Test processing a single event with mixed acceptable/unacceptable results."""
        output_path = tmp_path / "flags_evt_test_001.json"
        
        flags = process_quality_flags_for_event(temp_compression_results, output_path)
        
        assert len(flags) == 4
        
        # Check acceptable flags
        acceptable_flags = [f for f in flags if f["status"] == "acceptable"]
        assert len(acceptable_flags) == 2
        
        # Check unacceptable flags
        unacceptable_flags = [f for f in flags if f["status"] == "unacceptable"]
        assert len(unacceptable_flags) == 2
        
        # Verify file was created
        assert output_path.exists()

    def test_missing_snr_degradation(self, tmp_path):
        """Test handling of results missing SNR degradation."""
        results = {
            "event_id": "evt_missing",
            "compression_results": [
                {
                    "method": "quantization",
                    "level": "16-bit"
                    # Missing snr_degradation_db
                }
            ]
        }
        
        file_path = tmp_path / "event_evt_missing.json"
        with open(file_path, 'w') as f:
            json.dump(results, f)
        
        output_path = tmp_path / "flags_evt_missing.json"
        flags = process_quality_flags_for_event(file_path, output_path)
        
        # Should skip the entry with missing SNR
        assert len(flags) == 0

    def test_file_not_found(self, tmp_path):
        """Test handling of non-existent input file."""
        non_existent = tmp_path / "non_existent.json"
        
        with pytest.raises(FileNotFoundError):
            process_quality_flags_for_event(non_existent)

class TestAggregateQualityReport:
    """Tests for aggregate_quality_report function."""

    @pytest.fixture
    def temp_flag_files(self, tmp_path):
        """Create temporary flag files for aggregation."""
        # File 1
        flags1 = [
            {
                "event_id": "evt_1",
                "method": "quantization",
                "level": "16-bit",
                "snr_degradation_db": 2.0,
                "status": "acceptable"
            },
            {
                "event_id": "evt_1",
                "method": "quantization",
                "level": "4-bit",
                "snr_degradation_db": 8.0,
                "status": "unacceptable"
            }
        ]
        
        file1 = tmp_path / "flags_evt_1.json"
        with open(file1, 'w') as f:
            json.dump(flags1, f)
        
        # File 2
        flags2 = [
            {
                "event_id": "evt_2",
                "method": "jpeg2000",
                "level": "90",
                "snr_degradation_db": 3.5,
                "status": "acceptable"
            },
            {
                "event_id": "evt_2",
                "method": "jpeg2000",
                "level": "50",
                "snr_degradation_db": 10.0,
                "status": "unacceptable"
            }
        ]
        
        file2 = tmp_path / "flags_evt_2.json"
        with open(file2, 'w') as f:
            json.dump(flags2, f)
        
        return [file1, file2]

    def test_aggregate_report_structure(self, temp_flag_files, tmp_path):
        """Test that the aggregated report has the correct structure."""
        output_path = tmp_path / "aggregate_report.json"
        
        report = aggregate_quality_report(temp_flag_files, output_path)
        
        assert "summary" in report
        assert "method_statistics" in report
        assert "threshold_exceeded_events" in report
        
        # Check summary fields
        summary = report["summary"]
        assert summary["total_compressions_evaluated"] == 4
        assert summary["acceptable_count"] == 2
        assert summary["unacceptable_count"] == 2
        assert abs(summary["acceptance_rate"] - 0.5) < 0.01
        assert summary["threshold_db"] == SNR_DEGRADATION_THRESHOLD_DB

    def test_method_statistics(self, temp_flag_files, tmp_path):
        """Test that method statistics are correctly aggregated."""
        output_path = tmp_path / "aggregate_report.json"
        
        report = aggregate_quality_report(temp_flag_files, output_path)
        
        method_stats = report["method_statistics"]
        
        assert "quantization" in method_stats
        assert "jpeg2000" in method_stats
        
        # Check quantization stats
        quant_stats = method_stats["quantization"]
        assert quant_stats["total"] == 2
        assert quant_stats["acceptable"] == 1
        assert quant_stats["unacceptable"] == 1
        assert abs(quant_stats["avg_snr_degradation"] - 5.0) < 0.01

    def test_threshold_exceeded_events(self, temp_flag_files, tmp_path):
        """Test that threshold exceeded events are correctly identified."""
        output_path = tmp_path / "aggregate_report.json"
        
        report = aggregate_quality_report(temp_flag_files, output_path)
        
        exceeded = report["threshold_exceeded_events"]
        assert len(exceeded) == 2
        
        # All should be unacceptable
        for event in exceeded:
            assert event["status"] == "unacceptable"