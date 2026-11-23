"""
Tests for the Seed Manager (T038).
"""
import pytest
import json
import os
import sys
from pathlib import Path

# Add code directory to path if running from tests
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from utils.seed_manager import get_seed_ranges, save_seed_manifest, get_seed_range_for_purpose, MASTER_SEED

class TestSeedManager:
    def test_seed_ranges_disjoint(self):
        """Test that generated seed ranges are mutually disjoint."""
        ranges = get_seed_ranges()
        train_set = set(ranges["train"])
        eval_set = set(ranges["eval"])
        baseline_set = set(ranges["baseline"])

        assert len(train_set & eval_set) == 0, "Train and Eval must be disjoint"
        assert len(train_set & baseline_set) == 0, "Train and Baseline must be disjoint"
        assert len(eval_set & baseline_set) == 0, "Eval and Baseline must be disjoint"

    def test_seed_range_counts(self):
        """Test that the counts match the specification (Train: 50, Eval: 50, Baseline: 100)."""
        ranges = get_seed_ranges()
        assert len(ranges["train"]) == 50, f"Train seeds should be 50, got {len(ranges['train'])}"
        assert len(ranges["eval"]) == 50, f"Eval seeds should be 50, got {len(ranges['eval'])}"
        assert len(ranges["baseline"]) == 100, f"Baseline seeds should be 100, got {len(ranges['baseline'])}"

    def test_seed_range_values(self):
        """Test that the seed values fall within the expected ranges."""
        ranges = get_seed_ranges()
        
        # Train: 0-49
        assert min(ranges["train"]) == 0
        assert max(ranges["train"]) == 49

        # Eval: 50-99
        assert min(ranges["eval"]) == 50
        assert max(ranges["eval"]) == 99

        # Baseline: 1000-1099
        assert min(ranges["baseline"]) == 1000
        assert max(ranges["baseline"]) == 1099

    def test_master_seed_determinism(self):
        """Test that the same master seed produces the same ranges."""
        ranges1 = get_seed_ranges()
        ranges2 = get_seed_ranges()
        
        assert ranges1["train"] == ranges2["train"]
        assert ranges1["eval"] == ranges2["eval"]
        assert ranges1["baseline"] == ranges2["baseline"]

    def test_save_seed_manifest(self, tmp_path):
        """Test that save_seed_manifest creates a valid JSON file."""
        output_file = tmp_path / "seed_manifest.json"
        manifest = save_seed_manifest(str(output_file))

        assert output_file.exists(), "Manifest file was not created"
        
        with open(output_file, 'r') as f:
            loaded_manifest = json.load(f)

        assert loaded_manifest["master_seed"] == MASTER_SEED
        assert "ranges" in loaded_manifest
        assert "train" in loaded_manifest["ranges"]
        assert "eval" in loaded_manifest["ranges"]
        assert "baseline" in loaded_manifest["ranges"]
        
        # Check counts in manifest
        assert loaded_manifest["ranges"]["train"]["count"] == 50
        assert loaded_manifest["ranges"]["eval"]["count"] == 50
        assert loaded_manifest["ranges"]["baseline"]["count"] == 100

    def test_get_seed_range_for_purpose(self):
        """Test the helper function for retrieving specific ranges."""
        train_seeds = get_seed_range_for_purpose("train")
        assert len(train_seeds) == 50
        assert 0 in train_seeds
        assert 49 in train_seeds

        eval_seeds = get_seed_range_for_purpose("eval")
        assert len(eval_seeds) == 50
        assert 50 in eval_seeds
        assert 99 in eval_seeds

        baseline_seeds = get_seed_range_for_purpose("baseline")
        assert len(baseline_seeds) == 100
        assert 1000 in baseline_seeds
        assert 1099 in baseline_seeds

        with pytest.raises(ValueError):
            get_seed_range_for_purpose("invalid_purpose")
