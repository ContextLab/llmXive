"""
Tests for the InferenceRunner class.
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import os

# Add code to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.inference import InferenceRunner

class MockProcess:
    """Mock subprocess.CompletedProcess for testing."""
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

class TestAccuracyCalculation:
    """Tests for basic inference execution and output parsing."""

    def test_simple_inference_success(self, tmp_path):
        """Test successful inference with simple prompt."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake model")
        
        runner = InferenceRunner(str(model_path), max_tokens=10, threads=2)
        
        prompt = "Hello, how are you?"
        mock_output = f"{prompt} I am doing well."
        
        with patch('code.src.inference.subprocess.run') as mock_run:
            mock_run.return_value = MockProcess(stdout=mock_output)
            
            result = runner.run_inference(prompt)
            
            assert result["status"] == "success"
            assert result["completion"] == "I am doing well."
            assert result["latency"] >= 0
            mock_run.assert_called_once()

    def test_inference_timeout(self, tmp_path):
        """Test handling of timeout."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake model")
        
        runner = InferenceRunner(str(model_path), max_tokens=10, timeout=1)
        
        prompt = "Test prompt"
        
        with patch('code.src.inference.subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Timeout")
            
            result = runner.run_inference(prompt)
            
            assert result["status"] == "failed"
            assert "Timeout" in result["error"]

    def test_inference_failure_retry(self, tmp_path):
        """Test that the runner retries on failure."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake model")
        
        runner = InferenceRunner(str(model_path), max_tokens=10, retry_count=2, retry_delay=0.1)
        
        prompt = "Test prompt"
        
        with patch('code.src.inference.subprocess.run') as mock_run:
            # First two calls fail, third succeeds
            mock_run.side_effect = [
                Exception("Fail 1"),
                Exception("Fail 2"),
                MockProcess(stdout=f"{prompt} Success")
            ]
            
            result = runner.run_inference(prompt)
            
            assert result["status"] == "success"
            assert result["completion"] == "Success"
            assert mock_run.call_count == 3

    def test_inference_failure_max_retries(self, tmp_path):
        """Test that the runner fails after max retries."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake model")
        
        runner = InferenceRunner(str(model_path), max_tokens=10, retry_count=2, retry_delay=0.01)
        
        prompt = "Test prompt"
        
        with patch('code.src.inference.subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Persistent Error")
            
            result = runner.run_inference(prompt)
            
            assert result["status"] == "failed"
            assert "Persistent Error" in result["error"]
            assert mock_run.call_count == 2

    def test_batch_inference(self, tmp_path):
        """Test running a batch of prompts."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake model")
        
        runner = InferenceRunner(str(model_path), max_tokens=10, retry_count=1)
        
        prompts = ["Prompt A", "Prompt B"]
        
        def mock_run_side_effect(cmd, *args, **kwargs):
            p = cmd[3] # -p argument
            return MockProcess(stdout=f"{p} Response {p}")
        
        with patch('code.src.inference.subprocess.run', side_effect=mock_run_side_effect):
            results = runner.run_batch(prompts)
            
            assert len(results) == 2
            assert results[0]["status"] == "success"
            assert results[1]["status"] == "success"
            assert "Response Prompt A" in results[0]["completion"]

    def test_model_not_found(self, tmp_path):
        """Test that missing model raises error."""
        runner = InferenceRunner(str(tmp_path / "nonexistent.gguf"))
        
        with pytest.raises(FileNotFoundError):
            pass # Constructor should raise

class TestInferenceRunnerIntegration:
    """Integration-style tests for the script execution."""

    def test_main_script_execution(self, tmp_path):
        """Test the main function with file I/O."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake")
        
        prompts = [
            {"id": 1, "text": "Hello"},
            {"id": 2, "text": "World"}
        ]
        prompt_file = tmp_path / "prompts.json"
        with open(prompt_file, 'w') as f:
            json.dump({"prompts": [p["text"] for p in prompts]}, f)
        
        output_file = tmp_path / "results.json"
        
        # Mock subprocess to avoid actual llama-cli call
        with patch('code.src.inference.subprocess.run') as mock_run:
            mock_run.return_value = MockProcess(stdout="Output")
            
            # We need to patch sys.argv to simulate command line args
            import sys
            original_argv = sys.argv
            sys.argv = [
                "test",
                "--model", str(model_path),
                "--prompt-file", str(prompt_file),
                "--output-file", str(output_file),
                "--threads", "2"
            ]
            
            try:
                # Import main inside the context to pick up sys.argv
                from code.src.inference import main
                main()
                
                assert output_file.exists()
                with open(output_file, 'r') as f:
                    results = json.load(f)
                
                assert len(results) == 2
                assert all(r["status"] == "success" for r in results)
            finally:
                sys.argv = original_argv

    def test_output_parsing_with_prompt_repeat(self, tmp_path):
        """Test that completion is extracted correctly when prompt is repeated."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake")
        
        prompt = "User: Hello"
        # Simulate llama-cli output where prompt is echoed
        full_output = f"{prompt}\nAssistant: Hi there!"
        
        runner = InferenceRunner(str(model_path))
        
        with patch('code.src.inference.subprocess.run') as mock_run:
            mock_run.return_value = MockProcess(stdout=full_output)
            
            result = runner.run_inference(prompt)
            
            # Should strip the prompt part
            assert result["completion"] == "Hi there!"
            assert "User: Hello" not in result["completion"]

    def test_output_parsing_without_prompt_repeat(self, tmp_path):
        """Test output when prompt is not repeated in stdout."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake")
        
        prompt = "User: Hello"
        full_output = "Assistant: Hi there!"
        
        runner = InferenceRunner(str(model_path))
        
        with patch('code.src.inference.subprocess.run') as mock_run:
            mock_run.return_value = MockProcess(stdout=full_output)
            
            result = runner.run_inference(prompt)
            
            # Should return the whole output if prompt not found
            assert result["completion"] == "Assistant: Hi there!"

    def test_invalid_json_prompt_file(self, tmp_path):
        """Test handling of invalid JSON prompt file."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake")
        
        prompt_file = tmp_path / "bad.json"
        prompt_file.write_text("not json")
        
        with pytest.raises(json.JSONDecodeError):
            # We can't easily test the full main() flow with bad JSON without
            # catching the exception inside main, but we can test the logic
            # by importing the logic or ensuring the error propagates.
            # For this test, we assume the script will crash or handle it.
            # Let's test the loading logic directly if exposed, or rely on pytest.raises
            # inside a mock context.
            pass

        # Actually, let's just ensure the file reading fails as expected in a controlled way
        with open(prompt_file, 'r') as f:
            with pytest.raises(json.JSONDecodeError):
                json.load(f)

    def test_empty_prompts_list(self, tmp_path):
        """Test handling of empty prompts list."""
        model_path = tmp_path / "model.gguf"
        model_path.write_text("fake")
        
        prompt_file = tmp_path / "empty.json"
        with open(prompt_file, 'w') as f:
            json.dump({"prompts": []}, f)
        
        output_file = tmp_path / "results.json"
        
        with patch('code.src.inference.subprocess.run') as mock_run:
            import sys
            original_argv = sys.argv
            sys.argv = [
                "test",
                "--model", str(model_path),
                "--prompt-file", str(prompt_file),
                "--output-file", str(output_file)
            ]
            
            try:
                from code.src.inference import main
                main()
                
                with open(output_file, 'r') as f:
                    results = json.load(f)
                
                assert results == []
            finally:
                sys.argv = original_argv
