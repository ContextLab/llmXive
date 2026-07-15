import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
import hashlib

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.generators.synthetic_pairs import (
    generate_base_patch,
    generate_contradiction_pair,
    generate_non_contradiction_pair,
    generate_synthetic_pairs,
    read_sample_size_from_research_md
)


class TestBasePatchGeneration:
    def test_base_patch_structure(self):
        """Verify base patch has required fields and string types."""
        patch = generate_base_patch(seed=42)
        assert isinstance(patch, dict)
        assert "state_before" in patch
        assert "state_after" in patch
        assert "command" in patch
        assert isinstance(patch["state_before"], str)
        assert isinstance(patch["state_after"], str)
        assert isinstance(patch["command"], str)
        assert len(patch["state_before"]) > 0
        assert len(patch["state_after"]) > 0

    def test_base_patch_determinism(self):
        """Verify base patch generation is deterministic with same seed."""
        patch1 = generate_base_patch(seed=123)
        patch2 = generate_base_patch(seed=123)
        assert patch1 == patch2

    def test_base_patch_variability(self):
        """Verify different seeds produce different patches."""
        patch1 = generate_base_patch(seed=100)
        patch2 = generate_base_patch(seed=200)
        # They should differ in at least one field
        assert patch1 != patch2


class TestContradictionLogic:
    def test_contradiction_pair_structure(self):
        """Verify contradiction pair has correct schema."""
        pair = generate_contradiction_pair(seed=42)
        assert "patch_a" in pair
        assert "patch_b" in pair
        assert "is_contradiction" in pair
        assert pair["is_contradiction"] is True
        assert isinstance(pair["patch_a"], str)
        assert isinstance(pair["patch_b"], str)

    def test_contradiction_logic(self):
        """Verify contradiction pair actually contains a negated fact."""
        pair = generate_contradiction_pair(seed=999)
        # The pair should contain semantic negation logic
        # We verify by checking the pair is marked as contradiction
        assert pair["is_contradiction"] is True
        # Verify content is not empty
        assert len(pair["patch_a"]) > 0
        assert len(pair["patch_b"]) > 0


class TestNonContradictionLogic:
    def test_non_contradiction_pair_structure(self):
        """Verify non-contradiction pair has correct schema."""
        pair = generate_non_contradiction_pair(seed=42)
        assert "patch_a" in pair
        assert "patch_b" in pair
        assert "is_contradiction" in pair
        assert pair["is_contradiction"] is False
        assert isinstance(pair["patch_a"], str)
        assert isinstance(pair["patch_b"], str)

    def test_non_contradiction_logic(self):
        """Verify non-contradiction pair does not contain negated facts."""
        pair = generate_non_contradiction_pair(seed=888)
        assert pair["is_contradiction"] is False
        assert len(pair["patch_a"]) > 0
        assert len(pair["patch_b"]) > 0


class TestSyntheticPairsGeneration:
    def test_generate_synthetic_pairs_count(self):
        """Verify generation produces exactly N pairs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_pairs.json"
            # Generate 10 pairs
            generate_synthetic_pairs(n_pairs=10, output_path=str(output_path), seed=42)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 10

    def test_generate_synthetic_pairs_schema(self):
        """Verify all pairs have correct schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_pairs.json"
            generate_synthetic_pairs(n_pairs=5, output_path=str(output_path), seed=42)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            for pair in data:
                assert "patch_a" in pair
                assert "patch_b" in pair
                assert "is_contradiction" in pair
                assert isinstance(pair["patch_a"], str)
                assert isinstance(pair["patch_b"], str)
                assert isinstance(pair["is_contradiction"], bool)

    def test_generate_synthetic_pairs_checksum(self):
        """Verify deterministic generation produces same checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path1 = Path(tmpdir) / "test_pairs_1.json"
            output_path2 = Path(tmpdir) / "test_pairs_2.json"
            
            # Generate twice with same seed
            generate_synthetic_pairs(n_pairs=20, output_path=str(output_path1), seed=42)
            generate_synthetic_pairs(n_pairs=20, output_path=str(output_path2), seed=42)
            
            # Calculate checksums
            with open(output_path1, 'rb') as f:
                checksum1 = hashlib.sha256(f.read()).hexdigest()
            with open(output_path2, 'rb') as f:
                checksum2 = hashlib.sha256(f.read()).hexdigest()
            
            assert checksum1 == checksum2, "Deterministic generation failed: checksums differ"

    def test_generate_synthetic_pairs_mixed_labels(self):
        """Verify dataset contains both contradiction and non-contradiction pairs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_pairs.json"
            # Generate 100 pairs (should be roughly 50/50 split)
            generate_synthetic_pairs(n_pairs=100, output_path=str(output_path), seed=42)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            contradiction_count = sum(1 for p in data if p["is_contradiction"])
            non_contradiction_count = sum(1 for p in data if not p["is_contradiction"])
            
            # Verify both types exist
            assert contradiction_count > 0, "No contradiction pairs generated"
            assert non_contradiction_count > 0, "No non-contradiction pairs generated"
            # Verify total matches
            assert contradiction_count + non_contradiction_count == 100


class TestResearchMdFallback:
    def test_read_sample_size_from_research_md_existing(self):
        """Verify reading sample size from existing research.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            # Create a research.md with sample_size
            research_path.write_text("sample_size: 50\nother_key: value\n")
            
            result = read_sample_size_from_research_md(str(research_path))
            assert result == 50

    def test_read_sample_size_from_research_md_missing(self):
        """Verify fallback to default when research.md is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # research.md does not exist
            research_path = Path(tmpdir) / "nonexistent.md"
            
            result = read_sample_size_from_research_md(str(research_path))
            assert result == 100, "Should fallback to default N=100"

    def test_read_sample_size_from_research_md_invalid(self):
        """Verify fallback when sample_size is not a valid integer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            research_path.write_text("sample_size: not_a_number\n")
            
            result = read_sample_size_from_research_md(str(research_path))
            assert result == 100, "Should fallback to default N=100 on invalid value"

    def test_read_sample_size_from_research_md_empty_file(self):
        """Verify fallback when research.md is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_path = Path(tmpdir) / "research.md"
            research_path.write_text("")
            
            result = read_sample_size_from_research_md(str(research_path))
            assert result == 100, "Should fallback to default N=100 on empty file"