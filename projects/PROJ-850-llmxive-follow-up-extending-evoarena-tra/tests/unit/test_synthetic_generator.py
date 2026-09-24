import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
import hashlib
import random

# Ensure project root is in path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.data.generators.synthetic_pairs import (
    read_sample_size_from_research_md,
    generate_base_patch,
    generate_contradiction_pair,
    generate_non_contradiction_pair,
    generate_synthetic_pairs,
    main
)
from src.utils.seeding import set_deterministic_seed


class TestBasePatchGeneration:
    """Test the generation of base state patches."""

    def test_base_patch_structure(self):
        """Verify that generated base patches have the required schema."""
        patch = generate_base_patch()
        assert isinstance(patch, dict)
        assert "state_description" in patch
        assert "command_sequence" in patch
        assert isinstance(patch["state_description"], str)
        assert isinstance(patch["command_sequence"], list)
        assert len(patch["command_sequence"]) > 0

    def test_base_patch_determinism(self):
        """Verify that base patch generation is deterministic with a fixed seed."""
        set_deterministic_seed(42)
        patch1 = generate_base_patch()
        set_deterministic_seed(42)
        patch2 = generate_base_patch()
        assert patch1 == patch2

    def test_base_patch_content_variability(self):
        """Verify that different seeds produce different base patches."""
        set_deterministic_seed(42)
        patch1 = generate_base_patch()
        set_deterministic_seed(123)
        patch2 = generate_base_patch()
        # They should be different due to different seeds
        assert patch1 != patch2


class TestContradictionLogic:
    """Test the logic for generating contradiction pairs."""

    def test_contradiction_pair_structure(self):
        """Verify that contradiction pairs have the correct schema."""
        base = generate_base_patch()
        pair = generate_contradiction_pair(base)
        assert isinstance(pair, dict)
        assert "patch_a" in pair
        assert "patch_b" in pair
        assert "is_contradiction" in pair
        assert pair["is_contradiction"] is True
        assert isinstance(pair["patch_a"], str)
        assert isinstance(pair["patch_b"], str)

    def test_contradiction_fact_negation(self):
        """Verify that contradiction pairs actually negate a key fact."""
        base = generate_base_patch()
        pair = generate_contradiction_pair(base)
        # The descriptions should be different
        assert pair["patch_a"] != pair["patch_b"]
        # The base description should be present in patch_a
        assert base["state_description"] in pair["patch_a"]

    def test_contradiction_determinism(self):
        """Verify that contradiction generation is deterministic with a fixed seed."""
        base = generate_base_patch()
        set_deterministic_seed(42)
        pair1 = generate_contradiction_pair(base)
        set_deterministic_seed(42)
        pair2 = generate_contradiction_pair(base)
        assert pair1 == pair2


class TestNonContradictionLogic:
    """Test the logic for generating non-contradiction pairs."""

    def test_non_contradiction_pair_structure(self):
        """Verify that non-contradiction pairs have the correct schema."""
        base = generate_base_patch()
        pair = generate_non_contradiction_pair(base)
        assert isinstance(pair, dict)
        assert "patch_a" in pair
        assert "patch_b" in pair
        assert "is_contradiction" in pair
        assert pair["is_contradiction"] is False
        assert isinstance(pair["patch_a"], str)
        assert isinstance(pair["patch_b"], str)

    def test_non_contradiction_unrelated_update(self):
        """Verify that non-contradiction pairs update unrelated facts."""
        base = generate_base_patch()
        pair = generate_non_contradiction_pair(base)
        # The descriptions should be different (update happened)
        assert pair["patch_a"] != pair["patch_b"]
        # But they should not be a contradiction
        assert pair["is_contradiction"] is False

    def test_non_contradiction_determinism(self):
        """Verify that non-contradiction generation is deterministic with a fixed seed."""
        base = generate_base_patch()
        set_deterministic_seed(42)
        pair1 = generate_non_contradiction_pair(base)
        set_deterministic_seed(42)
        pair2 = generate_non_contradiction_pair(base)
        assert pair1 == pair2


