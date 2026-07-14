"""Unit tests for T033: validate_plot.py edge counting logic."""
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling.validate_plot import count_svg_edges


def create_mock_svg(num_lines: int, num_paths: int, has_namespace: bool = False) -> str:
    """Helper to create a mock SVG string with specified number of line and path elements."""
    ns = "http://www.w3.org/2000/svg"
    if has_namespace:
        root = ET.Element(f"{{{ns}}}svg")
        ET.SubElement(root, "title").text = "Test"
        for _ in range(num_lines):
            ET.SubElement(root, f"{{{ns}}}line")
        for _ in range(num_paths):
            ET.SubElement(root, f"{{{ns}}}path")
    else:
        root = ET.Element("svg")
        ET.SubElement(root, "title").text = "Test"
        for _ in range(num_lines):
            ET.SubElement(root, "line")
        for _ in range(num_paths):
            ET.SubElement(root, "path")

    tree = ET.ElementTree(root)
    from io import StringIO
    buf = StringIO()
    tree.write(buf, encoding="unicode", xml_declaration=False)
    return buf.getvalue()


def test_count_svg_edges_passes():
    """Test that count_svg_edges returns True when edge count >= 50."""
    svg_content = create_mock_svg(num_lines=30, num_paths=25)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        temp_path = f.name

    try:
        success, count, msg = count_svg_edges(temp_path, min_edges=50)
        assert success is True
        assert count == 55
        assert "passed" in msg.lower()
    finally:
        os.unlink(temp_path)


def test_count_svg_edges_fails_low_count():
    """Test that count_svg_edges returns False when edge count < 50."""
    svg_content = create_mock_svg(num_lines=10, num_paths=10)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        temp_path = f.name

    try:
        success, count, msg = count_svg_edges(temp_path, min_edges=50)
        assert success is False
        assert count == 20
        assert "below minimum" in msg.lower()
    finally:
        os.unlink(temp_path)


def test_count_svg_edges_file_not_found():
    """Test that count_svg_edges handles missing files gracefully."""
    success, count, msg = count_svg_edges("/nonexistent/path/file.svg")
    assert success is False
    assert count == 0
    assert "not found" in msg.lower()


def test_count_svg_edges_with_namespace():
    """Test parsing SVG with XML namespace (common in some renderers)."""
    svg_content = create_mock_svg(num_lines=60, num_paths=0, has_namespace=True)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        temp_path = f.name

    try:
        success, count, msg = count_svg_edges(temp_path, min_edges=50)
        assert success is True
        assert count == 60
    finally:
        os.unlink(temp_path)


def test_count_svg_edges_zero_edges():
    """Test handling of SVG with no lines or paths."""
    svg_content = create_mock_svg(num_lines=0, num_paths=0)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        temp_path = f.name

    try:
        success, count, msg = count_svg_edges(temp_path, min_edges=1)
        assert success is False
        assert count == 0
        assert "below minimum" in msg.lower()
    finally:
        os.unlink(temp_path)