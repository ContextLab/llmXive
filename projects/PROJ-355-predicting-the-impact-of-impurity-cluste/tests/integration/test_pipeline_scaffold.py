"""
Integration test to verify the basic pipeline structure and imports.

This test ensures that all core modules can be imported and basic
functions are accessible without errors.
"""
import pytest
from pathlib import Path
import sys

# Ensure code is importable
project_root = Path(__file__).parent.parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

def test_import_config():
    """Test that config module can be imported."""
    from config import get_project_root, get_data_paths, get_config_summary
    assert callable(get_project_root)
    assert callable(get_data_paths)
    assert callable(get_config_summary)

def test_import_validators():
    """Test that validators module can be imported."""
    from validators import validate_citations, validate_schema
    assert callable(validate_citations)
    assert callable(validate_schema)

def test_import_download():
    """Test that download module can be imported."""
    from data.download import download_bulk_configs, load_schema, validate_dataset_schema
    assert callable(download_bulk_configs)
    assert callable(load_schema)
    assert callable(validate_dataset_schema)

def test_import_gb_builder():
    """Test that gb_builder module can be imported."""
    from data.gb_builder import build_gb_supercell, insert_impurity, save_structure
    assert callable(build_gb_supercell)
    assert callable(insert_impurity)
    assert callable(save_structure)

def test_import_descriptors():
    """Test that descriptors module can be imported."""
    from data.descriptors import compute_rdf_peak, compute_pair_correlation, compute_voronoi_neighbor_counts
    assert callable(compute_rdf_peak)
    assert callable(compute_pair_correlation)
    assert callable(compute_voronoi_neighbor_counts)

def test_import_simulate_energy():
    """Test that simulate_energy module can be imported."""
    from data.simulate_energy import apply_structural_perturbation, calculate_segregation_energy, run_simulation
    assert callable(apply_structural_perturbation)
    assert callable(calculate_segregation_energy)
    assert callable(run_simulation)

def test_import_modeling_train():
    """Test that modeling.train module can be imported (if it exists)."""
    try:
        from modeling.train import train_model
        assert callable(train_model)
    except ImportError:
        # Module might not exist yet in early phases
        pass
