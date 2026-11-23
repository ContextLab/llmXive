import json
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.features.extract import (
    detect_pragmatic_markers,
    calculate_syntax_tree_depth,
    calculate_token_frequency,
    extract_features_from_log
)


class TestPragmaticMarkerIdentification:
    """Tests for pragmatic marker detection functionality."""

    def test_pragmatic_marker_identification_works(self):
        """Test that pragmatic markers are correctly identified in logs."""
        log_content = """
        2024-01-01 10:00:00 INFO Starting process
        2024-01-01 10:00:01 ERROR Connection failed, retrying...
        2024-01-01 10:00:02 INFO State changed to ERROR
        2024-01-01 10:00:03 WARN Attempt 2/3
        2024-01-01 10:00:04 INFO Recovery mode activated
        2024-01-01 10:00:05 INFO State transition from ERROR to RECOVERING
        2024-01-01 10:00:06 INFO Success after 2 retries
        """
        
        result = detect_pragmatic_markers(log_content)
        
        # Check that error recovery markers are detected
        assert 'error_recovery' in result
        assert result['error_recovery']['count'] >= 2  # retrying, Recovery mode
        assert result['error_recovery']['has_recovery_attempts'] is True
        
        # Check that state transition markers are detected
        assert 'state_transitions' in result
        assert result['state_transitions']['count'] >= 2  # State changed, State transition
        assert result['state_transitions']['has_state_changes'] is True
        
        # Check total count
        assert result['total_pragmatic_markers'] >= 4
        
        # Verify specific markers are captured
        recovery_markers = [m for m in result['error_recovery']['markers'] 
                          if 'retry' in m['match'].lower() or 'recovery' in m['match'].lower()]
        assert len(recovery_markers) >= 1
        
        transition_markers = [m for m in result['state_transitions']['markers'] 
                            if 'state' in m['match'].lower()]
        assert len(transition_markers) >= 1

    def test_pragmatic_markers_empty_log(self):
        """Test that empty logs return zero markers."""
        result = detect_pragmatic_markers("")
        
        assert result['error_recovery']['count'] == 0
        assert result['state_transitions']['count'] == 0
        assert result['total_pragmatic_markers'] == 0
        assert result['error_recovery']['has_recovery_attempts'] is False
        assert result['state_transitions']['has_state_changes'] is False

    def test_pragmatic_markers_no_matches(self):
        """Test logs without pragmatic markers."""
        log_content = "Simple log without any recovery or state transition patterns"
        result = detect_pragmatic_markers(log_content)
        
        assert result['error_recovery']['count'] == 0
        assert result['state_transitions']['count'] == 0
        assert result['total_pragmatic_markers'] == 0

class TestSyntaxTreeDepth:
    """Tests for syntax tree depth calculation."""

    def test_syntax_tree_depth_calculates_correctly(self):
        """Test that syntax tree depth is calculated correctly."""
        # Simple function
        code1 = "def foo(): pass"
        depth1 = calculate_syntax_tree_depth(code1)
        assert depth1 > 0
        
        # Nested structure
        code2 = """
        def outer():
            def inner():
                x = 1
                if x:
                    return x
        """
        depth2 = calculate_syntax_tree_depth(code2)
        assert depth2 > depth1
        
        # Invalid code should return 0
        invalid_code = "def foo("
        depth_invalid = calculate_syntax_tree_depth(invalid_code)
        assert depth_invalid == 0

    def test_syntax_tree_depth_empty(self):
        """Test empty code returns depth 0."""
        assert calculate_syntax_tree_depth("") == 0
        assert calculate_syntax_tree_depth("   ") == 0

class TestTokenFrequency:
    """Tests for token frequency calculation."""

    def test_token_frequency_counts_correctly(self):
        """Test that token frequencies are counted correctly."""
        log_content = "error error warning error info warning"
        freq = calculate_token_frequency(log_content)
        
        assert freq['error'] == 3
        assert freq['warning'] == 2
        assert freq['info'] == 1

    def test_token_frequency_case_insensitive(self):
        """Test that token frequency is case-insensitive."""
        log_content = "Error ERROR error"
        freq = calculate_token_frequency(log_content)
        
        assert freq['error'] == 3

class TestFeatureExtraction:
    """Integration tests for feature extraction."""

    def test_extract_features_from_log(self):
        """Test full feature extraction from a log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("""
            2024-01-01 10:00:00 INFO Starting
            2024-01-01 10:00:01 ERROR Retry attempt 1
            2024-01-01 10:00:02 INFO State changed to RECOVERING
            """)
            log_path = Path(f.name)
        
        try:
            features = extract_features_from_log(log_path)
            
            assert 'path' in features
            assert 'pragmatic_markers' in features
            assert 'token_frequency' in features
            assert 'syntax_tree_depth' in features
            
            # Check pragmatic markers
            assert features['pragmatic_markers']['error_recovery']['count'] >= 1
            assert features['pragmatic_markers']['state_transitions']['count'] >= 1
            
            # Check token frequency
            assert 'error' in features['token_frequency']
            
        finally:
            log_path.unlink()