"""
Shared pytest configuration and fixtures for unit tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add code directory to path
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add code directory to sys.path for all tests."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Cleanup if needed

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "stratified").mkdir()
    (data_dir / "features").mkdir()
    (data_dir / "results").mkdir()
    return data_dir

@pytest.fixture
def sample_image(tmp_path):
    """Create a sample image file."""
    import cv2
    import numpy as np
    
    img_path = tmp_path / "sample.png"
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), img)
    return img_path

@pytest.fixture
def sample_sequence_dir(tmp_path):
    """Create a sample sequence directory with multiple frames."""
    import cv2
    import numpy as np
    
    seq_dir = tmp_path / "test_sequence"
    seq_dir.mkdir()
    
    for i in range(5):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = seq_dir / f"frame_{i:04d}.png"
        cv2.imwrite(str(img_path), img)
    
    return seq_dir