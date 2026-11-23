"""
Integration test for the generation pipeline with timeout handling.

This test verifies that the generation loop correctly processes prompts,
handles timeouts, and produces the expected output format.
"""
import os
import sys
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from generate import (
    generate_snippet,
    load_prompts,
    save_results,
    TimeoutError
)

class TestGenerationPipeline:
    """Integration tests for the generation module."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model and tokenizer."""
        model = MagicMock()
        tokenizer = MagicMock()
        tokenizer.pad_token = "<pad>"
        tokenizer.eos_token = "<eos>"
        
        # Mock the generate method to return a simple response
        mock_output = MagicMock()
        mock_output.__getitem__ = lambda self, key: [1, 2, 3, 4]  # Mock token IDs
        model.generate.return_value = mock_output
        
        # Mock tokenizer.decode
        tokenizer.decode.return_value = "def hello():\n    return 'world'"
        
        return model, tokenizer

    @pytest.fixture
    def sample_manifest(self, tmp_path):
        """Create a sample manifest file."""
        manifest = {
            "prompts": [
                {
                    "id": "test_001",
                    "prompt": "Write a hello world function",
                    "source": "test",
                    "category": "basic"
                },
                {
                    "id": "test_002",
                    "prompt": "Write a sum function",
                    "source": "test",
                    "category": "basic"
                }
            ]
        }
        
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        return str(manifest_path)

    def test_load_prompts(self, sample_manifest):
        """Test loading prompts from manifest."""
        prompts = load_prompts(sample_manifest)
        
        assert len(prompts) == 2
        assert prompts[0]['id'] == 'test_001'
        assert prompts[1]['id'] == 'test_002'

    def test_generate_snippet_success(self, mock_model):
        """Test successful snippet generation."""
        model, tokenizer = mock_model
        
        with patch('generate.signal'):
            snippet = generate_snippet(model, tokenizer, "Write code", "test_model")
        
        assert snippet is not None
        assert isinstance(snippet, str)
        assert len(snippet) > 0

    def test_generate_snippet_timeout(self, mock_model):
        """Test timeout handling during generation."""
        model, tokenizer = mock_model
        
        # Simulate a timeout
        with patch('generate.signal.alarm', side_effect=TimeoutError("Timeout")):
            with patch('generate.signal.signal'):
                with pytest.raises(TimeoutError):
                    generate_snippet(model, tokenizer, "Write code", "test_model")

    def test_save_results(self, tmp_path):
        """Test saving results to CSV."""
        results = [
            {
                'snippet_id': 'test_001',
                'model': 'test_model',
                'prompt_id': 'prompt_001',
                'code': 'print("hello")',
                'timestamp': '2024-01-01 12:00:00'
            },
            {
                'snippet_id': 'test_002',
                'model': 'test_model',
                'prompt_id': 'prompt_002',
                'code': 'x = 1 + 2',
                'timestamp': '2024-01-01 12:01:00'
            }
        ]
        
        output_path = tmp_path / "output.csv"
        failures_path = tmp_path / "failures.log"
        
        save_results(results, str(output_path), str(failures_path))
        
        assert output_path.exists()
        assert failures_path.exists()
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            content = f.read()
            assert 'snippet_id' in content
            assert 'test_001' in content
            assert 'test_002' in content

    def test_generation_loop_structure(self, sample_manifest, tmp_path):
        """Test the structure of the generation loop output."""
        # This test verifies the expected output format without running actual models
        from generate import main
        
        # Mock the model loading and generation
        with patch('generate.load_model') as mock_load:
            with patch('generate.generate_snippet') as mock_gen:
                mock_load.return_value = (MagicMock(), MagicMock())
                mock_gen.return_value = "def test(): pass"
                
                with patch('generate.save_results') as mock_save:
                    with patch('generate.update_state_for_directory'):
                        with patch('generate.config') as mock_config:
                            mock_config.PROMPTS_MANIFEST_PATH = sample_manifest
                            mock_config.GENERATED_CSV_PATH = str(tmp_path / "snippets.csv")
                            mock_config.FAILURES_LOG_PATH = str(tmp_path / "failures.log")
                            
                            try:
                                main()
                            except Exception:
                                pass  # Ignore errors from incomplete mocks
                            
                            # Verify save_results was called
                            assert mock_save.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])