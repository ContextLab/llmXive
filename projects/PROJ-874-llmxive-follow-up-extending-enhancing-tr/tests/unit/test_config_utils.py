"""
Unit tests for configuration and utility functions.

Tests for:
- Seed management
- Path resolution
- Memory limit checks
- Dataset path validation
"""
import pytest
import os
import sys
import random
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config import (
    get_seed,
    set_seed,
    get_dataset_paths,
    get_required_files,
    get_processed_dir,
    get_results_dir,
    get_memory_limit,
    get_max_workers,
    get_flow_model,
    get_flow_precision
)


class TestSeedManagement:
    """Tests for random seed handling."""

    def test_set_seed_determinism(self):
        """Test that setting seed produces deterministic results."""
        set_seed(42)
        val1 = random.random()
        
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2, "Same seed should produce same random values"

    def test_get_seed_default(self):
        """Test default seed value."""
        # Reset to default state
        if hasattr(get_seed, '_seed'):
            delattr(get_seed, '_seed')
        
        seed = get_seed()
        assert isinstance(seed, int), "Seed should be an integer"

    def test_set_seed_updates_global(self):
        """Test that set_seed updates the internal state."""
        set_seed(12345)
        seed = get_seed()
        assert seed == 12345, f"Expected 12345, got {seed}"


class TestPathResolution:
    """Tests for path resolution functions."""

    def test_get_processed_dir(self):
        """Test processed directory path."""
        path = get_processed_dir()
        assert isinstance(path, Path), "Should return Path object"
        assert "processed" in str(path), "Path should contain 'processed'"

    def test_get_results_dir(self):
        """Test results directory path."""
        path = get_results_dir()
        assert isinstance(path, Path), "Should return Path object"
        assert "results" in str(path), "Path should contain 'results'"

    def test_get_dataset_paths_structure(self):
        """Test dataset paths structure."""
        paths = get_dataset_paths()
        assert "narrlv" in paths, "Should have NarrLV path"
        assert "vbench" in paths, "Should have VBench path"
        assert isinstance(paths["narrlv"], Path), "Paths should be Path objects"


class TestResourceLimits:
    """Tests for resource limit configuration."""

    def test_get_memory_limit(self):
        """Test memory limit retrieval."""
        limit = get_memory_limit()
        assert isinstance(limit, (int, float)), "Memory limit should be numeric"
        assert limit > 0, "Memory limit should be positive"
        # Check against CI constraint (should be reasonable for CPU CI)
        assert limit <= 8000, "Memory limit should be <= 8GB for CI compatibility"

    def test_get_max_workers(self):
        """Test max workers configuration."""
        workers = get_max_workers()
        assert isinstance(workers, int), "Max workers should be integer"
        assert workers >= 1, "Should have at least 1 worker"
        assert workers <= 8, "Should not exceed reasonable CPU limits"

    def test_get_flow_model(self):
        """Test flow model configuration."""
        model = get_flow_model()
        assert model in ["raft-small", "raft-large"], f"Unexpected model: {model}"

    def test_get_flow_precision(self):
        """Test flow precision configuration."""
        precision = get_flow_precision()
        assert precision in ["fp16", "fp32"], f"Unexpected precision: {precision}"


class TestRequiredFiles:
    """Tests for required file validation."""

    def test_get_required_files_list(self):
        """Test that required files list is populated."""
        files = get_required_files()
        assert isinstance(files, list), "Should return a list"
        assert len(files) > 0, "Should have at least one required file"

    def test_required_files_content(self):
        """Test content of required files list."""
        files = get_required_files()
        # Check for expected dataset files
        file_names = [os.path.basename(f) if isinstance(f, str) else f.name for f in files]
        # At least some dataset-related files should be present
        assert any("narrlv" in f.lower() or "vbench" in f.lower() for f in file_names), \
            "Should include dataset files"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
