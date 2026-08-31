import json
import os
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

# Add code directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from failure_logger import (
    FailureReason,
    load_existing_failure_log,
    record_failure,
    compile_failure_summary,
    write_failure_report
)

class TestFailureLogger:
    """Unit tests for the failure logger module."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp()
        self.original_failure_log_path = Path("artifacts/logs/failure_log.json")
        
        # Temporarily override the failure log path
        self.temp_log_path = Path(self.test_dir) / "failure_log.json"
        
        # We need to monkey-patch the module's global paths
        import failure_logger
        self.original_log_path = failure_logger.FAILURE_LOG_PATH
        self.original_summary_path = failure_logger.FAILURE_SUMMARY_PATH
        self.original_report_path = failure_logger.FAILURE_REPORT_PATH
        
        failure_logger.FAILURE_LOG_PATH = self.temp_log_path
        failure_logger.FAILURE_SUMMARY_PATH = Path(self.test_dir) / "failure_summary.json"
        failure_logger.FAILURE_REPORT_PATH = Path(self.test_dir) / "failure_report.md"
        
        yield
        
        # Restore original paths
        failure_logger.FAILURE_LOG_PATH = self.original_log_path
        failure_logger.FAILURE_SUMMARY_PATH = self.original_summary_path
        failure_logger.FAILURE_REPORT_PATH = self.original_report_path

    def test_failure_reason_constants(self):
        """Test that FailureReason constants are defined correctly."""
        assert FailureReason.MODEL_SUBSTITUTION == "Model Substitution/Unavailable"
        assert FailureReason.DATA_GAP == "Data Unavailable"
        assert FailureReason.MISSING_SEED == "Missing Random Seed"
        assert FailureReason.PARAMETER_LIMIT_EXCEEDED == "Parameter Limit Exceeded (>1M)"
        assert FailureReason.MANIFEST_VALIDATION_ERROR == "Manifest Validation Error"
        assert FailureReason.DATASET_FETCH_ERROR == "Dataset Fetch Error"
        assert FailureReason.VARIABLE_MISMATCH == "Variable Mismatch"
        assert FailureReason.UNKNOWN == "Unknown Failure"

    def test_load_empty_failure_log(self):
        """Test loading an empty or non-existent failure log."""
        log = load_existing_failure_log()
        assert isinstance(log, list)
        assert len(log) == 0

    def test_record_failure_creates_entry(self):
        """Test that recording a failure creates a valid entry."""
        entry = record_failure(
            paper_id="test_paper_123",
            reason=FailureReason.DATA_GAP,
            details="Test failure details",
            source_file="test_module.py"
        )
        
        assert entry["paper_id"] == "test_paper_123"
        assert entry["reason"] == FailureReason.DATA_GAP
        assert entry["details"] == "Test failure details"
        assert entry["source_file"] == "test_module.py"
        assert "timestamp" in entry

    def test_record_failure_persists(self):
        """Test that recorded failures are persisted to disk."""
        # Record a failure
        record_failure(
            paper_id="persist_test_456",
            reason=FailureReason.MODEL_SUBSTITUTION
        )
        
        # Load and verify
        log = load_existing_failure_log()
        assert len(log) == 1
        assert log[0]["paper_id"] == "persist_test_456"
        assert log[0]["reason"] == FailureReason.MODEL_SUBSTITUTION

    def test_multiple_failures_accumulate(self):
        """Test that multiple failures accumulate in the log."""
        # Record multiple failures
        record_failure("paper_1", FailureReason.DATA_GAP)
        record_failure("paper_2", FailureReason.MODEL_SUBSTITUTION)
        record_failure("paper_3", FailureReason.MISSING_SEED)
        
        # Verify accumulation
        log = load_existing_failure_log()
        assert len(log) == 3
        
        paper_ids = [entry["paper_id"] for entry in log]
        assert "paper_1" in paper_ids
        assert "paper_2" in paper_ids
        assert "paper_3" in paper_ids

    def test_compile_failure_summary(self):
        """Test compilation of failure summary."""
        # Record some failures
        record_failure("paper_1", FailureReason.DATA_GAP, "Details 1")
        record_failure("paper_2", FailureReason.DATA_GAP, "Details 2")
        record_failure("paper_3", FailureReason.MODEL_SUBSTITUTION, "Details 3")
        
        # Compile summary
        summary = compile_failure_summary()
        
        assert summary["total_failures"] == 3
        assert summary["by_reason"][FailureReason.DATA_GAP] == 2
        assert summary["by_reason"][FailureReason.MODEL_SUBSTITUTION] == 1
        assert len(summary["affected_papers"]) == 3
        assert "generated_at" in summary

    def test_write_failure_report(self):
        """Test writing a Markdown failure report."""
        # Record some failures
        record_failure("paper_1", FailureReason.DATA_GAP, "Test detail")
        record_failure("paper_2", FailureReason.MODEL_SUBSTITUTION, "Another detail")
        
        # Write report
        report_path = write_failure_report()
        
        # Verify file exists
        assert os.path.exists(report_path)
        
        # Verify content
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# Qualitative Failure Report" in content
        assert "Total Failures" in content
        assert "paper_1" in content
        assert "paper_2" in content
        assert FailureReason.DATA_GAP in content
        assert FailureReason.MODEL_SUBSTITUTION in content
        assert "Test detail" in content

    def test_summary_persists_to_disk(self):
        """Test that the failure summary is saved to disk."""
        # Record a failure and compile summary
        record_failure("summary_test", FailureReason.DATA_GAP)
        summary = compile_failure_summary()
        
        # Verify summary file exists
        assert os.path.exists(Path(self.test_dir) / "failure_summary.json")
        
        # Verify content matches
        with open(Path(self.test_dir) / "failure_summary.json", 'r', encoding='utf-8') as f:
            saved_summary = json.load(f)
        
        assert saved_summary["total_failures"] == summary["total_failures"]
        assert saved_summary["by_reason"] == summary["by_reason"]

    def test_empty_summary_when_no_failures(self):
        """Test summary generation when no failures exist."""
        summary = compile_failure_summary()
        
        assert summary["total_failures"] == 0
        assert summary["by_reason"] == {}
        assert summary["affected_papers"] == []
        assert "generated_at" in summary

    def test_report_content_for_empty_log(self):
        """Test report content when no failures exist."""
        # Ensure log is empty
        if self.temp_log_path.exists():
            self.temp_log_path.unlink()
        
        report_path = write_failure_report()
        
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "No failures recorded" in content