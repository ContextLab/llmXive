"""
Unit tests for GSM8K data splitting logic.
"""
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.data.split_gsm8k import (
    estimate_difficulty,
    stratified_split,
    save_splits,
    compute_sha256,
    SPLIT_DIR,
)


def test_estimate_difficulty_simple():
    """Test difficulty estimation on simple examples."""
    # Easy example with few operations
    easy_example = {
        "answer": "John has 5 apples. He buys 3 more. #### 8"
    }
    assert estimate_difficulty(easy_example) == 0

    # Medium example
    medium_example = {
        "answer": "Alice has 10 apples. She gives 2 to Bob. Then she buys 5 more. Then she splits them equally with Charlie. #### 6.5"
    }
    score = estimate_difficulty(medium_example)
    assert 1 <= score <= 3

    # Hard example with many operations
    hard_example = {
        "answer": "A complex problem with many steps = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 = 55. Then 55 * 2 = 110. Then 110 / 5 = 22. #### 22"
    }
    score = estimate_difficulty(hard_example)
    assert score >= 2


def test_stratified_split_balances_difficulty():
    """Test that stratified split maintains difficulty distribution."""
    # Create synthetic examples with known difficulties
    examples = []
    for i in range(100):
        examples.append({
            "answer": f"Problem {i}. Solution with = and + operations. #### {i}"
        })

    # Add some easy examples
    for i in range(20):
        examples.append({
            "answer": f"Easy {i}. Just 1 operation. #### {i}"
        })

    train, eval, gen = stratified_split(examples, seed=42)

    # Check that we have roughly the right proportions
    total = len(examples)
    assert abs(len(train) / total - 0.8) < 0.1
    assert abs(len(eval) / total - 0.1) < 0.05
    assert abs(len(gen) / total - 0.1) < 0.05

    # Check that all sets are non-empty
    assert len(train) > 0
    assert len(eval) > 0
    assert len(gen) > 0


def test_stratified_split_reproducibility():
    """Test that splitting is reproducible with the same seed."""
    examples = [{"answer": f"Problem {i}. #### {i}"} for i in range(50)]

    train1, eval1, gen1 = stratified_split(examples, seed=123)
    train2, eval2, gen2 = stratified_split(examples, seed=123)

    assert train1 == train2
    assert eval1 == eval2
    assert gen1 == gen2


def test_stratified_split_different_seeds():
    """Test that different seeds produce different splits."""
    examples = [{"answer": f"Problem {i}. #### {i}"} for i in range(50)]

    train1, eval1, gen1 = stratified_split(examples, seed=123)
    train2, eval2, gen2 = stratified_split(examples, seed=456)

    # They should be different (high probability)
    assert train1 != train2 or eval1 != eval2


def test_save_splits_creates_files(tmp_path):
    """Test that save_splits creates the expected files."""
    train = [{"answer": "Train 1. #### 1"}]
    eval_set = [{"answer": "Eval 1. #### 1"}]
    gen = [{"answer": "Gen 1. #### 1"}]

    file_paths = save_splits(train, eval_set, gen, tmp_path, seed=42)

    assert "train" in file_paths
    assert "eval" in file_paths
    assert "generalization" in file_paths

    # Check files exist
    for path in file_paths.values():
        assert os.path.exists(path)

    # Check checksums file exists
    checksum_file = tmp_path / "splits_checksums_seed42.json"
    assert checksum_file.exists()

    # Check checksums content
    with open(checksum_file) as f:
        checksums = json.load(f)
    assert "train" in checksums
    assert "eval" in checksums
    assert "generalization" in checksums


def test_compute_sha256():
    """Test SHA-256 computation."""
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        hash1 = compute_sha256(Path(temp_path))
        hash2 = compute_sha256(Path(temp_path))

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    finally:
        os.unlink(temp_path)