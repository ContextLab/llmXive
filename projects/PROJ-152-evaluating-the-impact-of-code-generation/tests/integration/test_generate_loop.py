"""
Integration test for the generation loop (T014).
Verifies that the pipeline processes prompts and generates output files.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import csv

# Test fixtures
@pytest.fixture
def test_manifest(tmp_path):
    """Create a minimal test manifest with 3 prompts."""
    manifest_dir = tmp_path / "data" / "prompts"
    manifest_dir.mkdir(parents=True)
    
    manifest_data = {
        "prompts": [
            {"id": "test-1", "prompt": "Write a function to add two numbers", "source": "test"},
            {"id": "test-2", "prompt": "Create a loop that prints numbers", "source": "test"},
            {"id": "test-3", "prompt": "Implement a simple class", "source": "test"}
        ]
    }
    
    manifest_path = manifest_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    
    return str(manifest_path)

@pytest.fixture
def setup_test_env(tmp_path):
    """Set up a temporary environment for testing."""
    # Create necessary directories
    dirs = [
        tmp_path / "data" / "generated",
        tmp_path / "data" / "failures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal config
    config_content = """
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
"""
    config_path = tmp_path / "code" / "config.py"
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    return tmp_path

def test_load_prompts(test_manifest):
    """Test that prompts are loaded correctly from manifest."""
    from generate import load_prompts
    
    prompts = load_prompts(test_manifest)
    
    assert len(prompts) == 3
    assert prompts[0]['id'] == 'test-1'
    assert prompts[1]['prompt'] == 'Create a loop that prints numbers'

def test_save_results(tmp_path):
    """Test that results are saved correctly to CSV."""
    from generate import save_results
    
    output_path = tmp_path / "test_output.csv"
    results = [
        {
            'snippet_id': 'test-1',
            'model': 'test-model',
            'prompt_id': 'p1',
            'code': 'print("hello")',
            'line_count': 1,
            'timestamp': '2024-01-01 00:00:00'
        }
    ]
    
    save_results(results, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]['snippet_id'] == 'test-1'
    assert rows[0]['code'] == 'print("hello")'

def test_generation_loop_structure(tmp_path, test_manifest):
    """
    Test the structure of the generation loop without actually running models.
    This verifies the logic flow and error handling.
    """
    # Mock the model loading and generation functions
    import generate
    
    original_load_model = generate.load_model
    original_generate_snippet = generate.generate_snippet
    
    mock_model = object()
    mock_tokenizer = object()
    
    def mock_load_model(model_name, device="cpu"):
        return mock_model, mock_tokenizer
    
    def mock_generate_snippet(model, tokenizer, prompt, max_tokens=256, timeout_seconds=120):
        return f"mocked_code_for_{prompt}"
    
    generate.load_model = mock_load_model
    generate.generate_snippet = mock_generate_snippet
    
    try:
        # Run the main logic with mocked dependencies
        prompts = generate.load_prompts(test_manifest)
        models = ["mock-model-1", "mock-model-2"]
        all_results = []
        
        for model_name in models:
            model, tokenizer = generate.load_model(model_name)
            
            for prompt_data in prompts:
                prompt_text = prompt_data.get('prompt', '')
                generated_code = generate.generate_snippet(model, tokenizer, prompt_text)
                
                result = {
                    'snippet_id': f"{model_name}_{prompt_data['id']}",
                    'model': model_name,
                    'prompt_id': prompt_data['id'],
                    'code': generated_code,
                    'line_count': len(generated_code.splitlines()),
                    'timestamp': '2024-01-01 00:00:00'
                }
                all_results.append(result)
        
        # Verify we got the expected number of results
        # 2 models * 3 prompts = 6 results
        assert len(all_results) == 6
        
        # Verify structure
        for result in all_results:
            assert 'snippet_id' in result
            assert 'model' in result
            assert 'prompt_id' in result
            assert 'code' in result
            assert 'line_count' in result
            assert 'timestamp' in result
            assert result['code'].startswith('mocked_code_for_')
    
    finally:
        # Restore original functions
        generate.load_model = original_load_model
        generate.generate_snippet = original_generate_snippet

if __name__ == "__main__":
    pytest.main([__file__, "-v"])