"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports during testing
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    project_root = Path(__file__).parent.parent
    if str(project_root / "code") not in sys.path:
        sys.path.insert(0, str(project_root / "code"))
    yield
    # Cleanup not strictly necessary but good practice
    if str(project_root / "code") in sys.path:
        sys.path.remove(str(project_root / "code"))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure for tests."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    return data_dir

@pytest.fixture
def sample_image_path(tmp_path):
    """Create a dummy image file for testing feature extraction."""
    import numpy as np
    import cv2
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True)
    # Create a simple dummy image (100x100 RGB)
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    path = img_dir / "test_image.jpg"
    cv2.imwrite(str(path), img)
    return path