class TestSyntheticPairsGeneration:
    """Test the full synthetic pairs generation pipeline."""

    def test_generate_synthetic_pairs_structure(self):
        """Verify that the generated dataset has the correct structure."""
        set_deterministic_seed(42)
        pairs = generate_synthetic_pairs(10)
        assert isinstance(pairs, list)
        assert len(pairs) == 10
        for pair in pairs:
            assert isinstance(pair, dict)
            assert "patch_a" in pair
            assert "patch_b" in pair
            assert "is_contradiction" in pair
            assert isinstance(pair["patch_a"], str)
            assert isinstance(pair["patch_b"], str)
            assert isinstance(pair["is_contradiction"], bool)

    def test_generate_synthetic_pairs_balance(self):
        """Verify that the dataset has a balanced mix of contradiction and non-contradiction pairs."""
        set_deterministic_seed(42)
        pairs = generate_synthetic_pairs(100)
        contradiction_count = sum(1 for p in pairs if p["is_contradiction"])
        non_contradiction_count = sum(1 for p in pairs if not p["is_contradiction"])
        # Should be roughly 50/50
        assert 40 <= contradiction_count <= 60
        assert 40 <= non_contradiction_count <= 60

    def test_generate_synthetic_pairs_determinism(self):
        """Verify that full generation is deterministic with a fixed seed."""
        set_deterministic_seed(42)
        pairs1 = generate_synthetic_pairs(20)
        set_deterministic_seed(42)
        pairs2 = generate_synthetic_pairs(20)
        assert pairs1 == pairs2

    def test_generate_synthetic_pairs_checksum_integrity(self):
        """Verify that the generated dataset has consistent checksums across runs."""
        set_deterministic_seed(42)
        pairs1 = generate_synthetic_pairs(50)
        set_deterministic_seed(42)
        pairs2 = generate_synthetic_pairs(50)
        
        # Calculate checksums
        json_str1 = json.dumps(pairs1, sort_keys=True)
        json_str2 = json.dumps(pairs2, sort_keys=True)
        checksum1 = hashlib.sha256(json_str1.encode()).hexdigest()
        checksum2 = hashlib.sha256(json_str2.encode()).hexdigest()
        
        assert checksum1 == checksum2


class TestResearchMdFallback:
    """Test the fallback behavior when research.md is missing."""

    def test_read_sample_size_from_research_md_missing(self):
        """Verify default sample size when research.md is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Ensure research.md doesn't exist
            research_md_path = Path(tmpdir) / "specs" / "001-evoconflict-filtering" / "research.md"
            # Don't create the file
            result = read_sample_size_from_research_md(str(research_md_path))
            assert result == 100  # Default fallback

    def test_read_sample_size_from_research_md_present(self):
        """Verify sample size is read correctly from research.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_md_path = Path(tmpdir) / "specs" / "001-evoconflict-filtering" / "research.md"
            research_md_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create research.md with sample_size
            research_md_path.write_text("sample_size: 250\n")
            
            result = read_sample_size_from_research_md(str(research_md_path))
            assert result == 250

    def test_main_with_missing_research_md(self):
        """Verify main function handles missing research.md gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create necessary directories
            data_dir = Path(tmpdir) / "data" / "raw"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Ensure research.md doesn't exist
            specs_dir = Path(tmpdir) / "specs" / "001-evoconflict-filtering"
            specs_dir.mkdir(parents=True, exist_ok=True)
            
            # Run main with custom output path
            output_path = data_dir / "test_synthetic_pairs.json"
            main(output_path=str(output_path), research_md_path=str(specs_dir / "research.md"))
            
            # Verify output file was created with default size (100)
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert len(data) == 100

    def test_main_creates_output_file(self):
        """Verify main function creates the output file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create necessary directories
            data_dir = Path(tmpdir) / "data" / "raw"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create research.md with custom sample size
            specs_dir = Path(tmpdir) / "specs" / "001-evoconflict-filtering"
            specs_dir.mkdir(parents=True, exist_ok=True)
            research_md_path = specs_dir / "research.md"
            research_md_path.write_text("sample_size: 50\n")
            
            # Run main
            output_path = data_dir / "test_synthetic_pairs.json"
            main(output_path=str(output_path), research_md_path=str(research_md_path))
            
            # Verify output file was created with correct size
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert len(data) == 50
            
            # Verify file format
            for pair in data:
                assert "patch_a" in pair
                assert "patch_b" in pair
                assert "is_contradiction" in pair

    def test_main_output_format(self):
        """Verify the output file format matches the schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data" / "raw"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            specs_dir = Path(tmpdir) / "specs" / "001-evoconflict-filtering"
            specs_dir.mkdir(parents=True, exist_ok=True)
            research_md_path = specs_dir / "research.md"
            research_md_path.write_text("sample_size: 20\n")
            
            output_path = data_dir / "test_synthetic_pairs.json"
            main(output_path=str(output_path), research_md_path=str(research_md_path))
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # Verify schema
            for pair in data:
                assert isinstance(pair["patch_a"], str)
                assert isinstance(pair["patch_b"], str)
                assert isinstance(pair["is_contradiction"], bool)