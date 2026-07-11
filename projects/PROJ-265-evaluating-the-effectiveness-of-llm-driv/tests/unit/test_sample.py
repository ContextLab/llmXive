"""
Unit tests for the sampling module (T014b).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path for imports
import sys
sys_path = Path(__file__).parent.parent.parent
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

from code.data.sample import (
    count_lines,
    assign_stratum,
    load_validated_functions,
    stratified_sample,
    STRATA_DEFINITIONS
)

def test_count_lines():
    """Test LOC counting logic."""
    code = """
    def foo():
        x = 1
        # comment
        y = 2
        return x + y
    """
    # 4 non-empty, non-comment lines
    assert count_lines(code) == 4

def test_assign_stratum():
    """Test stratum assignment based on LOC."""
    assert assign_stratum(5) == "small"
    assert assign_stratum(10) == "small"
    assert assign_stratum(11) == "medium"
    assert assign_stratum(50) == "medium"
    assert assign_stratum(51) == "large"
    assert assign_stratum(100) == "large"

def test_load_validated_functions_filters_imports():
    """Test that functions with > 3 external imports are excluded."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        # Valid function (2 imports)
        f.write(json.dumps({"id": "1", "code": "def a(): pass", "external_imports": 2, "loc": 1}) + "\n")
        # Invalid function (4 imports)
        f.write(json.dumps({"id": "2", "code": "def b(): pass", "external_imports": 4, "loc": 1}) + "\n")
        # Valid function (3 imports - boundary)
        f.write(json.dumps({"id": "3", "code": "def c(): pass", "external_imports": 3, "loc": 1}) + "\n")
        temp_path = f.name

    try:
        funcs = load_validated_functions(Path(temp_path))
        assert len(funcs) == 2
        ids = {f["id"] for f in funcs}
        assert "1" in ids
        assert "3" in ids
        assert "2" not in ids
    finally:
        os.unlink(temp_path)

def test_stratified_sample_distribution():
    """Test that sampling respects strata weights roughly."""
    # Create a mock pool
    pool = []
    # Add 100 small (weight 0.5 -> expect ~50)
    for i in range(100):
        pool.append({"id": f"small_{i}", "stratum": "small", "loc": 5, "code": "x=1"})
    # Add 60 medium (weight 0.3 -> expect ~30)
    for i in range(60):
        pool.append({"id": f"med_{i}", "stratum": "medium", "loc": 20, "code": "x=1"})
    # Add 40 large (weight 0.2 -> expect ~20)
    for i in range(40):
        pool.append({"id": f"large_{i}", "stratum": "large", "loc": 60, "code": "x=1"})

    sample = stratified_sample(pool, target_size=100)

    # Verify counts
    small_count = sum(1 for s in sample if s["stratum"] == "small")
    med_count = sum(1 for s in sample if s["stratum"] == "medium")
    large_count = sum(1 for s in sample if s["stratum"] == "large")

    # Allow some variance due to integer rounding and random sampling logic
    # Expected: 50, 30, 20
    assert 40 <= small_count <= 60
    assert 20 <= med_count <= 40
    assert 10 <= large_count <= 30
    assert len(sample) == 100

def test_stratified_sample_insufficient_data():
    """Test behavior when a stratum has fewer items than target weight."""
    pool = [
        {"id": "1", "stratum": "small", "loc": 5, "code": "x=1"},
        {"id": "2", "stratum": "medium", "loc": 20, "code": "x=1"},
    ]
    # Target 100, but only 2 available
    sample = stratified_sample(pool, target_size=100)
    assert len(sample) == 2