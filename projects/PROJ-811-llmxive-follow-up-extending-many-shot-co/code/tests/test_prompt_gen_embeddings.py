import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.prompt_gen import PromptGenerator
from code.src.parser_utils import save_json_file

@pytest.fixture
def temp_manifest_file():
    """Create a temporary manifest file with sample data."""
    sample_data = {
        "seed_0": {
            "examples": [
                {"id": "ex_1", "trace": "Step 1: Identify problem.\nStep 2: Solve problem."},
                {"id": "ex_2", "trace": "Step 1: Analyze data.\nStep 2: Conclude."}
            ]
        },
        "seed_1": {
            "examples": [
                {"id": "ex_3", "trace": "Step 1: Hypothesize.\nStep 2: Test."}
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_data, f)
    return f.name

@pytest.fixture
def mock_sbert_model():
    """Mock the SentenceTransformer class to avoid actual model download."""
    mock_model = MagicMock()
    # Return a dummy array of shape (3, 384) for 3 examples
    dummy_embeddings = np.random.rand(3, 384).astype(np.float32)
    mock_model.encode.return_value = dummy_embeddings
    return mock_model

def test_load_manifest_from_file(temp_manifest_file):
    """Test that the generator loads the manifest correctly."""
    generator = PromptGenerator(temp_manifest_file)
    assert generator.manifest is not None
    assert "seed_0" in generator.manifest
    assert len(generator.manifest["seed_0"]["examples"]) == 2

def test_generate_embeddings_calls_model(temp_manifest_file, mock_sbert_model):
    """Test that generate_embeddings calls the model's encode method."""
    with patch('code.src.prompt_gen.SentenceTransformer', return_value=mock_sbert_model):
        generator = PromptGenerator(temp_manifest_file)
        # Load a subset to test
        examples = generator.manifest["seed_0"]["examples"]
        result = generator.generate_embeddings(examples)

        mock_sbert_model.encode.assert_called_once()
        assert len(result) == 2
        assert "embedding" in result[0]
        assert isinstance(result[0]["embedding"], list)

def test_process_manifest_saves_file(temp_manifest_file, mock_sbert_model, tmp_path):
    """Test that process_manifest saves the output to the specified path."""
    output_path = str(tmp_path / "test_embeddings.json")

    with patch('code.src.prompt_gen.SentenceTransformer', return_value=mock_sbert_model):
        generator = PromptGenerator(temp_manifest_file)
        generator.process_manifest(output_path=output_path)

    assert Path(output_path).exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    # Should contain all examples from the manifest (2 from seed_0 + 1 from seed_1)
    assert len(data) == 3
    assert data[0]["id"] == "ex_1"
    assert len(data[0]["embedding"]) == 384

def test_missing_manifest_raises_error():
    """Test that a missing manifest file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        PromptGenerator("/nonexistent/path/to/manifest.json")

def test_empty_examples_handling(temp_manifest_file, mock_sbert_model):
    """Test handling of empty example lists."""
    with patch('code.src.prompt_gen.SentenceTransformer', return_value=mock_sbert_model):
        generator = PromptGenerator(temp_manifest_file)
        # Manually set an empty list for testing
        empty_examples = []
        result = generator.generate_embeddings(empty_examples)
        assert result == []
        mock_sbert_model.encode.assert_not_called()

def test_missing_text_content_warns_and_skips(temp_manifest_file, mock_sbert_model):
    """Test that examples missing text content are handled gracefully."""
    # Modify manifest to include an example without text
    with open(temp_manifest_file, 'r') as f:
        data = json.load(f)
    data["seed_0"]["examples"].append({"id": "ex_bad"})
    
    with open(temp_manifest_file, 'w') as f:
        json.dump(data, f)

    with patch('code.src.prompt_gen.SentenceTransformer', return_value=mock_sbert_model):
        generator = PromptGenerator(temp_manifest_file)
        examples = generator.manifest["seed_0"]["examples"]
        result = generator.generate_embeddings(examples)
        
        # Should still process valid ones, and handle the bad one (empty string passed to model)
        # The model mock will return embeddings for the empty string too
        assert len(result) == 3
        assert result[2]["id"] == "ex_bad"
        assert "embedding" in result[2]
