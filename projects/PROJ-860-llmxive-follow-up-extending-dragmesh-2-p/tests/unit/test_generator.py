"""
Unit tests for the NovelObjectSet generator class.
"""

import os
import tempfile
import pytest
import numpy as np
import xml.etree.ElementTree as ET

from generator import NovelObjectSet
from seed_config import set_seeds


class TestNovelObjectSet:
    """Tests for the NovelObjectSet generator class."""

    def test_initialization_valid_params(self):
        """Test that valid parameters initialize correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = NovelObjectSet(
                count=10,
                seed=42,
                friction_min=0.1,
                friction_max=1.2,
                output_dir=tmpdir
            )
            assert generator.count == 10
            assert generator.seed == 42
            assert generator.friction_min == 0.1
            assert generator.friction_max == 1.2
            assert generator.output_dir == tmpdir

    def test_initialization_invalid_count(self):
        """Test that invalid count raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                NovelObjectSet(
                    count=0,
                    seed=42,
                    friction_min=0.1,
                    friction_max=1.2,
                    output_dir=tmpdir
                )

            with pytest.raises(ValueError):
                NovelObjectSet(
                    count=-5,
                    seed=42,
                    friction_min=0.1,
                    friction_max=1.2,
                    output_dir=tmpdir
                )

    def test_initialization_invalid_friction_range(self):
        """Test that invalid friction range raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Min > max
            with pytest.raises(ValueError):
                NovelObjectSet(
                    count=10,
                    seed=42,
                    friction_min=1.5,
                    friction_max=0.5,
                    output_dir=tmpdir
                )

            # Out of bounds
            with pytest.raises(ValueError):
                NovelObjectSet(
                    count=10,
                    seed=42,
                    friction_min=-0.1,
                    friction_max=1.0,
                    output_dir=tmpdir
                )

            with pytest.raises(ValueError):
                NovelObjectSet(
                    count=10,
                    seed=42,
                    friction_min=0.5,
                    friction_max=3.0,
                    output_dir=tmpdir
                )

    def test_generate_creates_files(self):
        """Test that generate() creates the expected number of files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = NovelObjectSet(
                count=5,
                seed=42,
                friction_min=0.1,
                friction_max=1.2,
                output_dir=tmpdir
            )
            files = generator.generate()

            assert len(files) == 5
            for f in files:
                assert os.path.exists(f)
                assert f.endswith(".urdf")

    def test_generate_reproducibility(self):
        """Test that same seed produces same files."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                gen1 = NovelObjectSet(
                    count=3,
                    seed=123,
                    friction_min=0.2,
                    friction_max=0.8,
                    output_dir=tmpdir1
                )
                files1 = gen1.generate()

                gen2 = NovelObjectSet(
                    count=3,
                    seed=123,
                    friction_min=0.2,
                    friction_max=0.8,
                    output_dir=tmpdir2
                )
                files2 = gen2.generate()

                # Compare file contents
                for f1, f2 in zip(files1, files2):
                    with open(f1, 'r') as a, open(f2, 'r') as b:
                        assert a.read() == b.read()

    def test_urdf_validity(self):
        """Test that generated URDF files are valid XML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = NovelObjectSet(
                count=2,
                seed=42,
                friction_min=0.1,
                friction_max=1.2,
                output_dir=tmpdir
            )
            files = generator.generate()

            for f in files:
                # Should not raise
                tree = ET.parse(f)
                root = tree.getroot()
                assert root.tag == "robot"
                # Check for required elements
                links = root.findall(".//link")
                joints = root.findall(".//joint")
                assert len(links) >= 2  # Base + moving link
                assert len(joints) >= 1  # At least one joint

    def test_friction_values_in_range(self):
        """Test that generated friction values are within specified range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            friction_min = 0.3
            friction_max = 0.9
            generator = NovelObjectSet(
                count=20,
                seed=42,
                friction_min=friction_min,
                friction_max=friction_max,
                output_dir=tmpdir
            )
            files = generator.generate()

            for f in files:
                tree = ET.parse(f)
                root = tree.getroot()

                # Extract friction from dynamics element
                dynamics = root.find(".//dynamics")
                assert dynamics is not None
                friction = float(dynamics.get("friction"))

                assert friction_min <= friction <= friction_max

    def test_output_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "subdir", "generated")
            assert not os.path.exists(new_dir)

            generator = NovelObjectSet(
                count=1,
                seed=42,
                friction_min=0.1,
                friction_max=1.0,
                output_dir=new_dir
            )
            files = generator.generate()

            assert os.path.exists(new_dir)
            assert len(files) == 1