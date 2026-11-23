"""
Unit tests for the Seed Manager module.
Verifies deterministic seed generation and the constraint that Baseline
and Experimental seeds are identical for the same scene.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest

from generation.seed_manager import SeedManager, get_generation_seed, get_baseline_experimental_seeds, run_seed_generation


class TestSeedManager:
    """Tests for SeedManager class."""

    def test_derive_seed_deterministic(self):
        """Test that derive_seed produces the same result for same inputs."""
        manager = SeedManager(base_seed=42)
        
        seed1 = manager._derive_seed("scene_001", "baseline")
        seed2 = manager._derive_seed("scene_001", "baseline")
        
        assert seed1 == seed2
        assert isinstance(seed1, int)
        assert 0 <= seed1 < 2**32

    def test_baseline_experimental_identical(self):
        """Test that Baseline and Experimental seeds are identical for a scene."""
        manager = SeedManager(base_seed=42)
        seeds = manager.generate_seeds_for_scene("scene_001")
        
        assert seeds["baseline"] == seeds["experimental"]
        assert seeds["baseline"] != seeds["control"] # Control should be different

    def test_control_seeds_distinct(self):
        """Test that Control seeds are distinct from Baseline/Experimental."""
        manager = SeedManager(base_seed=42)
        seeds = manager.generate_seeds_for_scene("scene_001")
        
        assert seeds["control"] != seeds["baseline"]
        assert seeds["control"] != seeds["experimental"]

    def test_different_scenes_different_seeds(self):
        """Test that different scenes produce different seeds."""
        manager = SeedManager(base_seed=42)
        seeds1 = manager.generate_seeds_for_scene("scene_001")
        seeds2 = manager.generate_seeds_for_scene("scene_002")
        
        # Baseline seeds should differ
        assert seeds1["baseline"] != seeds2["baseline"]
        # Control seeds should differ
        assert seeds1["control"] != seeds2["control"]

    def test_save_manifest(self):
        """Test that manifest is saved correctly to JSON."""
        manager = SeedManager(base_seed=42)
        manager.generate_all_seeds(["scene_001", "scene_002"])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest.json"
            manager.save_manifest(output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["base_seed"] == 42
            assert "seeds" in data
            assert "scene_001" in data["seeds"]
            assert "scene_002" in data["seeds"]
            
            # Verify structure
            scene_001 = data["seeds"]["scene_001"]
            assert scene_001["baseline"] == scene_001["experimental"]
            assert scene_001["baseline"] != scene_001["control"]

    def test_get_baseline_experimental_seeds(self):
        """Test the utility function for getting seeds."""
        b_seed, e_seed = get_baseline_experimental_seeds("test_scene", base_seed=123)
        
        assert b_seed == e_seed
        assert isinstance(b_seed, int)

    def test_run_seed_generation(self):
        """Test the full generation pipeline from CSV."""
        # Create a temporary CSV
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "scenes.csv"
            manifest_path = Path(tmpdir) / "manifest.json"
            
            # Write test CSV
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["scene_id", "description"])
                writer.writeheader()
                writer.writerow({"scene_id": "scene_A", "description": "A on B"})
                writer.writerow({"scene_id": "scene_B", "description": "A next to B"})
            
            run_seed_generation(
                input_csv_path=str(csv_path),
                output_manifest_path=str(manifest_path),
                base_seed=999
            )
            
            assert manifest_path.exists()
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            
            assert data["base_seed"] == 999
            assert len(data["seeds"]) == 2
            assert "scene_A" in data["seeds"]
            assert "scene_B" in data["seeds"]

# Import csv here to avoid global import in module scope if not needed elsewhere
import csv
