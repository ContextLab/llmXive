import pytest
from pathlib import Path
import os
import sys

# Add code to path if running from tests directory
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from spec_verification import analyze_contradiction, read_file_safe
from config import get_config_summary, ensure_directories

class TestSpecVerification:
    
    def test_analyze_contradiction_format(self):
        """Verify the log entry format matches the T000b requirement."""
        result = analyze_contradiction("", "")
        
        # Check format: TIMESTAMP | CRITICAL_DEVIATION | ... | ACTION: KICKBACK_REQUIRED
        assert "CRITICAL_DEVIATION" in result
        assert "Spec mandates Raw/Semgrep" in result
        assert "Plan mandates Density/SonarQube" in result
        assert "ACTION: KICKBACK_REQUIRED" in result
        
        parts = result.split(" | ")
        assert len(parts) == 4, f"Expected 4 parts separated by ' | ', got {len(parts)}: {result}"
        
        # Check timestamp format (YYYY-MM-DD HH:MM:SS)
        timestamp = parts[0]
        assert len(timestamp) == 19, f"Timestamp length incorrect: {timestamp}"
        assert " " in timestamp, "Timestamp missing space between date and time"
    
    def test_log_file_creation(self, tmp_path):
        """Test that the main function creates the log file with correct content."""
        # Mock config to use tmp_path
        import config
        original_get_config = config.get_config_summary
        
        def mock_config():
            return {
                "project_root": tmp_path,
                "log_dir": str(tmp_path / "data" / "logs"),
                "raw_dir": str(tmp_path / "data" / "raw"),
                "processed_dir": str(tmp_path / "data" / "processed"),
                "results_dir": str(tmp_path / "data" / "results"),
                "contracts_dir": str(tmp_path / "contracts"),
                "code_dir": str(tmp_path / "code")
            }
        
        config.get_config_summary = mock_config
        
        try:
            # Import main here to pick up mocked config
            from spec_verification import main
            main()
            
            # Check file exists
            log_file = tmp_path / "data" / "logs" / "spec_verification.log"
            assert log_file.exists(), "Log file was not created"
            
            # Check content
            content = log_file.read_text()
            assert "CRITICAL_DEVIATION" in content
            assert "ACTION: KICKBACK_REQUIRED" in content
        finally:
            # Restore original function
            config.get_config_summary = original_get_config
    
    def test_read_file_safe_missing(self):
        """Test reading a non-existent file returns empty string."""
        result = read_file_safe(Path("/non/existent/path"))
        assert result == ""
    
    def test_read_file_safe_existing(self, tmp_path):
        """Test reading an existing file."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        result = read_file_safe(test_file)
        assert result == test_content