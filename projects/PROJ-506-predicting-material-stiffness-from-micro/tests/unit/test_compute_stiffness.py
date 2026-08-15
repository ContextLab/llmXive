"""
Unit tests for the stiffness tensor calculator (T018).
"""
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.data_generation.compute_stiffness import load_microstructure, compute_stiffness_tensor, main

@pytest.fixture
def temp_image(tmp_path):
    """Create a temporary microstructure image for testing."""
    img_path = tmp_path / "micro_123.png"
    # Create a simple synthetic image: 128x128, mostly 1.0 (matrix) with a small 0.0 (void) center
    img = np.ones((128, 128), dtype=np.float64)
    img[60:68, 60:68] = 0.0  # Small void
    # Save as uint8 (0-255) to mimic real generation
    img_uint8 = (img * 255).astype(np.uint8)
    from skimage import io
    io.imsave(str(img_path), img_uint8)
    return img_path

def test_load_microstructure_success(temp_image):
    """Test loading a valid image."""
    img = load_microstructure(temp_image)
    assert isinstance(img, np.ndarray)
    assert img.shape == (128, 128)
    assert img.dtype == np.float64
    # Check normalization (0-1 range)
    assert img.min() >= 0.0
    assert img.max() <= 1.0

def test_load_microstructure_not_found():
    """Test loading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_microstructure(Path("non_existent.png"))

@patch('code.data_generation.compute_stiffness.compute_effective_stiffness')
def test_compute_stiffness_tensor(mock_fft_solver, temp_image):
    """Test stiffness computation calls the solver correctly."""
    # Setup mock return value (3x3 plane strain stiffness)
    mock_stiffness = np.eye(3) * 100.0
    mock_fft_solver.return_value = mock_stiffness

    img = load_microstructure(temp_image)
    result = compute_stiffness_tensor(img)

    mock_fft_solver.assert_called_once_with(img)
    assert isinstance(result, np.ndarray)
    assert result.shape == (3, 3)
    np.testing.assert_array_almost_equal(result, mock_stiffness)

@patch('code.data_generation.compute_stiffness.compute_effective_stiffness')
def test_main_integration(mock_fft_solver, tmp_path, temp_image):
    """Test the main function orchestrates loading, computing, and saving."""
    # Mock the solver to return a constant stiffness
    mock_stiffness = np.ones((3, 3)) * 50.0
    mock_fft_solver.return_value = mock_stiffness

    # Move the temp image to the expected location in tmp_path
    # We need to simulate the data/raw structure
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    # Copy the test image to the raw dir
    import shutil
    target_img = raw_dir / "micro_123.png"
    shutil.copy(str(temp_image), str(target_img))

    # Patch Path to point to our temp directory
    with patch('code.data_generation.compute_stiffness.Path', return_value=raw_dir):
        # We need to patch the glob behavior too
        with patch.object(Path, 'glob', return_value=[target_img]):
            # Patch the output path
            with patch('code.data_generation.compute_stiffness.json.dump') as mock_json_dump:
                main()

                # Verify json.dump was called (indicating success)
                assert mock_json_dump.called

                # Check that the mock solver was called with the loaded image
                # Note: Since we mocked Path, the actual load logic inside main might differ,
                # but the flow should be triggered.
                # A more robust test would assert the specific arguments passed to dump.
                call_args = mock_json_dump.call_args[0][0]
                assert call_args["successful"] == 1
                assert call_args["failed"] == 0
                assert len(call_args["data"]) == 1
                assert call_args["data"][0]["seed"] == 123
                assert call_args["data"][0]["status"] == "success"