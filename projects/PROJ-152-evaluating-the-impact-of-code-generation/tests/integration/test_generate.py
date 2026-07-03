import os
import sys
import tempfile
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate import TimeoutError, timeout_handler, load_model, generate_snippet, load_prompts, save_results

@pytest.fixture
def sample_prompts():
    """Create a temporary manifest file with sample prompts for testing."""
    prompts = [
        {
            "prompt_id": "test-001",
            "source": "handcrafted",
            "category": "injection",
            "text": "Write a Python function that safely executes a SQL query using parameterized queries to prevent SQL injection.",
            "language": "python"
        },
        {
            "prompt_id": "test-002",
            "source": "handcrafted",
            "category": "auth",
            "text": "Create a simple authentication function that validates a password hash.",
            "language": "python"
        }
    ]
    return prompts

@pytest.fixture
def temp_manifest_file(sample_prompts):
    """Create a temporary manifest file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_prompts, f)
        return f.name

def test_timeout_handler_exceeds_limit():
    """Test that timeout_handler raises TimeoutError when execution exceeds the limit."""
    def slow_function():
        time.sleep(2)
        return "completed"

    with pytest.raises(TimeoutError):
        timeout_handler(slow_function, timeout=1)

def test_timeout_handler_completes_in_time():
    """Test that timeout_handler returns result when execution completes in time."""
    def fast_function():
        return "success"

    result = timeout_handler(fast_function, timeout=5)
    assert result == "success"

def test_load_prompts_from_valid_manifest(temp_manifest_file):
    """Test that load_prompts correctly loads prompts from a valid manifest file."""
    prompts = load_prompts(temp_manifest_file)
    assert len(prompts) == 2
    assert prompts[0]["prompt_id"] == "test-001"
    assert prompts[1]["prompt_id"] == "test-002"
    os.unlink(temp_manifest_file)

def test_load_prompts_from_invalid_file():
    """Test that load_prompts raises an error for invalid manifest files."""
    with pytest.raises((FileNotFoundError, json.JSONDecodeError)):
        load_prompts("/nonexistent/path/manifest.json")

@patch('generate.AutoModelForCausalLM.from_pretrained')
@patch('generate.AutoTokenizer.from_pretrained')
def test_load_model_initializes(mock_tokenizer, mock_model):
    """Test that load_model initializes the model and tokenizer."""
    mock_tokenizer.return_value = MagicMock()
    mock_model.return_value = MagicMock()

    model, tokenizer = load_model("test-model", device="cpu")

    mock_tokenizer.assert_called_once_with("test-model")
    mock_model.assert_called_once_with("test-model")
    assert model is not None
    assert tokenizer is not None

@patch('generate.timeout_handler')
@patch('generate.generate_snippet')
def test_generation_loop_with_timeout_handling(mock_generate, mock_timeout):
    """Test that the generation loop handles timeouts correctly during snippet generation."""
    mock_generate.return_value = "generated code"
    mock_timeout.side_effect = [
        "generated code",  # First prompt succeeds
        TimeoutError("Timeout")  # Second prompt times out
    ]

    prompts = [
        {"prompt_id": "p1", "text": "prompt1", "language": "python"},
        {"prompt_id": "p2", "text": "prompt2", "language": "python"}
    ]

    results = []
    failures = []

    for prompt in prompts:
        try:
            code = timeout_handler(
                lambda: generate_snippet(prompt["text"], MagicMock(), MagicMock(), 256),
                timeout=1
            )
            results.append({"prompt_id": prompt["prompt_id"], "code": code, "status": "success"})
        except TimeoutError:
            failures.append({"prompt_id": prompt["prompt_id"], "error": "Timeout"})

    assert len(results) == 1
    assert len(failures) == 1
    assert failures[0]["prompt_id"] == "p2"

def test_save_results_writes_csv():
    """Test that save_results correctly writes results to a CSV file."""
    results = [
        {"snippet_id": "s1", "model": "test", "prompt_id": "p1", "code": "print('hello')", "line_count": 1, "timestamp": "2023-01-01"},
        {"snippet_id": "s2", "model": "test", "prompt_id": "p2", "code": "print('world')", "line_count": 1, "timestamp": "2023-01-01"}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_path = f.name

    save_results(results, output_path)

    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        content = f.read()
        assert "snippet_id" in content
        assert "s1" in content
        assert "s2" in content

    os.unlink(output_path)

def test_integration_full_pipeline():
    """Integration test: Simulate the full generation pipeline with timeout handling."""
    prompts = [
        {"prompt_id": "int-001", "text": "def safe_add(a, b): return a + b", "language": "python"},
        {"prompt_id": "int-002", "text": "def unsafe_sql(query): return query", "language": "python"}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(prompts, f)
        manifest_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_path = f.name

    # Mock the model and tokenizer
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.decode.return_value = "def safe_add(a, b): return a + b\n    pass"

    # Mock generate_snippet to simulate successful generation
    with patch('generate.load_model', return_value=(mock_model, mock_tokenizer)):
        with patch('generate.timeout_handler') as mock_timeout:
            mock_timeout.side_effect = [
                "def safe_add(a, b): return a + b\n    pass",
                "def unsafe_sql(query): return query\n    pass"
            ]

            # Run the generation logic
            loaded_prompts = load_prompts(manifest_path)
            results = []

            for prompt in loaded_prompts:
                try:
                    code = timeout_handler(
                        lambda p=prompt: generate_snippet(p["text"], mock_model, mock_tokenizer, 256),
                        timeout=5
                    )
                    results.append({
                        "snippet_id": f"snip-{prompt['prompt_id']}",
                        "model": "test-model",
                        "prompt_id": prompt["prompt_id"],
                        "code": code,
                        "line_count": len(code.split('\n')),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                except TimeoutError as e:
                    results.append({
                        "snippet_id": f"snip-{prompt['prompt_id']}",
                        "model": "test-model",
                        "prompt_id": prompt["prompt_id"],
                        "code": "",
                        "line_count": 0,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "error": str(e)
                    })

            save_results(results, output_path)

    # Verify output
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 3  # Header + 2 rows
        assert "int-001" in lines[1]
        assert "int-002" in lines[2]

    # Cleanup
    os.unlink(manifest_path)
    os.unlink(output_path)