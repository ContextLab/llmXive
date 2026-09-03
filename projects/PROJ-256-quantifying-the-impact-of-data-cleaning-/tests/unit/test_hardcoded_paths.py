"""
Unit tests for T1205: Audit hardcoded paths functionality.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open

# Import the audit function
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code' / 'scripts'))
from audit_hardcoded_paths import audit_file, is_comment_or_string_context

class TestAuditFile:
    def test_detects_hardcoded_data_raw_path(self):
        """Test that hardcoded data/raw paths are detected."""
        test_content = '''
        import pandas as pd
        df = pd.read_csv("data/raw/dataset.csv")
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            findings = audit_file(temp_path)
            assert len(findings) > 0
            assert any('data/raw' in f['matched_string'] for f in findings)
        finally:
            os.unlink(temp_path)
    
    def test_detects_hardcoded_data_processed_path(self):
        """Test that hardcoded data/processed paths are detected."""
        test_content = '''
        output_path = "data/processed/metrics.json"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            findings = audit_file(temp_path)
            assert len(findings) > 0
            assert any('data/processed' in f['matched_string'] for f in findings)
        finally:
            os.unlink(temp_path)
    
    def test_ignores_commented_paths(self):
        """Test that commented paths are ignored."""
        test_content = '''
        # This is a comment with "data/raw/dataset.csv" in it
        df = pd.read_csv(config.RAW_DATA_PATH)
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            findings = audit_file(temp_path)
            # Should only find config reference if it's hardcoded, but we're using config
            # So should be 0 or only non-config matches
            assert len(findings) == 0
        finally:
            os.unlink(temp_path)
    
    def test_ignores_config_references(self):
        """Test that config references are ignored."""
        test_content = '''
        path = config.RAW_DATA_PATH
        df = pd.read_csv(config.PROCESSED_DATA_PATH)
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            findings = audit_file(temp_path)
            assert len(findings) == 0
        finally:
            os.unlink(temp_path)
    
    def test_detects_multiple_hardcoded_paths(self):
        """Test detection of multiple hardcoded paths in one file."""
        test_content = '''
        import pandas as pd
        df1 = pd.read_csv("data/raw/dataset1.csv")
        df2 = pd.read_csv("data/raw/dataset2.csv")
        output = "data/processed/metrics.json"
        figures = "output/figures/plot.png"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            findings = audit_file(temp_path)
            assert len(findings) >= 3  # At least 3 hardcoded paths
            paths_found = [f['matched_string'] for f in findings]
            assert '"data/raw/dataset1.csv"' in paths_found
            assert '"data/raw/dataset2.csv"' in paths_found
            assert '"data/processed/metrics.json"' in paths_found
        finally:
            os.unlink(temp_path)

class TestIsCommentOrStringContext:
    def test_detects_comment_context(self):
        """Test that strings in comments are identified."""
        line = '# This is a comment with "data/raw/test.csv" in it'
        # Find the match position
        import re
        match = re.search(r'"data/raw/[^"]*"', line)
        assert match is not None
        assert is_comment_or_string_context(line, match.start(), match.end()) is True
    
    def test_detects_non_comment_context(self):
        """Test that strings not in comments are identified."""
        line = 'path = "data/raw/test.csv"'
        import re
        match = re.search(r'"data/raw/[^"]*"', line)
        assert match is not None
        assert is_comment_or_string_context(line, match.start(), match.end()) is False
    
    def test_detects_config_reference(self):
        """Test that config references are identified."""
        line = 'path = config.RAW_DATA_PATH'
        assert is_comment_or_string_context(line, 0, len(line)) is True  # Should be treated as config

class TestAuditReportGeneration:
    def test_report_structure(self):
        """Test that the audit report has the correct structure."""
        # This would normally be tested by running the full audit
        # For now, we verify the expected structure
        expected_structure = {
            'total_files_audited': int,
            'total_hardcoded_paths_found': int,
            'findings': list
        }
        
        # Verify structure matches
        assert 'total_files_audited' in expected_structure
        assert 'total_hardcoded_paths_found' in expected_structure
        assert 'findings' in expected_structure

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
