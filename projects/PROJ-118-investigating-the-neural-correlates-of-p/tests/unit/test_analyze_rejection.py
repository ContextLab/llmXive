import pytest
from pathlib import Path
import tempfile
import os
from code.analyze_rejection import (
    parse_ica_log,
    find_ica_logs,
    analyze_rejection_rates,
    identify_excluded_participants,
    write_exclusion_log,
    run_rejection_analysis
)

class TestParseIcaLog:
    def test_parse_standard_log(self, tmp_path):
        """Test parsing a standard log format."""
        log_content = """
        Processing sub-01...
        Total epochs: 100
        Rejected epochs: 15
        ICA components removed: 2
        """
        log_file = tmp_path / "sub-01_ica_rejection.log"
        log_file.write_text(log_content)
        
        total, rejected, pid = parse_ica_log(log_file)
        
        assert total == 100
        assert rejected == 15
        assert pid == "sub-01"

    def test_parse_mne_format(self, tmp_path):
        """Test parsing MNE-like log format."""
        log_content = """
        Dropped 10 epochs due to excessive amplitude.
        Rejected 12 epochs based on ICA components.
        """
        log_file = tmp_path / "sub-02_ica_rejection.log"
        log_file.write_text(log_content)
        
        # This format might not have explicit "Total", so it might return 0 for total
        # depending on regex strictness. Let's test what we expect.
        total, rejected, pid = parse_ica_log(log_file)
        
        # We expect to catch "Rejected 12 epochs"
        assert rejected == 12
        assert pid == "sub-02"
        # Total might be 0 if not explicitly "Total epochs: X"
        # The regex looks for "Total (epochs|trials)"
        # The content has "Dropped 10 epochs" but not "Total epochs: 100"
        # So total might be 0.
        
    def test_parse_invalid_log(self, tmp_path):
        """Test parsing a log with no relevant data."""
        log_content = "Some random text without numbers."
        log_file = tmp_path / "sub-03_ica_rejection.log"
        log_file.write_text(log_content)
        
        total, rejected, pid = parse_ica_log(log_file)
        
        assert total == 0
        assert rejected == 0
        assert pid == "sub-03"

class TestFindIcaLogs:
    def test_find_logs_in_directory(self, tmp_path):
        """Test finding log files in a directory."""
        (tmp_path / "sub-01_ica_rejection.log").write_text("log")
        (tmp_path / "sub-02_ica_rejection.log").write_text("log")
        (tmp_path / "data.txt").write_text("not a log")
        
        logs = find_ica_logs(tmp_path)
        
        assert len(logs) == 2
        assert all(l.suffix == '.log' for l in logs)

    def test_no_logs_found(self, tmp_path):
        """Test behavior when no logs are found."""
        logs = find_ica_logs(tmp_path)
        assert len(logs) == 0

class TestAnalyzeRejectionRates:
    def test_calculate_rates(self, tmp_path):
        """Test rate calculation."""
        # Create mock logs
        (tmp_path / "sub-01_ica_rejection.log").write_text("Total epochs: 100\nRejected epochs: 10")
        (tmp_path / "sub-02_ica_rejection.log").write_text("Total epochs: 200\nRejected epochs: 150")
        
        logs = find_ica_logs(tmp_path)
        rates = analyze_rejection_rates(logs)
        
        assert "sub-01" in rates
        assert rates["sub-01"]["rate"] == 0.10
        assert "sub-02" in rates
        assert rates["sub-02"]["rate"] == 0.75

class TestIdentifyExcludedParticipants:
    def test_threshold_exceeded(self):
        """Test exclusion logic."""
        data = {
            "sub-01": {"total": 100, "rejected": 10, "rate": 0.10},
            "sub-02": {"total": 100, "rejected": 60, "rate": 0.60},
            "sub-03": {"total": 100, "rejected": 50, "rate": 0.50} # Exactly 50%
        }
        
        excluded = identify_excluded_participants(data, threshold=0.50)
        
        assert "sub-01" not in excluded
        assert "sub-02" in excluded
        assert "sub-03" not in excluded # 50% is not > 50%

    def test_missing_data_excluded(self):
        """Test that participants with no data are excluded."""
        data = {
            "sub-01": {"total": 0, "rejected": 0, "rate": 0.0}
        }
        
        excluded = identify_excluded_participants(data, threshold=0.50)
        
        assert "sub-01" in excluded

class TestWriteExclusionLog:
    def test_write_log(self, tmp_path):
        """Test writing the exclusion log file."""
        excluded_ids = {"sub-02", "sub-05"}
        output_path = tmp_path / "rejected.log"
        
        write_exclusion_log(excluded_ids, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "sub-02" in content
        assert "sub-05" in content
        assert "Total excluded: 2" in content

class TestRunRejectionAnalysis:
    def test_full_pipeline(self, tmp_path):
        """Test the full pipeline."""
        # Setup mock logs
        (tmp_path / "sub-01_ica_rejection.log").write_text("Total epochs: 100\nRejected epochs: 10")
        (tmp_path / "sub-02_ica_rejection.log").write_text("Total epochs: 100\nRejected epochs: 60")
        
        result = run_rejection_analysis(tmp_path, output_file="test_rejected.log")
        
        assert result["total_analyzed"] == 2
        assert "sub-02" in result["excluded"]
        assert "sub-01" in result["included"]
        assert (tmp_path / "test_rejected.log").exists()