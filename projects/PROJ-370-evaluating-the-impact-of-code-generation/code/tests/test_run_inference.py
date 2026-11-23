"""
test_run_inference.py

Unit tests for run_inference.py module.
Tests cover:
- parse_llm_output function
- process_single_pr function
- run_batch_inference function
- save_results function
- Error handling and retry logic
"""

import json
import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from dataclasses import asdict

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.inference.run_inference import (
    parse_llm_output,
    process_single_pr,
    run_batch_inference,
    save_results,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
    MAX_LATENCY_PER_PR_SECONDS,
    MEMORY_LIMIT_BYTES
)
from code.src.inference.schema import InferenceStatus
from code.src.utils.timeout_wrapper import TimeoutExceeded
from code.src.utils.memory_watchdog import MemoryLimitExceeded

# Mock fixtures
@pytest.fixture
def mock_pr_data():
    """Create mock PR data for testing"""
    return {
        'pr_id': 'test-pr-123',
        'file_path': 'test_file.py',
        'diff': '+def new_function():\n- old_code\n+ new_code',
        'linked_issue_ids': [],
        'reviewers': ['user1', 'user2']
    }

@pytest.fixture
def mock_model():
    """Create mock model for testing"""
    model = MagicMock()
    model.device = 'cpu'
    model.generate = MagicMock()
    return model

@pytest.fixture
def mock_tokenizer():
    """Create mock tokenizer for testing"""
    tokenizer = MagicMock()
    tokenizer.eos_token_id = 0
    tokenizer.decode = MagicMock(return_value='{"severity": "major", "description": "test bug"}')
    tokenizer.return_value = {
        'input_ids': torch.tensor([[1, 2, 3]]),
        'attention_mask': torch.tensor([[1, 1, 1]])
    }
    return tokenizer

@pytest.fixture
def mock_config():
    """Create mock configuration"""
    return {
        'max_input_length': 4096,
        'max_new_tokens': 512,
        'model_id': 'test-model'
    }

class TestParseLLMOutput:
    """Tests for parse_llm_output function"""

    def test_parse_valid_json(self):
        """Test parsing valid JSON output"""
        llm_output = '{"severity": "critical", "description": "Bug found", "line_start": 10, "line_end": 15}'
        result = parse_llm_output(llm_output)
        
        assert result['severity'] == 'critical'
        assert result['description'] == 'Bug found'
        assert result['line_start'] == 10
        assert result['line_end'] == 15

    def test_parse_json_with_extra_text(self):
        """Test parsing JSON with surrounding text"""
        llm_output = 'Here is the result: {"severity": "minor", "description": "Style issue"}'
        result = parse_llm_output(llm_output)
        
        assert result['severity'] == 'minor'
        assert result['description'] == 'Style issue'

    def test_parse_json_with_markdown(self):
        """Test parsing JSON in markdown code block"""
        llm_output = '```json\n{"severity": "major", "description": "Logic error"}\n```'
        result = parse_llm_output(llm_output)
        
        assert result['severity'] == 'major'
        assert result['description'] == 'Logic error'

    def test_parse_invalid_json_no_braces(self):
        """Test parsing invalid JSON without braces"""
        llm_output = 'This is just plain text without JSON'
        
        with pytest.raises(ValueError, match="No JSON object found"):
            parse_llm_output(llm_output)

    def test_parse_invalid_json_malformed(self):
        """Test parsing malformed JSON"""
        llm_output = '{"severity": "major", "description": "missing quote}'
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_llm_output(llm_output)

class TestProcessSinglePR:
    """Tests for process_single_pr function"""

    @patch('code.src.inference.run_inference.get_bug_detection_prompt')
    @patch('code.src.inference.run_inference.create_inference_request')
    def test_process_valid_pr(self, mock_create_request, mock_get_prompt, mock_pr_data, mock_model, mock_tokenizer, mock_config):
        """Test processing a valid PR"""
        mock_get_prompt.return_value = "Test prompt"
        mock_create_request.return_value = MagicMock()
        
        # Mock the generate method
        mock_tokenizer.decode.return_value = '{"severity": "major", "description": "test"}'
        
        result, is_error = process_single_pr(mock_pr_data, mock_model, mock_tokenizer, mock_config)
        
        assert is_error is False
        assert result is not None
        assert result['pr_id'] == 'test-pr-123'
        assert result['file_path'] == 'test_file.py'
        assert result['llm_error_flag'] is False

    def test_process_empty_diff(self, mock_pr_data, mock_model, mock_tokenizer, mock_config, caplog):
        """Test processing PR with empty diff"""
        mock_pr_data['diff'] = ''
        
        with caplog.at_level(logging.WARNING):
            result, is_error = process_single_pr(mock_pr_data, mock_model, mock_tokenizer, mock_config)
        
        assert is_error is True
        assert result is None
        assert "No diff content" in caplog.text

    @patch('code.src.inference.run_inference.get_bug_detection_prompt')
    @patch('code.src.inference.run_inference.create_inference_request')
    def test_process_timeout_error(self, mock_create_request, mock_get_prompt, mock_pr_data, mock_model, mock_tokenizer, mock_config):
        """Test processing PR with timeout error"""
        mock_get_prompt.return_value = "Test prompt"
        mock_create_request.return_value = MagicMock()
        
        # Mock timeout
        mock_model.generate.side_effect = TimeoutExceeded("Test timeout")
        
        result, is_error = process_single_pr(mock_pr_data, mock_model, mock_tokenizer, mock_config)
        
        assert is_error is True
        assert result is None

    @patch('code.src.inference.run_inference.get_bug_detection_prompt')
    @patch('code.src.inference.run_inference.create_inference_request')
    def test_process_memory_limit_error(self, mock_create_request, mock_get_prompt, mock_pr_data, mock_model, mock_tokenizer, mock_config):
        """Test processing PR with memory limit error"""
        mock_get_prompt.return_value = "Test prompt"
        mock_create_request.return_value = MagicMock()
        
        # Mock memory limit exceeded
        mock_model.generate.side_effect = MemoryLimitExceeded("Memory exceeded")
        
        result, is_error = process_single_pr(mock_pr_data, mock_model, mock_tokenizer, mock_config)
        
        assert is_error is True
        assert result is None

