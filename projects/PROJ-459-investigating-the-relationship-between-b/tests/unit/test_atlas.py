"""
Unit tests for code/utils/atlas.py
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import nibabel as nib
from pathlib import Path

# We need to mock the file system and the atlas loading
# because the real atlas might not be present in the test environment.

from code.utils.atlas import load_atlas, map_to_yeo, _name_to_yeo_id

@pytest.fixture
def mock_atlas_data():
    """Create mock atlas data and labels."""
    # Create a 3D array with some ROI IDs
    data = np.zeros((10, 10, 10), dtype=int)
    # Fill with some ROI IDs
    data[0, 0, 0] = 1
    data[0, 0, 1] = 2
    data[0, 0, 2] = 3
    # ...
    
    # Create a mock image
    img = nib.Nifti1Image(data, np.eye(4))
    
    # Create a mock labels file content
    labels_content = [
        "1 Visual",
        "2 Somatomotor",
        "3 DorsalAttention",
        "4 SalienceVentralAttention",
        "5 Limbic",
        "6 Frontoparietal",
        "7 DefaultModeNetwork"
    ]
    
    return img, labels_content

def test_name_to_yeo_id():
    """Test the network name to Yeo ID mapping."""
    assert _name_to_yeo_id("Visual") == 1
    assert _name_to_yeo_id("Somatomotor") == 2
    assert _name_to_yeo_id("DorsalAttention") == 3
    assert _name_to_yeo_id("SalienceVentralAttention") == 4
    assert _name_to_yeo_id("Limbic") == 5
    assert _name_to_yeo_id("Frontoparietal") == 6
    assert _name_to_yeo_id("DefaultModeNetwork") == 7
    assert _name_to_yeo_id("default_mode_network") == 7
    assert _name_to_yeo_id("Salience") == 4

def test_name_to_yeo_id_unknown():
    """Test that unknown network names raise an error."""
    with pytest.raises(ValueError):
        _name_to_yeo_id("UnknownNetwork")

@patch('code.utils.atlas.ATLAS_PATH', Path('/mock/atlas.nii.gz'))
@patch('code.utils.atlas.LABELS_PATH', Path('/mock/labels.txt'))
@patch('nibabel.load')
@patch('builtins.open', new_callable=MagicMock)
def test_load_atlas(mock_open, mock_nib_load, mock_atlas_path, mock_labels_path):
    """Test loading the atlas with mocked data."""
    # Setup mocks
    mock_img = MagicMock()
    mock_img.get_fdata.return_value = np.array([[[1, 2], [3, 4]]])
    mock_nib_load.return_value = mock_img
    
    mock_file = MagicMock()
    mock_file.__enter__.return_value = [
        "1 Visual\n",
        "2 Somatomotor\n"
    ]
    mock_open.return_value = mock_file
    
    label_map, network_dict = load_atlas()
    
    assert label_map.shape == (2, 2)
    assert network_dict[1] == "Visual"
    assert network_dict[2] == "Somatomotor"

@patch('code.utils.atlas.ATLAS_PATH', Path('/mock/atlas.nii.gz'))
@patch('code.utils.atlas.LABELS_PATH', Path('/mock/labels.txt'))
@patch('nibabel.load')
@patch('builtins.open', new_callable=MagicMock)
def test_map_to_yeo(mock_open, mock_nib_load, mock_atlas_path, mock_labels_path):
    """Test mapping ROI IDs to Yeo networks."""
    # Setup mocks
    mock_img = MagicMock()
    mock_img.get_fdata.return_value = np.array([[[1, 2], [3, 4]]])
    mock_nib_load.return_value = mock_img
    
    mock_file = MagicMock()
    mock_file.__enter__.return_value = [
        "1 Visual\n",
        "2 Somatomotor\n",
        "3 DorsalAttention\n",
        "4 SalienceVentralAttention\n"
    ]
    mock_open.return_value = mock_file
    
    # Load atlas to get network map
    _, network_map = load_atlas()
    
    # Map ROIs
    roi_ids = [1, 2, 3, 4]
    yoe_ids = map_to_yeo(roi_ids, network_map)
    
    assert yoe_ids == [1, 2, 3, 4]

@patch('code.utils.atlas.ATLAS_PATH', Path('/mock/atlas.nii.gz'))
@patch('code.utils.atlas.LABELS_PATH', Path('/mock/labels.txt'))
@patch('nibabel.load')
@patch('builtins.open', new_callable=MagicMock)
def test_map_to_yeo_missing_roi(mock_open, mock_nib_load, mock_atlas_path, mock_labels_path):
    """Test mapping with a missing ROI ID."""
    # Setup mocks
    mock_img = MagicMock()
    mock_img.get_fdata.return_value = np.array([[[1, 2], [3, 4]]])
    mock_nib_load.return_value = mock_img
    
    mock_file = MagicMock()
    mock_file.__enter__.return_value = [
        "1 Visual\n",
        "2 Somatomotor\n"
    ]
    mock_open.return_value = mock_file
    
    _, network_map = load_atlas()
    
    # Try to map an ROI that is not in the map
    with pytest.raises(ValueError):
        map_to_yeo([1, 999], network_map)