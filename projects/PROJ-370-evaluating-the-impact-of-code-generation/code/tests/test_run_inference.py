import json
import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.inference.run_inference import (
    parse_llm_output,
    process_single_pr,
    run_batch_inference,
    save_results
)

@pytest.fixture
def mock_pr_data():
    return {
        'pr_id': 'test-pr-001',
        'diff': 'def foo():\n    return 42',
        'file_path': 'test.py'
    }

@pytest.fixture
def mock_model():
    return MagicMock()

@pytest.fixture
def mock_tokenizer():
    tokenizer = MagicMock()
    tokenizer.eos_token_id = 50256
    return tokenizer

class TestParseLLMOutput:
    def test_valid_json_output(self):
        raw_output = '{"severity": "major", "description": "Potential bug", "file_path": "test.py", "line_start": 1, "line_end": 5}'
        result = parse_llm_output(raw_output, 'pr-001')
        
        assert result['pr_id'] == 'pr-001'
        assert result['severity'] == 'major'
        assert result['description'] == 'Potential bug'
        assert result['file_path'] == 'test.py'
        assert result['line_start'] == 1
        assert result['line_end'] == 5
        assert result['llm_error_flag'] is False

    def test_missing_required_field(self):
        raw_output = '{"description": "Missing severity"}'
        result = parse_llm_output(raw_output, 'pr-002')
        
        assert result['llm_error_flag'] is True
        assert 'Parse error' in result['description']

    def test_invalid_json(self):
        raw_output = 'not valid json'
        result = parse_llm_output(raw_output, 'pr-003')
        
        assert result['llm_error_flag'] is True
        assert 'Parse error' in result['description']

    def test_default_severity_on_missing(self):
        raw_output = '{"description": "No severity specified"}'
        result = parse_llm_output(raw_output, 'pr-004')
        
        assert result['severity'] == 'minor'
        assert result['llm_error_flag'] is False

class TestProcessSinglePR:
    @patch('code.src.inference.run_inference.get_bug_detection_prompt')
    @patch('code.src.inference.run_inference.check_timeout')
    @patch('code.src.inference.run_inference.check_memory_limit')
    def test_successful_processing(
        self, 
        mock_mem_check, 
        mock_timeout, 
        mock_get_prompt,
        mock_pr_data,
        mock_model,
        mock_tokenizer
    ):
        mock_timeout.return_value = False
        mock_get_prompt.return_value = "Prompt for test-pr-001"
        mock_tokenizer.return_value = MagicMock()
        mock_model.generate.return_value = [[1, 2, 3]]
        mock_tokenizer.decode.return_value = '{"severity": "critical", "description": "Critical bug found", "file_path": "test.py", "line_start": 1, "line_end": 10}'
        
        result = process_single_pr(mock_pr_data, mock_model, mock_tokenizer)
        
        assert result['pr_id'] == 'test-pr-001'
        assert result['severity'] == 'critical'
        assert result['description'] == 'Critical bug found'
        assert result['llm_error_flag'] is False

    @patch('code.src.inference.run_inference.check_timeout')
    def test_timeout_handling(self, mock_timeout, mock_pr_data, mock_model, mock_tokenizer):
        mock_timeout.return_value = True
        
        result = process_single_pr(mock_pr_data, mock_model, mock_tokenizer)
        
        assert result['llm_error_flag'] is True
        assert 'Timeout' in result['description']

    @patch('code.src.inference.run_inference.check_memory_limit')
    @patch('code.src.inference.run_inference.check_timeout')
    def test_memory_limit_exceeded(self, mock_timeout, mock_mem_check, mock_pr_data, mock_model, mock_tokenizer):
        from code.src.utils.memory_watchdog import MemoryLimitExceeded
        
        mock_timeout.return_value = False
        mock_mem_check.side_effect = MemoryLimitExceeded("Memory limit exceeded")
        
        result = process_single_pr(mock_pr_data, mock_model, mock_tokenizer)
        
        assert result['llm_error_flag'] is True
        assert 'Memory' in result['description']

class TestRunBatchInference:
    @patch('code.src.inference.run_inference.process_single_pr')
    def test_batch_processing(self, mock_process, mock_model, mock_tokenizer):
        prs = [
            {'pr_id': 'pr-001', 'diff': 'diff1'},
            {'pr_id': 'pr-002', 'diff': 'diff2'},
            {'pr_id': 'pr-003', 'diff': 'diff3'}
        ]
        
        mock_process.side_effect = [
            {'pr_id': 'pr-001', 'severity': 'major', 'llm_error_flag': False},
            {'pr_id': 'pr-002', 'severity': 'minor', 'llm_error_flag': False},
            {'pr_id': 'pr-003', 'llm_error_flag': True}
        ]
        
        results = run_batch_inference(prs, mock_model, mock_tokenizer)
        
        assert len(results) == 3
        assert results[0]['pr_id'] == 'pr-001'
        assert results[1]['pr_id'] == 'pr-002'
        assert results[2]['llm_error_flag'] is True

class TestSaveResults:
    def test_save_results_creates_file(self, tmp_path):
        results = [
            {'pr_id': 'pr-001', 'severity': 'major', 'description': 'Bug 1', 'llm_error_flag': False},
            {'pr_id': 'pr-002', 'llm_error_flag': True}
        ]
        
        output_path = tmp_path / 'test_output.json'
        save_results(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 2
        assert saved_data[0]['pr_id'] == 'pr-001'
        assert saved_data[1]['llm_error_flag'] is True