class TestRunBatchInference:
    """Tests for run_batch_inference function"""

    @patch('code.src.inference.run_inference.process_single_pr')
    def test_batch_success(self, mock_process_single, mock_pr_data, mock_model, mock_tokenizer, mock_config):
        """Test successful batch inference"""
        mock_process_single.return_value = ({'severity': 'major', 'description': 'test'}, False)
        
        prs = [mock_pr_data, mock_pr_data.copy(), mock_pr_data.copy()]
        results = run_batch_inference(prs, mock_model, mock_tokenizer, mock_config)
        
        assert len(results) == 3
        assert all(not r.get('llm_error_flag', False) for r in results)

    @patch('code.src.inference.run_inference.process_single_pr')
    def test_batch_with_errors(self, mock_process_single, mock_pr_data, mock_model, mock_tokenizer, mock_config):
        """Test batch inference with some errors"""
        # First PR succeeds, second fails, third succeeds
        mock_process_single.side_effect = [
            ({'severity': 'major'}, False),
            (None, True),
            ({'severity': 'minor'}, False)
        ]
        
        prs = [mock_pr_data, mock_pr_data.copy(), mock_pr_data.copy()]
        results = run_batch_inference(prs, mock_model, mock_tokenizer, mock_config)
        
        assert len(results) == 3
        assert results[0].get('llm_error_flag') is False
        assert results[1].get('llm_error_flag') is True
        assert results[2].get('llm_error_flag') is False

    @patch('code.src.inference.run_inference.process_single_pr')
    def test_batch_retry_logic(self, mock_process_single, mock_pr_data, mock_model, mock_tokenizer, mock_config, monkeypatch):
        """Test retry logic for JSON parsing errors"""
        # Mock time.sleep to avoid actual delay
        monkeypatch.setattr('code.src.inference.run_inference.time.sleep', lambda x: None)
        
        # Fail twice, then succeed
        mock_process_single.side_effect = [
            (None, False),  # First attempt fails (no result, not error - should retry)
            (None, False),  # Second attempt fails
            ({'severity': 'major'}, False)  # Third attempt succeeds
        ]
        
        prs = [mock_pr_data]
        results = run_batch_inference(prs, mock_model, mock_tokenizer, mock_config)
        
        # Should have retried and eventually succeeded
        assert len(results) == 1
        assert results[0].get('llm_error_flag') is False

    @patch('code.src.inference.run_inference.process_single_pr')
    def test_batch_max_retries_exceeded(self, mock_process_single, mock_pr_data, mock_model, mock_tokenizer, mock_config, monkeypatch):
        """Test batch inference when max retries are exceeded"""
        monkeypatch.setattr('code.src.inference.run_inference.time.sleep', lambda x: None)
        
        # Always fail
        mock_process_single.return_value = (None, False)
        
        prs = [mock_pr_data]
        results = run_batch_inference(prs, mock_model, mock_tokenizer, mock_config)
        
        # Should mark as error after max retries
        assert len(results) == 1
        assert results[0].get('llm_error_flag') is True
        assert 'error_message' in results[0]

class TestSaveResults:
    """Tests for save_results function"""

    def test_save_results_creates_file(self, tmp_path):
        """Test that save_results creates the output file"""
        results = [
            {'pr_id': '1', 'severity': 'major', 'llm_error_flag': False},
            {'pr_id': '2', 'severity': 'minor', 'llm_error_flag': True}
        ]
        
        output_path = tmp_path / 'test_results.json'
        save_results(results, output_path, split_name="test")
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['split'] == 'test'
        assert data['total_processed'] == 2
        assert data['successful'] == 1
        assert data['errors'] == 1
        assert len(data['results']) == 2

    def test_save_results_correct_counts(self, tmp_path):
        """Test that save_results counts successes and errors correctly"""
        results = [
            {'pr_id': '1', 'llm_error_flag': False},
            {'pr_id': '2', 'llm_error_flag': False},
            {'pr_id': '3', 'llm_error_flag': True},
            {'pr_id': '4', 'llm_error_flag': True}
        ]
        
        output_path = tmp_path / 'test_results.json'
        save_results(results, output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['successful'] == 2
        assert data['errors'] == 2

class TestRunInferenceModule:
    """Tests for module-level constants and structure"""

    def test_constants_defined(self):
        """Test that required constants are defined"""
        assert MAX_RETRIES >= 1
        assert RETRY_DELAY_SECONDS >= 0
        assert MAX_LATENCY_PER_PR_SECONDS > 0
        assert MEMORY_LIMIT_BYTES > 0

    def test_main_function_exists(self):
        """Test that main function exists"""
        from code.src.inference.run_inference import main
        assert callable(main)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
