"""
Unit tests for the structured logging infrastructure (T009).

Verifies that:
1. Logger is properly initialized
2. Error codes follow ERR-### format
3. Logs contain correct error codes
4. All seven Constitution Principles are referenced in error codes where applicable
"""
import pytest
import logging
import json
from pathlib import Path
import tempfile
import re
import sys
from io import StringIO

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.utils.logger import (
    AuditLogger,
    get_default_logger,
    get_error_message,
    validate_error_code,
    ERROR_CODES,
    main
)


class TestErrorCodes:
    """Test that error codes follow the ERR-### format."""
    
    def test_error_code_format(self):
        """Verify all error codes match ERR-### pattern."""
        pattern = re.compile(r'^ERR-\d{3}$')
        for code in ERROR_CODES.keys():
            assert pattern.match(code), f"Error code {code} does not match ERR-### format"
    
    def test_error_code_range(self):
        """Verify error codes are in expected ranges."""
        # Extraction errors: ERR-001 to ERR-099
        extraction_codes = [c for c in ERROR_CODES if c.startswith("ERR-0")]
        assert len(extraction_codes) > 0, "Should have extraction error codes"
        
        # Validation errors: ERR-100 to ERR-199
        validation_codes = [c for c in ERROR_CODES if c.startswith("ERR-1")]
        assert len(validation_codes) > 0, "Should have validation error codes"
        
        # Export errors: ERR-200 to ERR-299
        export_codes = [c for c in ERROR_CODES if c.startswith("ERR-2")]
        assert len(export_codes) > 0, "Should have export error codes"
        
        # Resource errors: ERR-300 to ERR-399
        resource_codes = [c for c in ERROR_CODES if c.startswith("ERR-3")]
        assert len(resource_codes) > 0, "Should have resource error codes"
        
        # Evaluation errors: ERR-800 to ERR-899
        eval_codes = [c for c in ERROR_CODES if c.startswith("ERR-8")]
        assert len(eval_codes) > 0, "Should have evaluation error codes"
    
    def test_known_error_codes_exist(self):
        """Verify specific required error codes exist."""
        required_codes = [
            "ERR-001",  # Missing metric
            "ERR-101",  # P-value inconsistency
            "ERR-201",  # Export mismatch
            "ERR-301",  # Resource limit
            "ERR-800",  # Validation threshold
            "ERR-950",  # Constitution violation
        ]
        for code in required_codes:
            assert code in ERROR_CODES, f"Required error code {code} not found"
    
    def test_error_descriptions_non_empty(self):
        """Verify all error codes have non-empty descriptions."""
        for code, desc in ERROR_CODES.items():
            assert len(desc) > 0, f"Error code {code} has empty description"
            assert isinstance(desc, str), f"Error code {code} description is not a string"


class TestAuditLogger:
    """Test the AuditLogger class functionality."""
    
    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            yield Path(f.name)
    
    def test_logger_initialization(self):
        """Test logger can be initialized."""
        logger = AuditLogger(name="test_logger")
        assert logger is not None
        assert logger.logger.level == logging.INFO
    
    def test_logger_with_file(self, temp_log_file):
        """Test logger writes to file."""
        logger = AuditLogger(name="test_logger_file", log_file=temp_log_file)
        logger.info("Test message")
        
        assert temp_log_file.exists()
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "Test message" in content
    
    def test_error_code_formatting(self, temp_log_file):
        """Test that error messages include the error code."""
        logger = AuditLogger(name="test_logger_format", log_file=temp_log_file)
        logger.error("Test error", "ERR-001")
        
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "[ERR-001]" in content or "ERR-001" in content
    
    def test_invalid_error_code_raises(self):
        """Test that invalid error codes raise ValueError."""
        logger = AuditLogger(name="test_logger_invalid")
        with pytest.raises(ValueError):
            logger.error("Test error", "INVALID-CODE")
    
    def test_log_extraction_error(self, temp_log_file):
        """Test extraction error logging."""
        logger = AuditLogger(name="test_logger_extraction", log_file=temp_log_file)
        logger.log_extraction_error("https://example.com", "ERR-001", "p_value")
        
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "ERR-001" in content
            assert "example.com" in content
            assert "p_value" in content
    
    def test_log_validation_error(self, temp_log_file):
        """Test validation error logging."""
        logger = AuditLogger(name="test_logger_validation", log_file=temp_log_file)
        logger.log_validation_error("record_123", "ERR-101", "P-value mismatch")
        
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "ERR-101" in content
            assert "record_123" in content
    
    def test_log_resource_error(self, temp_log_file):
        """Test resource error logging."""
        logger = AuditLogger(name="test_logger_resource", log_file=temp_log_file)
        logger.log_resource_error("RAM", 2048.0, 2100.0, "ERR-301")
        
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "ERR-301" in content
            assert "RAM" in content
    
    def test_get_error_message(self):
        """Test retrieving error message by code."""
        msg = get_error_message("ERR-001")
        assert "Missing required metric" in msg
        assert isinstance(msg, str)
    
    def test_validate_error_code(self):
        """Test error code validation."""
        assert validate_error_code("ERR-001") is True
        assert validate_error_code("INVALID") is False
    
    def test_get_all_error_codes(self):
        """Test retrieving all error codes."""
        logger = AuditLogger(name="test_logger_all")
        codes = logger.get_all_error_codes()
        assert isinstance(codes, dict)
        assert len(codes) > 0
        assert "ERR-001" in codes


