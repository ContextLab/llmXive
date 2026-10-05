import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.detection.detect_llm_code import (
    calculate_confidence,
    detect_llm_generated_code,
    process_pr_diffs,
    main
)
from code.src.detection.schema import ConfidenceLevel, LLMCodeDetectionResult

class TestDetectLlmCode:
    def test_detect_llm_generated_code_with_explanation(self):
        """Test detection of LLM-generated code with explanatory comments."""
        diff_with_explanation = """
        diff --git a/test.py b/test.py
        index 1234567..abcdefg 100644
        --- a/test.py
        +++ b/test.py
        @@ -1,3 +1,5 @@
        # Here is a function to calculate the sum
        def add(a, b):
            return a + b
        """
        
        is_llm, confidence, patterns = detect_llm_generated_code(diff_with_explanation)
        
        assert is_llm is True
        assert confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
        assert len(patterns) > 0

    def test_detect_llm_generated_code_without_explanation(self):
        """Test that normal code without LLM markers is not detected."""
        normal_diff = """
        diff --git a/test.py b/test.py
        index 1234567..abcdefg 100644
        --- a/test.py
        +++ b/test.py
        @@ -1,3 +1,3 @@
        def add(a, b):
            return a + b
        +def subtract(a, b):
        +    return a - b
        """
        
        is_llm, confidence, patterns = detect_llm_generated_code(normal_diff)
        
        assert is_llm is False
        assert confidence == ConfidenceLevel.NONE
        assert len(patterns) == 0

    def test_detect_llm_generated_code_with_markdown_block(self):
        """Test detection of markdown code blocks."""
        diff_with_markdown = """
        diff --git a/test.py b/test.py
        index 1234567..abcdefg 100644
        --- a/test.py
        +++ b/test.py
        @@ -1,3 +1,5 @@
        ```python
        def hello():
            print("Hello, World!")
        ```
        """
        
        is_llm, confidence, patterns = detect_llm_generated_code(diff_with_markdown)
        
        assert is_llm is True
        assert len(patterns) > 0

    def test_calculate_confidence_high_matches(self):
        """Test confidence calculation with many matches."""
        confidence = calculate_confidence(
            matches=['pattern1', 'pattern2', 'pattern3'],
            total_lines=10,
            diff_hunks=1
        )
        
        assert 0.0 <= confidence <= 1.0

    def test_calculate_confidence_no_matches(self):
        """Test confidence calculation with no matches."""
        confidence = calculate_confidence(
            matches=[],
            total_lines=100,
            diff_hunks=1
        )
        
        assert confidence == 0.0

    def test_calculate_confidence_empty_diff(self):
        """Test confidence calculation with empty diff."""
        confidence = calculate_confidence(
            matches=[],
            total_lines=0,
            diff_hunks=1
        )
        
        assert confidence == 0.0

class TestProcessPrDiffs:
    def test_process_pr_diffs_basic(self):
        """Test basic processing of PR data."""
        pr_data = [
            {
                'pr_id': 'PR-001',
                'repo': 'test/repo',
                'diff': '# Here is a function\ndef test(): pass'
            }
        ]
        
        results = process_pr_diffs(pr_data)
        
        assert len(results) == 1
        assert results[0].pr_id == 'PR-001'
        assert results[0].repo == 'test/repo'
        assert results[0].llm_code_flag is True

    def test_process_pr_diffs_empty_diff(self):
        """Test processing of PR with empty diff."""
        pr_data = [
            {
                'pr_id': 'PR-002',
                'repo': 'test/repo',
                'diff': ''
            }
        ]
        
        results = process_pr_diffs(pr_data)
        
        assert len(results) == 1
        assert results[0].llm_code_flag is False
        assert results[0].error_message is None

    def test_process_pr_diffs_multiple_prs(self):
        """Test processing multiple PRs."""
        pr_data = [
            {
                'pr_id': 'PR-003',
                'repo': 'test/repo',
                'diff': '# Here is code\ndef a(): pass'
            },
            {
                'pr_id': 'PR-004',
                'repo': 'test/repo',
                'diff': 'def b(): pass'
            }
        ]
        
        results = process_pr_diffs(pr_data)
        
        assert len(results) == 2
        assert results[0].llm_code_flag is True
        assert results[1].llm_code_flag is False

class TestLLMCodeDetectionResult:
    def test_llm_code_detection_result_to_dict(self):
        """Test conversion of result to dictionary."""
        result = LLMCodeDetectionResult(
            pr_id='PR-005',
            repo='test/repo',
            llm_code_flag=True,
            confidence=ConfidenceLevel.HIGH,
            matched_patterns=['pattern1'],
            file_paths=['file.py'],
            error_message=None
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['pr_id'] == 'PR-005'
        assert result_dict['llm_code_flag'] is True
        assert result_dict['confidence'] == 'HIGH'
        assert 'pattern1' in result_dict['matched_patterns']
        assert 'file.py' in result_dict['file_paths']

    def test_llm_code_detection_result_with_error(self):
        """Test result with error message."""
        result = LLMCodeDetectionResult(
            pr_id='PR-006',
            repo='test/repo',
            llm_code_flag=False,
            confidence=ConfidenceLevel.NONE,
            matched_patterns=[],
            file_paths=[],
            error_message='Test error'
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['error_message'] == 'Test error'
        assert result_dict['llm_code_flag'] is False

@patch('code.src.detection.detect_llm_code.get_paths')
@patch('code.src.detection.detect_llm_code.ensure_directories')
@patch('code.src.detection.detect_llm_code.json.load')
@patch('code.src.detection.detect_llm_code.json.dump')
@patch('builtins.open')
def test_main(mock_open, mock_dump, mock_json_load, mock_ensure_dirs, mock_get_paths, caplog):
    """Test main function execution."""
    import logging
    
    # Setup mock paths
    mock_paths = {
        'data_raw': Path('/tmp/data/raw'),
        'data_derived': Path('/tmp/data/derived')
    }
    mock_get_paths.return_value = mock_paths
    
    # Setup mock data
    mock_json_load.return_value = [
        {
            'pr_id': 'PR-TEST',
            'repo': 'test/repo',
            'diff': '# Here is a function\ndef test(): pass'
        }
    ]
    
    # Mock file existence
    with patch('pathlib.Path.exists', return_value=True):
        main()
    
    # Verify output was written
    mock_dump.assert_called_once()
    
    # Check log messages
    assert any('Detection complete' in str(record.message) for record in caplog.records)
