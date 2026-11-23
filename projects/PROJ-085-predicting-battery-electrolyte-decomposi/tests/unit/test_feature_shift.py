import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil

from models.feature_shift_analyzer import (
    load_importance_data,
    identify_shifted_features,
    save_shift_analysis_report,
    run_feature_shift_pipeline
)

@pytest.fixture
def sample_importance_data():
    """Create sample importance data for testing."""
    return {
        "feature_importances": {
            "Low": {
                "homo_energy": 0.85,
                "lumo_energy": 0.72,
                "bond_length_c_o": 0.65,
                "dihedral_angle": 0.45,
                "band_gap": 0.30
            },
            "High": {
                "homo_energy": 0.90,
                "bond_length_c_o": 0.82,
                "solvent_dipole": 0.75,  # New feature in high bin
                "lumo_energy": 0.50,
                "bond_angle_o_c_o": 0.40
            }
        }
    }

@pytest.fixture
def temp_importance_file(sample_importance_data):
    """Create a temporary file with sample importance data."""
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "model_run.json")
    
    with open(file_path, 'w') as f:
        json.dump(sample_importance_data, f)
    
    yield file_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_load_importance_data(temp_importance_file, sample_importance_data):
    """Test loading importance data from file."""
    loaded_data = load_importance_data(temp_importance_file)
    assert loaded_data == sample_importance_data
    assert "feature_importances" in loaded_data
    assert "Low" in loaded_data["feature_importances"]
    assert "High" in loaded_data["feature_importances"]

def test_identify_shifted_features(sample_importance_data):
    """Test identifying features that enter top-3 in high bin but absent in low bin."""
    shifted, low_top, high_top = identify_shifted_features(
        sample_importance_data,
        low_potential_threshold=3,
        high_potential_threshold=3
    )
    
    # Low bin top-3: homo_energy, lumo_energy, bond_length_c_o
    assert low_top == ["homo_energy", "lumo_energy", "bond_length_c_o"]
    
    # High bin top-3: homo_energy, bond_length_c_o, solvent_dipole
    assert high_top == ["homo_energy", "bond_length_c_o", "solvent_dipole"]
    
    # Shifted: solvent_dipole (in high top-3, not in low top-3)
    assert shifted == ["solvent_dipole"]

def test_identify_shifted_features_no_shift(sample_importance_data):
    """Test when there are no shifted features."""
    # Modify data so top features are the same
    modified_data = {
        "feature_importances": {
            "Low": {
                "homo_energy": 0.90,
                "lumo_energy": 0.80,
                "bond_length_c_o": 0.70,
                "dihedral_angle": 0.50
            },
            "High": {
                "homo_energy": 0.95,
                "lumo_energy": 0.85,
                "bond_length_c_o": 0.75,
                "solvent_dipole": 0.60
            }
        }
    }
    
    shifted, low_top, high_top = identify_shifted_features(
        modified_data,
        low_potential_threshold=3,
        high_potential_threshold=3
    )
    
    # Both top-3 should be the same
    assert low_top == ["homo_energy", "lumo_energy", "bond_length_c_o"]
    assert high_top == ["homo_energy", "lumo_energy", "bond_length_c_o"]
    assert shifted == []

def test_save_shift_analysis_report(sample_importance_data):
    """Test saving the shift analysis report."""
    shifted, low_top, high_top = identify_shifted_features(sample_importance_data)
    
    temp_dir = tempfile.mkdtemp()
    output_file = os.path.join(temp_dir, "shift_report.json")
    
    try:
        saved_path = save_shift_analysis_report(
            shifted, low_top, high_top, output_file
        )
        
        assert os.path.exists(saved_path)
        
        with open(saved_path, 'r') as f:
            report = json.load(f)
        
        assert "shifted_features" in report
        assert report["shifted_features"] == shifted
        assert "spec_deviation_note" in report
        assert "3-5V" in report["spec_deviation_note"]
        assert "4V" in report["spec_deviation_note"]
    finally:
        shutil.rmtree(temp_dir)

def test_run_feature_shift_pipeline(temp_importance_file):
    """Test the complete pipeline."""
    temp_dir = tempfile.mkdtemp()
    output_file = os.path.join(temp_dir, "pipeline_report.json")
    
    try:
        result = run_feature_shift_pipeline(
            importance_file=temp_importance_file,
            output_file=output_file
        )
        
        assert "shifted_features" in result
        assert "low_bin_top_features" in result
        assert "high_bin_top_features" in result
        assert "report_path" in result
        assert os.path.exists(result["report_path"])
        assert "spec_deviation_note" in result
    finally:
        shutil.rmtree(temp_dir)

def test_shifted_features_not_in_low_bin(sample_importance_data):
    """Verify that all shifted features are indeed not in the low bin top."""
    shifted, low_top, high_top = identify_shifted_features(sample_importance_data)
    
    for feat in shifted:
        assert feat not in low_top, f"Shifted feature '{feat}' should not be in low bin top"
        assert feat in high_top, f"Shifted feature '{feat}' should be in high bin top"
