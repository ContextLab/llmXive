"""
Pytest configuration and shared fixtures for all tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path so imports work
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Ensure code/ is in sys.path for imports."""
    project_root = Path(__file__).parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    
    # Also ensure tests directory is accessible
    yield
    
    # Cleanup if needed
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def sample_structure_dir(tmp_path):
    """Create a temporary directory with sample structure files."""
    sample_dir = tmp_path / "sample_structures"
    sample_dir.mkdir()
    
    # Create a dummy structure file
    dummy_file = sample_dir / "dummy_structure.cif"
    dummy_file.write_text(
        "data_sample\n"
        "_cell_length_a 5.0\n"
        "_cell_length_b 5.0\n"
        "_cell_length_c 5.0\n"
        "_cell_angle_alpha 90\n"
        "_cell_angle_beta 90\n"
        "_cell_angle_gamma 90\n"
        "_symmetry_space_group_name_H-M 'Pm-3m'\n"
        "_atom_site_label Fe\n"
        "_atom_site_type_symbol Fe\n"
        "_atom_site_fract_x 0.0\n"
        "_atom_site_fract_y 0.0\n"
        "_atom_site_fract_z 0.0\n"
    )
    return sample_dir

@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration file for testing."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(
        "project_name: test_project\n"
        "random_seed: 42\n"
        "data_paths:\n"
        "  raw: data/raw\n"
        "  processed: data/processed\n"
        "  results: results\n"
    )
    return config_file
