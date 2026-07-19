"""
Unit tests for the NovelObjectSet generator.
"""
import os
import pytest
import tempfile
import xml.etree.ElementTree as ET
from generator import NovelObjectSet

class TestNovelObjectSet:
    """Tests for the NovelObjectSet class."""

    def test_initialization(self):
        """Test that the generator initializes with a seed."""
        gen = NovelObjectSet(seed=123)
        assert gen.seed == 123

        gen_no_seed = NovelObjectSet()
        assert gen_no_seed.seed is None

    def test_generate_object_structure(self):
        """Test that a generated URDF has the correct XML structure."""
        gen = NovelObjectSet(seed=42)
        urdf_str = gen.generate_object(object_id=1, friction_coef=0.5)

        # Parse the XML
        root = ET.fromstring(urdf_str)
        assert root.tag == "robot"
        assert root.get("name") == "novel_object_1"

        # Check for required links
        links = [link.get("name") for link in root.findall("link")]
        assert "base_link" in links
        assert "mobile_link" in links

        # Check for joint
        joints = root.findall("joint")
        assert len(joints) == 1
        assert joints[0].get("name") == "drag_joint"
        assert joints[0].get("type") == "prismatic"

    def test_friction_assignment(self):
        """Test that friction coefficient is correctly embedded in the URDF."""
        test_mu = 1.25
        gen = NovelObjectSet(seed=99)
        urdf_str = gen.generate_object(object_id=1, friction_coef=test_mu)

        root = ET.fromstring(urdf_str)
        # Find the contact element in mobile_link
        mobile_link = root.find("link[@name='mobile_link']")
        contact = mobile_link.find("contact")

        lateral_friction = float(contact.find("lateral_friction").get("value"))
        assert abs(lateral_friction - test_mu) < 1e-6

    def test_generate_set_creates_files(self):
        """Test that generate_set creates the correct number of files."""
        count = 5
        friction_min = 0.1
        friction_max = 1.0
        seed = 42

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = NovelObjectSet(seed=seed)
            files = gen.generate_set(
                count=count,
                friction_min=friction_min,
                friction_max=friction_max,
                output_dir=tmpdir
            )

            assert len(files) == count
            for f in files:
                assert os.path.exists(f)
                assert f.endswith(".urdf")

    def test_friction_distribution(self):
        """Test that friction values are distributed across the range."""
        count = 10
        friction_min = 0.1
        friction_max = 2.0
        seed = 12345

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = NovelObjectSet(seed=seed)
            files = gen.generate_set(
                count=count,
                friction_min=friction_min,
                friction_max=friction_max,
                output_dir=tmpdir
            )

            # Extract friction values from filenames
            mus = []
            for f in files:
                # Filename format: object_XXX_mu_X.XX.urdf
                basename = os.path.basename(f)
                mu_str = basename.split("mu_")[1].split(".urdf")[0]
                mus.append(float(mu_str))

            assert min(mus) >= friction_min - 0.01 # Allow small jitter
            assert max(mus) <= friction_max + 0.01
            assert len(set(mus)) == count # All unique (due to jitter)

    def test_reproducibility(self):
        """Test that same seed produces same output."""
        count = 3
        seed = 555
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                gen1 = NovelObjectSet(seed=seed)
                files1 = gen1.generate_set(count=count, friction_min=0.1, friction_max=1.0, output_dir=tmpdir1)

                gen2 = NovelObjectSet(seed=seed)
                files2 = gen2.generate_set(count=count, friction_min=0.1, friction_max=1.0, output_dir=tmpdir2)

                # Compare file contents
                for f1, f2 in zip(files1, files2):
                    with open(f1, 'r') as file1, open(f2, 'r') as file2:
                        assert file1.read() == file2.read()
