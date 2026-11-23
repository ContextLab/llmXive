import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import pytest
import sys

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.scripts.run_batch_strategies import load_manifest, generate_prompts_for_seed, run_batch, STRATEGIES
from code.src.prompt_gen import PromptGenerator

@pytest.fixture
def temp_manifest_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "entries": [
                {"id": "1", "trace": "Step 1. Step 2.", "answer": "A", "logical_difficulty": 2, "curvature_score": 0.5},
                {"id": "2", "trace": "Step 1. Step 2. Step 3.", "answer": "B", "logical_difficulty": 3, "curvature_score": 0.8},
                {"id": "3", "trace": "Step 1.", "answer": "C", "logical_difficulty": 1, "curvature_score": 0.2}
            ],
            "metadata": {"version": "1.0"}
        }
        json.dump(data, f)
        f.flush()
        yield Path(f.name)
        os.unlink(f.name)

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_config():
    return Mock()

def test_load_manifest_success(temp_manifest_file):
    data = load_manifest(temp_manifest_file)
    assert "entries" in data
    assert len(data["entries"]) == 3

def test_load_manifest_not_found():
    with pytest.raises(FileNotFoundError):
        load_manifest(Path("nonexistent.json"))

def test_load_manifest_invalid_format(temp_manifest_file):
    # Write invalid JSON
    with open(temp_manifest_file, 'w') as f:
        f.write("not json")
    with pytest.raises((json.JSONDecodeError, ValueError)):
        load_manifest(temp_manifest_file)

@patch('code.scripts.run_batch_strategies.PromptGenerator')
def test_generate_prompts_for_seed(mock_gen_class, temp_manifest_file, temp_output_dir, mock_config):
    mock_gen_instance = Mock(spec=PromptGenerator)
    mock_gen_instance.generate_ordered_examples.return_value = [
        {"id": "3", "trace": "Step 1.", "answer": "C"},
        {"id": "1", "trace": "Step 1. Step 2.", "answer": "A"}
    ]
    mock_gen_class.return_value = mock_gen_instance

    manifest_data = load_manifest(temp_manifest_file)
    files = generate_prompts_for_seed(
        generator=mock_gen_instance,
        manifest_data=manifest_data,
        seed=42,
        strategy="logical_ascending",
        output_dir=temp_output_dir,
        max_examples=2
    )

    assert len(files) == 1
    assert "seed_42_logical_ascending.json" in files[0]

    # Verify content
    with open(files[0], 'r') as f:
        content = json.load(f)
    assert content["seed"] == 42
    assert content["strategy"] == "logical_ascending"
    assert len(content["examples"]) == 2

@patch('code.scripts.run_batch_strategies.load_manifest')
@patch('code.scripts.run_batch_strategies.PromptGenerator')
def test_run_batch_success(mock_gen_class, mock_load_manifest, temp_manifest_file, temp_output_dir, mock_config):
    mock_manifest_data = {
        "entries": [
            {"id": "1", "trace": "T1", "answer": "A", "logical_difficulty": 1},
            {"id": "2", "trace": "T2", "answer": "B", "logical_difficulty": 2}
        ]
    }
    mock_load_manifest.return_value = mock_manifest_data

    mock_gen_instance = Mock(spec=PromptGenerator)
    mock_gen_instance.generate_ordered_examples.return_value = mock_manifest_data["entries"]
    mock_gen_class.return_value = mock_gen_instance

    seeds = [42, 123]
    results = run_batch(
        manifest_path=temp_manifest_file,
        seeds=seeds,
        output_base_dir=temp_output_dir,
        strategies=["logical_ascending"]
    )

    assert len(results["files"]) == 2  # 2 seeds * 1 strategy
    assert len(results["errors"]) == 0
    assert temp_output_dir.exists()

@patch('code.scripts.run_batch_strategies.load_manifest')
@patch('code.scripts.run_batch_strategies.PromptGenerator')
def test_run_batch_missing_manifest(mock_gen_class, mock_load_manifest, temp_output_dir, mock_config):
    mock_load_manifest.side_effect = FileNotFoundError("Missing")
    seeds = [42]
    results = run_batch(
        manifest_path=Path("missing.json"),
        seeds=seeds,
        output_base_dir=temp_output_dir,
        strategies=["logical_ascending"]
    )
    # The run_batch function catches exceptions and logs them, but doesn't crash
    # However, our implementation in run_batch catches exceptions inside the loop.
    # Let's check the error list.
    assert len(results["errors"]) > 0

@patch('code.scripts.run_batch_strategies.load_manifest')
@patch('code.scripts.run_batch_strategies.PromptGenerator')
def test_run_batch_invalid_strategy(mock_gen_class, mock_load_manifest, temp_manifest_file, temp_output_dir, mock_config):
    mock_manifest_data = {"entries": []}
    mock_load_manifest.return_value = mock_manifest_data
    mock_gen_instance = Mock(spec=PromptGenerator)
    mock_gen_instance.generate_ordered_examples.side_effect = ValueError("Unknown strategy")
    mock_gen_class.return_value = mock_gen_instance

    results = run_batch(
        manifest_path=temp_manifest_file,
        seeds=[42],
        output_base_dir=temp_output_dir,
        strategies=["invalid_strategy"]
    )

    assert len(results["errors"]) == 1
    assert "invalid_strategy" in results["errors"][0]
