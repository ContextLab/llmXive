import pytest
import json
import tempfile
from pathlib import Path
import sys

from src.compression.quality_flagger import (
    flag_compression_quality,
    process_quality_flags_for_event,
    aggregate_quality_report,
    SNR_DEGRADATION_THRESHOLD
)

class TestFlagCompressionQuality:
    def test_acceptable_degradation(self):
        # 1 dB degradation is approx 20% power loss? No.
        # 10 log10(P_sig/P_noise).
        # If SNR drops by 1 dB, ratio changes.
        # Let's test the logic: 0.1 dB -> ~2.3% loss. Should be acceptable.
        result = flag_compression_quality(0.1, "quantization", "8-bit", "evt1")
        assert result["is_unacceptable"] is False
        assert "Acceptable" in result["reason"]

    def test_unacceptable_degradation_high_dB(self):
        # 10 dB degradation is huge.
        # 10 dB -> 90% loss.
        result = flag_compression_quality(10.0, "jpeg2000", "50", "evt1")
        assert result["is_unacceptable"] is True
        assert "exceeds threshold" in result["reason"]

    def test_zero_degradation(self):
        result = flag_compression_quality(0.0, "lossless", "gzip", "evt1")
        assert result["is_unacceptable"] is False

    def test_negative_degradation(self):
        # Should not happen, but handle gracefully
        result = flag_compression_quality(-0.5, "test", "1", "evt1")
        assert result["is_unacceptable"] is False

class TestProcessQualityFlagsForEvent:
    def test_process_flags_from_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            metrics_file = tmp_path / "metrics.json"
            
            data = {
                "results": [
                    {"method": "q", "level": "8", "snr_degradation": 0.1},
                    {"method": "j", "level": "50", "snr_degradation": 10.0}
                ]
            }
            with open(metrics_file, 'w') as f:
                json.dump(data, f)

            flags = process_quality_flags_for_event(metrics_file, "evt1")
            
            assert len(flags) == 2
            assert flags[0]["is_unacceptable"] is False
            assert flags[1]["is_unacceptable"] is True

    def test_missing_file(self):
        flags = process_quality_flags_for_event(Path("/nonexistent/file.json"), "evt1")
        assert flags == []

class TestAggregateQualityReport:
    def test_aggregate_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_file = tmp_path / "report.json"
            
            flags = [
                {"event_id": "e1", "method": "m1", "level": "l1", "snr_degradation_db": 0.1, "snr_degradation_percent": 2.0, "is_unacceptable": False, "reason": "Ok"},
                {"event_id": "e1", "method": "m2", "level": "l2", "snr_degradation_db": 10.0, "snr_degradation_percent": 90.0, "is_unacceptable": True, "reason": "Bad"}
            ]
            
            aggregate_quality_report(flags, output_file)
            
            assert output_file.exists()
            with open(output_file, 'r') as f:
                report = json.load(f)
            
            assert report["total_compressions"] == 2
            assert report["unacceptable_count"] == 1
            assert report["acceptable_count"] == 1
            assert report["threshold_percent"] == SNR_DEGRADATION_THRESHOLD