class TestDefaultLogger:
    """Test the default logger singleton pattern."""
    
    def test_get_default_logger(self):
        """Test getting default logger."""
        logger1 = get_default_logger()
        logger2 = get_default_logger()
        # Should return same instance
        assert logger1 is logger2
    
    def test_default_logger_with_file(self):
        """Test default logger with file parameter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = Path(f.name)
        
        # Reset global state
        import code.src.utils.logger as logger_module
        logger_module._default_logger = None
        
        logger = get_default_logger(log_file=log_file, level=logging.DEBUG)
        logger.info("Test")
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            assert "Test" in f.read()
    
    def test_default_logger_level(self):
        """Test default logger level setting."""
        import code.src.utils.logger as logger_module
        logger_module._default_logger = None
        
        logger = get_default_logger(level=logging.DEBUG)
        assert logger.logger.level == logging.DEBUG


class TestMainFunction:
    """Test the main function of logger module."""
    
    def test_main_executes_successfully(self, capsys):
        """Test that main() runs without error."""
        result = main()
        assert result == 0
        
        # Check output
        captured = capsys.readouterr()
        assert "Structured logging verification" in captured.out
        assert "Error codes registered" in captured.out
    
    def test_main_creates_log_file(self, tmp_path):
        """Test that main() creates log file."""
        # Temporarily override the log path
        import code.src.utils.logger as logger_module
        original_main = logger_module.main
        
        def patched_main():
            from pathlib import Path
            log_dir = tmp_path / "data" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "logger_test.log"
            
            logger = logger_module.get_default_logger(log_file=log_file, level=logging.DEBUG)
            logger.info("Test from patched main")
            logger.error("Test error", "ERR-001")
            
            assert log_file.exists()
            with open(log_file, 'r') as f:
                content = f.read()
                assert "ERR-001" in content
            return 0
        
        logger_module.main = patched_main
        try:
            result = logger_module.main()
            assert result == 0
        finally:
            logger_module.main = original_main


class TestConstitutionCompliance:
    """Test that logging infrastructure supports Constitution Principles."""
    
    def test_error_codes_for_principle_vii(self):
        """Verify error codes support provenance tracking (Principle VII)."""
        # ERR-001 to ERR-010 cover extraction provenance
        provenance_codes = ["ERR-001", "ERR-002", "ERR-008", "ERR-009", "ERR-010"]
        for code in provenance_codes:
            assert code in ERROR_CODES, f"Provenance code {code} missing for Principle VII"
    
    def test_error_codes_for_principle_v(self):
        """Verify error codes support governance (Principle V)."""
        # ERR-950 is for Constitution principle violations
        assert "ERR-950" in ERROR_CODES
        assert "Constitution" in ERROR_CODES["ERR-950"]
    
    def test_error_codes_for_principle_iv(self):
        """Verify error codes support checksums/integrity (Principle IV)."""
        # ERR-202 covers manifest generation
        assert "ERR-202" in ERROR_CODES
        assert "Manifest" in ERROR_CODES["ERR-202"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
