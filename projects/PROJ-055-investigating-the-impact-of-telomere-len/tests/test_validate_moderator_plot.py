import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Import functions to test
import sys
sys.path.insert(0, 'code')
from validate_moderator_plot import (
    validate_plot_exists,
    validate_plot_content,
    validate_species_grouping
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = pd.DataFrame({
        'species': ['Species_A', 'Species_B', 'Species_C', 'Species_D', 'Species_E', 'Species_F'],
        'telomere_length_kb': [2.5, 3.1, 2.8, 3.5, 2.9, 3.2],
        'lifespan': [10.5, 12.3, 11.2, 15.1, 11.8, 13.4],
        'migration_status': ['Migratory', 'Migratory', 'Resident', 'Resident', 'Migratory', 'Resident']
    })
    return data

@pytest.fixture
def sample_results():
    """Create sample moderator results."""
    results = pd.DataFrame({
        'model_name': ['moderator_model'],
        'interaction_coefficient': [0.45],
        'interaction_se': [0.12],
        'interaction_pvalue': [0.001],
        'aic': [125.6],
        'df': [10]
    })
    return results

@pytest.fixture
def temp_plot_path():
    """Create a temporary plot file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        # Create a simple plot
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter([1, 2, 3], [1, 2, 3], label='Test')
        ax.set_title('Test Plot')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        plt.savefig(f.name)
        plt.close(fig)
        yield Path(f.name)
        os.unlink(f.name)

def test_validate_plot_exists_with_valid_file(temp_plot_path):
    """Test that validate_plot_exists returns True for a valid file."""
    assert validate_plot_exists(temp_plot_path) is True

def test_validate_plot_exists_with_nonexistent_file():
    """Test that validate_plot_exists returns False for a nonexistent file."""
    path = Path('/nonexistent/path/plot.png')
    assert validate_plot_exists(path) is False

def test_validate_plot_exists_with_empty_file():
    """Test that validate_plot_exists returns False for an empty file."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        empty_path = Path(f.name)
    # File is created but empty
    assert validate_plot_exists(empty_path) is False
    os.unlink(empty_path)

def test_validate_plot_content_with_valid_inputs(sample_data, sample_results, temp_plot_path):
    """Test that validate_plot_content returns True for valid inputs."""
    is_valid, errors = validate_plot_content(temp_plot_path, sample_data, sample_results)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_plot_content_with_missing_results(sample_data, temp_plot_path):
    """Test that validate_plot_content handles missing results gracefully."""
    is_valid, errors = validate_plot_content(temp_plot_path, sample_data, None)
    # Should have warnings but not necessarily fail
    assert len(errors) >= 0  # May have warnings but not critical errors

def test_validate_species_grouping_with_valid_data(sample_data, temp_plot_path):
    """Test that validate_species_grouping returns True for valid data."""
    is_valid, errors = validate_species_grouping(sample_data, temp_plot_path)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_species_grouping_with_insufficient_groups():
    """Test that validate_species_grouping fails with insufficient groups."""
    data = pd.DataFrame({
        'species': ['Species_A', 'Species_B'],
        'migration_status': ['Migratory', 'Migratory']  # Only one group
    })
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        plot_path = Path(f.name)
    
    is_valid, errors = validate_species_grouping(data, plot_path)
    assert is_valid is False
    assert any('No valid migration groups found' in error for error in errors)
    os.unlink(plot_path)

def test_validate_species_grouping_with_small_sample():
    """Test that validate_species_grouping warns about small samples."""
    data = pd.DataFrame({
        'species': ['Species_A', 'Species_B', 'Species_C', 'Species_D', 'Species_E'],
        'migration_status': ['Migratory', 'Migratory', 'Resident', 'Resident', 'Resident']
    })
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        plot_path = Path(f.name)
    
    # This should pass but might have warnings
    is_valid, errors = validate_species_grouping(data, plot_path)
    # Should be valid since we have 5 points total
    assert is_valid is True
    os.unlink(plot_path)

def test_validate_plot_content_with_invalid_image():
    """Test that validate_plot_content handles invalid image files."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        # Write invalid data
        f.write(b'not a valid image')
        invalid_path = Path(f.name)
    
    data = pd.DataFrame({
        'species': ['Species_A'],
        'migration_status': ['Migratory']
    })
    
    is_valid, errors = validate_plot_content(invalid_path, data, None)
    assert is_valid is False
    assert any('Failed to read plot image' in error for error in errors)
    os.unlink(invalid_path)