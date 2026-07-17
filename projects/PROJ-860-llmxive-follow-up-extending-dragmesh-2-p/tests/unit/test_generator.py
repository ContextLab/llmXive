import os
import pytest
import tempfile
import xml.etree.ElementTree as ET
from code.generator import NovelObjectSet

def test_generator_creates_directory():
    """Test that the generator creates the output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sub_dir = os.path.join(tmpdir, "sub", "nested")
        gen = NovelObjectSet(sub_dir)
        # Just init doesn't create, but generate does.
        gen.generate_set(count=1)
        assert os.path.exists(sub_dir)

def test_generator_creates_valid_urdf():
    """Test that generated URDF is valid XML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = NovelObjectSet(tmpdir)
        files = gen.generate_set(count=3)
        
        for f_path in files:
            assert os.path.exists(f_path)
            try:
                tree = ET.parse(f_path)
                root = tree.getroot()
                assert root.tag == "robot"
            except ET.ParseError as e:
                pytest.fail(f"Invalid URDF XML: {e}")

def test_generator_friction_distribution():
    """Test that friction values are within expected range [0.1, 2.0]."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = NovelObjectSet(tmpdir, seed=123)
        files = gen.generate_set(count=10)
        
        for f_path in files:
            tree = ET.parse(f_path)
            root = tree.getroot()
            
            # Check friction in contact tags
            contact_tags = root.findall(".//contact")
            for contact in contact_tags:
                friction_val = float(contact.find("friction").get("value"))
                assert 0.1 <= friction_val <= 2.0, f"Friction {friction_val} out of range"

def test_generator_articulated_structure():
    """Test that objects have multiple links and joints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = NovelObjectSet(tmpdir)
        files = gen.generate_set(count=1)
        
        for f_path in files:
            tree = ET.parse(f_path)
            root = tree.getroot()
            
            links = root.findall(".//link")
            joints = root.findall(".//joint")
            
            # Should have base + 3 links by default
            assert len(links) >= 4
            assert len(joints) >= 3