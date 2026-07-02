"""
Unit tests for the extract_changed_lines function in data_loader.py.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# We need to mock the data loading and config to avoid real downloads in unit tests
# But we want to test the logic of extract_changed_lines

@pytest.fixture
def sample_diff_text():
    """Sample unified diff text for testing."""
    return """--- a/src/main/java/org/example/Calculator.java
+++ b/src/main/java/org/example/Calculator.java
@@ -1,5 +1,6 @@
 public class Calculator {
-    public int add(int a, int b) { return a + b; }
+    public int add(int a, int b) {
+        return a + b;
+    }
 
     public int subtract(int a, int b) { return a - b; }
 }
"""

@pytest.fixture
def mock_dataframe(sample_diff_text):
    """Create a mock DataFrame with diff data."""
    data = {
        'bug_id': ['bug_001', 'bug_002'],
        'commit_diff': [sample_diff_text, sample_diff_text]
    }
    return pd.DataFrame(data)

def test_extract_changed_lines_logic(sample_diff_text, mock_dataframe):
    """Test that changed lines are correctly parsed from diff text."""
    from data_loader import extract_changed_lines
    
    # Mock load_defects4j_data to return our mock dataframe
    with patch('data_loader.load_defects4j_data', return_value=mock_dataframe):
        # Mock get_data_dir and get_output_dir to use temp directories
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            output_dir = Path(tmpdir) / "output"
            data_dir.mkdir()
            output_dir.mkdir()
            
            with patch('data_loader.get_data_dir', return_value=data_dir):
                with patch('data_loader.get_output_dir', return_value=output_dir):
                    with patch('data_loader.ensure_directories'):
                        result = extract_changed_lines()
                        
                        # Verify result structure
                        assert isinstance(result, dict)
                        assert 'bug_001' in result
                        assert 'bug_002' in result
                        
                        # Verify line numbers are sets of integers
                        for bug_id, lines in result.items():
                            assert isinstance(lines, set)
                            assert all(isinstance(line, int) for line in lines)
                            
                        # Verify specific lines were captured (based on the sample diff)
                        # The added lines are at positions 3, 4, 5 in the new file (1-indexed in diff, but we track new file lines)
                        # In the diff:
                        # Line 3: +    public int add(int a, int b) {
                        # Line 4: +        return a + b;
                        # Line 5: +    }
                        bug_1_lines = result['bug_001']
                        assert 3 in bug_1_lines
                        assert 4 in bug_1_lines
                        assert 5 in bug_1_lines

def test_extract_changed_lines_output_file(sample_diff_text, mock_dataframe):
    """Test that the output file is created correctly."""
    from data_loader import extract_changed_lines
    
    with patch('data_loader.load_defects4j_data', return_value=mock_dataframe):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            output_dir = Path(tmpdir) / "output"
            data_dir.mkdir()
            output_dir.mkdir()
            
            with patch('data_loader.get_data_dir', return_value=data_dir):
                with patch('data_loader.get_output_dir', return_value=output_dir):
                    with patch('data_loader.ensure_directories'):
                        extract_changed_lines()
                        
                        # Verify output file exists
                        output_file = output_dir / "changed_lines.json"
                        assert output_file.exists()
                        
                        # Verify content
                        with open(output_file, 'r') as f:
                            saved_data = json.load(f)
                            
                        assert 'bug_001' in saved_data
                        assert 'bug_002' in saved_data
                        # Values should be lists (JSON serializable)
                        assert isinstance(saved_data['bug_001'], list)
                        assert all(isinstance(x, int) for x in saved_data['bug_001'])
