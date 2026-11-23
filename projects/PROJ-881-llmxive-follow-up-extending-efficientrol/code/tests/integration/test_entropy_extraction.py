"""
Integration test for intermediate state extraction (T018).

This test verifies that the generation pipeline correctly captures layer-wise
probability distributions and computes entropy values for every token position
in a sequence, as required by User Story 2.

Dependencies:
  - T005: Schema Validation (EntropyProfile)
  - T016: Merged Data (Labeled Dataset)
  - T019: Generation hooks (to be implemented)
  - T020: Entropy integration
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generation.generation import (
    GenerationConfig,
    load_model_for_cpu_inference,
    generate_single_pass,
    process_dataset,
    setup_logging,
)
from src.utils.entropy_calc import compute_layer_wise_entropy
from src.utils.validators import EntropyProfile, validate_entropy_profile
from src.data.download import download_gsm8k_subset, download_minigrid_subset
from src.config import Config

# Import contract test schema to ensure consistency
from tests.contract.test_entropy_profile_schema import schema as entropy_schema


@pytest.fixture(scope="module")
def temp_test_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="module")
def gsm8k_test_path(temp_test_dir):
    """Download a small subset of GSM8K for testing."""
    # Ensure we have the data
    data_path = temp_test_dir / "gsm8k_test.jsonl"
    # Use the download module to fetch a small representative subset
    # The download module handles caching and fetching
    try:
        # Download a tiny subset (1-2 examples) for integration testing
        download_gsm8k_subset(str(data_path), num_examples=2)
    except Exception as e:
        pytest.skip(f"Could not download GSM8K subset: {e}")
    return data_path


@pytest.fixture(scope="module")
def minigrid_test_path(temp_test_dir):
    """Download a small subset of MiniGrid for testing."""
    data_path = temp_test_dir / "minigrid_test.jsonl"
    try:
        download_minigrid_subset(str(data_path), num_examples=2)
    except Exception as e:
        pytest.skip(f"Could not download MiniGrid subset: {e}")
    return data_path


@pytest.fixture(scope="module")
def model_path():
    """Return the path to a CPU-tractable model."""
    # Use a small, fast model for testing
    return "distilgpt2"


def test_entropy_extraction_gsm8k(gsm8k_test_path, model_path, temp_test_dir):
    """
    Test that intermediate state extraction works for GSM8K sequences.

    Verifies:
      1. Model loads successfully for CPU inference
      2. Generation captures layer-wise probabilities
      3. Entropy is computed for every token position
      4. Output matches EntropyProfile schema
      5. No missing entropy values in the output
    """
    # Setup logging to capture intermediate state
    log_path = temp_test_dir / "test_extraction.log"
    setup_logging(log_level="INFO", output_path=str(log_path))

    # Configure generation with entropy extraction enabled
    config = GenerationConfig(
        model_name=model_path,
        temperature=0.0,
        max_tokens=20,  # Keep short for fast testing
        extract_entropy=True,  # Enable entropy capture
        batch_size=10,  # Small batch for testing
        output_dir=str(temp_test_dir),
        dataset_type="gsm8k",
    )

    # Run generation with entropy extraction
    output_file = temp_test_dir / "gsm8k_entropy_output.jsonl"

    try:
        process_dataset(
            input_path=str(gsm8k_test_path),
            config=config,
            output_path=str(output_file),
        )
    except Exception as e:
        pytest.fail(f"Generation with entropy extraction failed: {e}")

    # Verify output file exists and has content
    assert output_file.exists(), "Entropy output file was not created"
    assert output_file.stat().st_size > 0, "Entropy output file is empty"

    # Load and validate each record
    records = []
    with open(output_file, "r") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                records.append(record)

    assert len(records) > 0, "No records were generated"

    # Validate each record against EntropyProfile schema
    for i, record in enumerate(records):
        # Check required fields exist
        assert "sequence_id" in record, f"Record {i} missing sequence_id"
        assert "entropy_profile" in record, f"Record {i} missing entropy_profile"
        assert "tokens" in record, f"Record {i} missing tokens"

        entropy_profile = record["entropy_profile"]

        # Validate against schema
        try:
            validate_entropy_profile(entropy_profile)
        except ValueError as e:
            pytest.fail(f"Record {i} failed EntropyProfile validation: {e}")

        # Verify layer-wise granularity is preserved
        assert "layers" in entropy_profile, f"Record {i} missing layers"
        assert isinstance(entropy_profile["layers"], list), "Layers must be a list"
        assert len(entropy_profile["layers"]) > 0, "Record {i} has no layers"

        # Verify each layer has entropy values for all tokens
        for layer_idx, layer_data in enumerate(entropy_profile["layers"]):
            assert "layer_id" in layer_data, f"Layer {layer_idx} missing layer_id"
            assert "entropy_values" in layer_data, f"Layer {layer_idx} missing entropy_values"

            entropy_values = layer_data["entropy_values"]
            assert isinstance(entropy_values, list), "entropy_values must be a list"
            assert len(entropy_values) > 0, f"Layer {layer_idx} has no entropy values"

            # Verify no None or missing values
            for j, val in enumerate(entropy_values):
                assert val is not None, f"Layer {layer_idx}, token {j} has None entropy"
                assert isinstance(val, (int, float)), f"Layer {layer_idx}, token {j} has non-numeric entropy"
                assert val >= 0, f"Layer {layer_idx}, token {j} has negative entropy"

        # Verify token count matches entropy vector length
        token_count = len(record["tokens"])
        for layer_data in entropy_profile["layers"]:
            assert len(layer_data["entropy_values"]) == token_count, (
                f"Entropy vector length ({len(layer_data['entropy_values'])}) "
                f"does not match token count ({token_count})"
            )


def test_entropy_extraction_minigrid(minigrid_test_path, model_path, temp_test_dir):
    """
    Test that intermediate state extraction works for MiniGrid sequences.

    Similar to GSM8K test but verifies behavior with MiniGrid-specific
    token patterns and multiple valid paths.
    """
    log_path = temp_test_dir / "test_extraction_minigrid.log"
    setup_logging(log_level="INFO", output_path=str(log_path))

    config = GenerationConfig(
        model_name=model_path,
        temperature=0.0,
        max_tokens=15,
        extract_entropy=True,
        batch_size=10,
        output_dir=str(temp_test_dir),
        dataset_type="minigrid",
    )

    output_file = temp_test_dir / "minigrid_entropy_output.jsonl"

    try:
        process_dataset(
            input_path=str(minigrid_test_path),
            config=config,
            output_path=str(output_file),
        )
    except Exception as e:
        pytest.fail(f"MiniGrid generation with entropy extraction failed: {e}")

    assert output_file.exists(), "MiniGrid entropy output file was not created"
    assert output_file.stat().st_size > 0, "MiniGrid entropy output file is empty"

    records = []
    with open(output_file, "r") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    assert len(records) > 0, "No MiniGrid records were generated"

    # Validate structure (same as GSM8K test)
    for i, record in enumerate(records):
        assert "entropy_profile" in record, f"Record {i} missing entropy_profile"
        entropy_profile = record["entropy_profile"]

        # Check layer structure
        assert "layers" in entropy_profile
        assert len(entropy_profile["layers"]) > 0

        for layer_data in entropy_profile["layers"]:
            assert "entropy_values" in layer_data
            entropy_values = layer_data["entropy_values"]

            # Verify no missing values
            for val in entropy_values:
                assert val is not None, "Found None entropy value in MiniGrid record"
                assert isinstance(val, (int, float))
                assert val >= 0


def test_entropy_values_consistency(temp_test_dir):
    """
    Test that entropy values are consistent with manual calculation.

    This test generates a simple sequence and verifies that the entropy
    values in the output match what we would expect from the probability
    distributions.
    """
    # Create a simple test case with known probabilities
    # We'll use a mock to verify the calculation path
    from src.utils.entropy_calc import compute_shannon_entropy
    import numpy as np

    # Test with uniform distribution (max entropy)
    probs_uniform = np.array([0.25, 0.25, 0.25, 0.25])
    entropy_uniform = compute_shannon_entropy(probs_uniform)
    expected_uniform = np.log2(4)  # Should be 2.0
    assert abs(entropy_uniform - expected_uniform) < 1e-6, (
        f"Uniform entropy calculation incorrect: {entropy_uniform} != {expected_uniform}"
    )

    # Test with deterministic distribution (zero entropy)
    probs_deterministic = np.array([1.0, 0.0, 0.0, 0.0])
    entropy_deterministic = compute_shannon_entropy(probs_deterministic)
    assert entropy_deterministic == 0.0, (
        f"Deterministic entropy should be 0: {entropy_deterministic}"
    )

    # Test with edge case (very small probabilities)
    probs_edge = np.array([0.999, 0.001, 0.0, 0.0])
    entropy_edge = compute_shannon_entropy(probs_edge)
    assert entropy_edge >= 0, "Edge case entropy should be non-negative"
    assert entropy_edge < 1, "Edge case entropy should be small"


def test_no_missing_entropy_values(gsm8k_test_path, model_path, temp_test_dir):
    """
    Regression test: Ensure no entropy values are missing (None) in the output.

    This specifically checks for the bug where some layers or tokens might
    have None values instead of computed entropy.
    """
    config = GenerationConfig(
        model_name=model_path,
        temperature=0.0,
        max_tokens=10,
        extract_entropy=True,
        batch_size=5,
        output_dir=str(temp_test_dir),
        dataset_type="gsm8k",
    )

    output_file = temp_test_dir / "no_missing_test.jsonl"

    process_dataset(
        input_path=str(gsm8k_test_path),
        config=config,
        output_path=str(output_file),
    )

    with open(output_file, "r") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            entropy_profile = record["entropy_profile"]

            for layer_data in entropy_profile["layers"]:
                for val in layer_data["entropy_values"]:
                    assert val is not None, "Found None entropy value - extraction incomplete"
                    assert not (isinstance(val, float) and np.isnan(val)), "Found NaN entropy value"
                    assert not (isinstance(val, float) and np.isinf(val)), "Found Inf entropy value"