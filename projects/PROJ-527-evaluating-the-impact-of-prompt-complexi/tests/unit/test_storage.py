"""
Unit tests for the storage module.

Tests verify that generated code and metadata are correctly serialized
and persisted to Parquet format.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from pydantic import ValidationError

# Import from project API surface
from models.data_models import GeneratedCode, ComplexityLabel
from data.storage import (
    serialize_generated_code,
    write_variants_to_parquet,
    append_to_variants_parquet,
    load_variants_from_parquet
)
from config import get_config

@pytest.fixture
def sample_generated_code():
    """Create a sample GeneratedCode object for testing."""
    return GeneratedCode(
        problem_id="human_eval_001",
        prompt_id="prompt_simple_001",
        complexity_label=ComplexityLabel.SIMPLE,
        generated_code="def add(a, b):\n    return a + b",
        generation_timestamp=datetime(2024, 1, 15, 10, 30, 0),
        llm_model="test-model-v1",
        prompt_token_count=45,
        structural_element_count=2,
        prompt_text_hash="abc123def456",
        generation_duration_ms=1250
    )


@pytest.fixture
def sample_generated_codes(sample_generated_code):
    """Create a list of sample GeneratedCode objects."""
    codes = [sample_generated_code]
    # Add a second variant with different complexity
    codes.append(GeneratedCode(
        problem_id="human_eval_001",
        prompt_id="prompt_complex_001",
        complexity_label=ComplexityLabel.COMPLEX,
        generated_code="def add(a: int, b: int) -> int:\n    \"\"\"Add two integers.\"\"\"\n    return a + b",
        generation_timestamp=datetime(2024, 1, 15, 10, 31, 0),
        llm_model="test-model-v1",
        prompt_token_count=85,
        structural_element_count=5,
        prompt_text_hash="xyz789ghi012",
        generation_duration_ms=1890
    ))
    return codes


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True)
    return output_dir


def test_serialize_generated_code(sample_generated_code):
    """Test that GeneratedCode is correctly serialized to dictionary."""
    result = serialize_generated_code(sample_generated_code)

    assert result["problem_id"] == "human_eval_001"
    assert result["prompt_id"] == "prompt_simple_001"
    assert result["complexity_label"] == "simple"
    assert "def add" in result["generated_code"]
    assert result["llm_model"] == "test-model-v1"
    assert result["prompt_token_count"] == 45
    assert result["structural_element_count"] == 2
    assert result["status"] == "success"
    assert "2024-01-15" in result["generation_timestamp"]


def test_write_variants_to_parquet_creates_file(sample_generated_codes, temp_output_dir):
    """Test that write_variants_to_parquet creates the output file."""
    output_path = temp_output_dir / "test_output.parquet"
    result_path = write_variants_to_parquet(sample_generated_codes, output_path)

    assert result_path.exists()
    assert result_path == output_path

    # Verify file is readable Parquet
    df = pd.read_parquet(result_path)
    assert len(df) == 2
    assert "problem_id" in df.columns
    assert "complexity_label" in df.columns


def test_write_variants_to_parquet_with_numeric_columns(sample_generated_codes, temp_output_dir):
    """Test that numeric columns are properly typed in the output."""
    output_path = temp_output_dir / "test_numeric.parquet"
    write_variants_to_parquet(sample_generated_codes, output_path)

    df = pd.read_parquet(output_path)

    # Check numeric columns are integers
    assert df["prompt_token_count"].dtype in ['int64', 'int32']
    assert df["structural_element_count"].dtype in ['int64', 'int32']
    assert df["generation_duration_ms"].dtype in ['int64', 'int32']


def test_write_variants_to_parquet_empty_list_raises():
    """Test that writing an empty list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot write empty list"):
        write_variants_to_parquet([])


def test_append_to_variants_parquet_creates_new(temp_output_dir, sample_generated_codes):
    """Test that append creates a new file if none exists."""
    output_path = temp_output_dir / "append_test.parquet"

    # First append (creates file)
    result_path = append_to_variants_parquet(sample_generated_codes, output_path)

    assert result_path.exists()
    df = pd.read_parquet(result_path)
    assert len(df) == 2


def test_append_to_variants_parquet_adds_to_existing(temp_output_dir, sample_generated_codes):
    """Test that append adds to existing file."""
    output_path = temp_output_dir / "append_existing.parquet"

    # Create initial file
    write_variants_to_parquet(sample_generated_codes, output_path)

    # Add more codes
    new_codes = [sample_generated_codes[0]]  # Just one more
    result_path = append_to_variants_parquet(new_codes, output_path)

    df = pd.read_parquet(result_path)
    assert len(df) == 3


def test_load_variants_from_parquet(temp_output_dir, sample_generated_codes):
    """Test that loaded data matches written data."""
    output_path = temp_output_dir / "load_test.parquet"

    # Write data
    write_variants_to_parquet(sample_generated_codes, output_path)

    # Load data
    loaded_codes = load_variants_from_parquet(output_path)

    assert len(loaded_codes) == 2
    assert loaded_codes[0].problem_id == "human_eval_001"
    assert loaded_codes[0].complexity_label == ComplexityLabel.SIMPLE
    assert loaded_codes[1].complexity_label == ComplexityLabel.COMPLEX


def test_load_variants_from_parquet_missing_file():
    """Test that loading from missing file returns empty list."""
    result = load_variants_from_parquet(Path("/nonexistent/path/file.parquet"))
    assert result == []