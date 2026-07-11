"""
Tests for the batch strategy runner script (T026).

These tests verify that:
1. The batch runner correctly iterates over seeds and strategies
2. Prompts are generated and saved to the correct paths
3. The output manifest is correctly formatted
"""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import pytest
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.scripts.run_batch_strategies import (
    load_manifest,
    generate_prompts_for_seed,
    run_batch,
    STRATEGIES
)
from code.src.prompt_gen import PromptGenerator

@pytest.fixture
def temp_manifest_file():
    """Create a temporary manifest file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        sample_data = [
            {
                "id": "trace_001",
                "cot_trace": "Step 1: Identify problem. Step 2: Analyze data. Step 3: Propose solution.",
                "dag_depth": 3,
                "is_valid": True,
                "curvature_score": 0.15
            },
            {
                "id": "trace_002",
                "cot_trace": "Step 1: Read input. Step 2: Process. Step 3: Output result.",
                "dag_depth": 2,
                "is_valid": True,
                "curvature_score": 0.22
            },
            {
                "id": "trace_003",
                "cot_trace": "Step 1: Start. Step 2: Loop. Step 3: End.",
                "dag_depth": 3,
                "is_valid": False,  # Invalid trace
                "curvature_score": 0.10
            }
        ]
        json.dump(sample_data, f)
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: {
        "experiment": {
            "seeds": [42, 123],
            "strategies": ["logical_ascending", "logical_random"]
        },
        "prompt": {
            "max_examples": 5,
            "template": "standard"
        }
    }.get(key, default)
    return config

def test_load_manifest_success(temp_manifest_file):
    """Test successful loading of manifest."""
    entries = load_manifest(temp_manifest_file)
    assert len(entries) == 3
    assert entries[0]["id"] == "trace_001"
    assert entries[0]["is_valid"] is True

def test_load_manifest_not_found():
    """Test loading non-existent manifest raises error."""
    with pytest.raises(FileNotFoundError):
        load_manifest(Path("/nonexistent/path/manifest.json"))

def test_load_manifest_invalid_format(temp_output_dir):
    """Test loading manifest with invalid format raises error."""
    invalid_file = temp_output_dir / "invalid.json"
    with open(invalid_file, 'w') as f:
        json.dump({"not": "a list"}, f)
    
    with pytest.raises(ValueError):
        load_manifest(invalid_file)

@patch('code.scripts.run_batch_strategies.PromptGenerator')
def test_generate_prompts_for_seed(mock_generator_class, temp_manifest_file, temp_output_dir, mock_config):
    """Test prompt generation for a single seed and strategy."""
    # Setup mock generator
    mock_generator = MagicMock(spec=PromptGenerator)
    mock_generator.generate_ordering.return_value = [
        {"id": "trace_001", "cot_trace": "..."}
    ]
    mock_generator.assemble_prompts.return_value = {
        "seed": 42,
        "strategy": "logical_ascending",
        "prompts": ["prompt1"]
    }
    mock_generator_class.return_value = mock_generator

    examples = load_manifest(temp_manifest_file)
    output_file = generate_prompts_for_seed(
        generator=mock_generator,
        examples=examples,
        seed=42,
        strategy="logical_ascending",
        output_dir=temp_output_dir
    )

    assert output_file is not None
    assert output_file.exists()
    assert "prompts_seed_42_logical_ascending.json" in str(output_file)
    
    # Verify file content
    with open(output_file) as f:
        data = json.load(f)
    assert len(data["prompts"]) == 1

def test_run_batch_success(temp_manifest_file, temp_output_dir, mock_config):
    """Test successful batch run across multiple seeds and strategies."""
    with patch('code.scripts.run_batch_strategies.PromptGenerator') as mock_generator_class:
        mock_generator = MagicMock(spec=PromptGenerator)
        mock_generator.generate_ordering.return_value = [
            {"id": "trace_001", "cot_trace": "..."}
        ]
        mock_generator.assemble_prompts.return_value = {
            "seed": 42,
            "strategy": "logical_ascending",
            "prompts": ["prompt1"]
        }
        mock_generator_class.return_value = mock_generator

        results = run_batch(
            config=mock_config,
            manifest_path=temp_manifest_file,
            output_dir=temp_output_dir,
            seeds=[42, 123],
            strategies=["logical_ascending", "logical_random"]
        )

        assert results["status"] == "completed"
        assert len(results["outputs"]) == 4  # 2 seeds * 2 strategies
        assert results["total_prompts_generated"] == 4

def test_run_batch_missing_manifest(temp_output_dir, mock_config):
    """Test batch run with missing manifest fails gracefully."""
    results = run_batch(
        config=mock_config,
        manifest_path=Path("/nonexistent/manifest.json"),
        output_dir=temp_output_dir,
        seeds=[42],
        strategies=["logical_ascending"]
    )
    
    assert results["status"] == "failed"
    assert "error" in results

def test_run_batch_invalid_strategy(temp_manifest_file, temp_output_dir, mock_config):
    """Test batch run skips unknown strategies."""
    with patch('code.scripts.run_batch_strategies.PromptGenerator') as mock_generator_class:
        mock_generator = MagicMock(spec=PromptGenerator)
        mock_generator.generate_ordering.return_value = []
        mock_generator.assemble_prompts.return_value = {"prompts": []}
        mock_generator_class.return_value = mock_generator

        results = run_batch(
            config=mock_config,
            manifest_path=temp_manifest_file,
            output_dir=temp_output_dir,
            seeds=[42],
            strategies=["invalid_strategy", "logical_ascending"]
        )

        # Should skip invalid strategy, process valid one
        assert results["status"] == "completed"
        assert len(results["outputs"]) == 1
        assert results["outputs"][0]["strategy"] == "logical_ascending"

def test_strategies_constant():
    """Test that STRATEGIES constant contains expected values."""
    assert "logical_ascending" in STRATEGIES
    assert "logical_random" in STRATEGIES
    assert "original_cds" in STRATEGIES
    assert len(STRATEGIES) == 3
