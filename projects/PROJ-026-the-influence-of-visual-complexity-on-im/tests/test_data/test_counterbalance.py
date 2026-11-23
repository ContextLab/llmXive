"""
Tests for the counterbalance assignment generation (T027a).
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Import the function to test
from code.data.counterbalance import generate_counterbalance_assignments, load_complexity_categories, get_participant_ids

@pytest.fixture
def temp_project_root():
    """Create a temporary project structure for testing."""
    temp_dir = tempfile.mkdtemp()
    # Create necessary directories
    os.makedirs(os.path.join(temp_dir, "data", "processed"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "data", "raw", "responses"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "logs"), exist_ok=True)

    # Create a mock complexity_scores.csv
    complexity_data = {
        'filename': ['img1.png', 'img2.png', 'img3.png', 'img4.png'],
        'complexity_category': ['Low', 'High', 'Low', 'High']
    }
    pd.DataFrame(complexity_data).to_csv(
        os.path.join(temp_dir, "data", "processed", "complexity_scores.csv"), index=False
    )

    # Create a mock participants.csv
    participants_data = {
        'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006']
    }
    pd.DataFrame(participants_data).to_csv(
        os.path.join(temp_dir, "data", "raw", "responses", "participants.csv"), index=False
    )

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)

@patch('code.data.counterbalance.get_project_root')
@patch('code.data.counterbalance.get_data_path')
def test_generate_counterbalance_assignments(mock_get_data_path, mock_get_project_root, temp_project_root):
    """Test that counterbalance assignments are generated correctly."""
    # Mock get_project_root to return the temp directory
    mock_get_project_root.return_value = Path(temp_project_root)

    # Mock get_data_path if necessary (though not used directly in the logic we are testing)
    mock_get_data_path.return_value = Path(temp_project_root) / "data"

    # Run the function
    df = generate_counterbalance_assignments()

    # Assertions
    assert 'participant_id' in df.columns
    assert 'session_order' in df.columns
    assert 'stimulus_set_id' in df.columns

    # Check that all participant IDs are present
    assert set(df['participant_id'].tolist()) == {'P001', 'P002', 'P003', 'P004', 'P005', 'P006'}

    # Check session orders
    session_orders = df['session_order'].tolist()
    assert all(order in ['Low-High', 'High-Low'] for order in session_orders)

    # Check stimulus set IDs
    stimulus_sets = df['stimulus_set_id'].tolist()
    assert all(set_id in ['SetA', 'SetB'] for set_id in stimulus_sets)

    # Check the mapping: SetA -> Low-High, SetB -> High-Low
    for _, row in df.iterrows():
        if row['session_order'] == 'Low-High':
            assert row['stimulus_set_id'] == 'SetA'
        elif row['session_order'] == 'High-Low':
            assert row['stimulus_set_id'] == 'SetB'

    # Check that the assignment is randomized (seeded)
    # With 6 participants, we expect 3 Low-High and 3 High-Low
    assert df['session_order'].value_counts()['Low-High'] == 3
    assert df['session_order'].value_counts()['High-Low'] == 3

@patch('code.data.counterbalance.get_project_root')
def test_load_complexity_categories(mock_get_project_root, temp_project_root):
    """Test loading complexity categories from CSV."""
    mock_get_project_root.return_value = Path(temp_project_root)

    low_images, high_images = load_complexity_categories()

    assert set(low_images) == {'img1.png', 'img3.png'}
    assert set(high_images) == {'img2.png', 'img4.png'}

@patch('code.data.counterbalance.get_project_root')
def test_get_participant_ids_from_real_data(mock_get_project_root, temp_project_root):
    """Test getting participant IDs from real data file."""
    mock_get_project_root.return_value = Path(temp_project_root)

    ids = get_participant_ids()
    assert ids == ['P001', 'P002', 'P003', 'P004', 'P005', 'P006']

@patch('code.data.counterbalance.get_project_root')
def test_get_participant_ids_synthetic(mock_get_project_root, temp_project_root):
    """Test generating synthetic participant IDs when real data is missing."""
    # Remove the real participants file
    os.remove(os.path.join(temp_project_root, "data", "raw", "responses", "participants.csv"))

    mock_get_project_root.return_value = Path(temp_project_root)

    ids = get_participant_ids()

    # Should generate 60 synthetic IDs
    assert len(ids) == 60
    assert all(pid.startswith('P') for pid in ids)
    assert ids[0] == 'P001'
    assert ids[-1] == 'P060'

@patch('code.data.counterbalance.get_project_root')
def test_generate_counterbalance_assignments_empty_complexity(mock_get_project_root, temp_project_root):
    """Test that an error is raised if complexity categories are missing."""
    # Create an empty complexity_scores.csv
    pd.DataFrame(columns=['filename', 'complexity_category']).to_csv(
        os.path.join(temp_project_root, "data", "processed", "complexity_scores.csv"), index=False
    )

    mock_get_project_root.return_value = Path(temp_project_root)

    with pytest.raises(ValueError, match="Complexity categories must contain at least one image in both Low and High groups"):
        generate_counterbalance_assignments()

@patch('code.data.counterbalance.get_project_root')
def test_generate_counterbalance_assignments_no_participants(mock_get_project_root, temp_project_root):
    """Test that an error is raised if no participant IDs are found."""
    # Remove the participants file
    os.remove(os.path.join(temp_project_root, "data", "raw", "responses", "participants.csv"))

    # Mock get_participant_ids to return an empty list
    with patch('code.data.counterbalance.get_participant_ids', return_value=[]):
        mock_get_project_root.return_value = Path(temp_project_root)

        with pytest.raises(ValueError, match="No participant IDs found or generated"):
            generate_counterbalance_assignments()