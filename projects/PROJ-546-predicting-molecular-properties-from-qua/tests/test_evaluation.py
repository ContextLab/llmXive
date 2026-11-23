"""
Integration tests for evaluation module.
"""
import json
import os
import tempfile
import pytest
import numpy as np
from pathlib import Path

# Mock data generation for tests
def generate_mock_csv(filepath, rows, headers):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', newline='') as f:
        f.write(','.join(headers) + '\n')
        for row in rows:
            f.write(','.join(map(str, row)) + '\n')

def generate_mock_splits(filepath, train, test):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump({"train_indices": train, "test_indices": test, "random_state": 42}, f)

@pytest.fixture
def mock_data(tmp_path):
    # Create temporary files
    semi_data = tmp_path / "data" / "descriptors_semi.csv"
    dft_data = tmp_path / "data" / "descriptors_dft.csv"
    splits = tmp_path / "state" / "splits.json"
    
    os.makedirs(tmp_path / "data")
    os.makedirs(tmp_path / "state")
    
    # Mock data: molecule_id, experimental_barrier, HOMO, LUMO, mayer
    semi_rows = [
        ("mol1", 10.0, -5.0, -2.0, 0.5),
        ("mol2", 12.0, -5.2, -2.1, 0.6),
        ("mol3", 11.0, -4.9, -1.9, 0.4),
        ("mol4", 13.0, -5.1, -2.2, 0.55),
        ("mol5", 10.5, -5.05, -2.05, 0.45),
        ("mol6", 11.5, -5.15, -2.15, 0.52),
    ]
    generate_mock_csv(str(semi_data), semi_rows, ["molecule_id", "experimental_barrier", "HOMO_energy", "LUMO_energy", "mayer_bond_order"])
    
    # DFT data: molecule_id, HOMO, LUMO, mayer (different values)
    dft_rows = [
        ("mol1", -5.5, -1.5, 0.6),
        ("mol2", -5.7, -1.6, 0.7),
        ("mol3", -5.4, -1.4, 0.5),
        ("mol4", -5.6, -1.7, 0.65),
        ("mol5", -5.55, -1.55, 0.55),
        ("mol6", -5.65, -1.65, 0.58),
    ]
    generate_mock_csv(str(dft_data), dft_rows, ["molecule_id", "HOMO_energy", "LUMO_energy", "mayer_bond_order"])
    
    generate_mock_splits(str(splits), [0, 1, 2], [3, 4, 5])
    
    return {
        "semi": str(semi_data),
        "dft": str(dft_data),
        "splits": str(splits),
        "output": str(tmp_path / "reports" / "evaluation.json")
    }

def test_t_test_null_hypothesis(mock_data):
    """
    Test that the paired t-test logic runs and produces a valid result structure.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from evaluate_models import main
    
    import argparse
    
    # Mock arguments
    class Args:
        semi_data = mock_data["semi"]
        dft_data = mock_data["dft"]
        splits = mock_data["splits"]
        output = mock_data["output"]
    
    # Run main
    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised an exception: {e}")
    
    # Verify output exists
    assert os.path.exists(mock_data["output"]), "Output file not created"
    
    with open(mock_data["output"], 'r') as f:
        report = json.load(f)
    
    assert "t_test" in report
    assert "statistic" in report["t_test"]
    assert "p_value" in report["t_test"]
    assert "null_hypothesis" in report["t_test"]
    assert report["t_test"]["null_hypothesis"] == "There is no difference in the error distribution between the Semi-Empirical RF and DFT RF models."
    assert "mae_semi" in report
    assert "mae_dft" in report

def test_mae_calculation(mock_data):
    """
    Test that MAE is calculated and reported.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from evaluate_models import main
    
    import argparse
    
    class Args:
        semi_data = mock_data["semi"]
        dft_data = mock_data["dft"]
        splits = mock_data["splits"]
        output = mock_data["output"]
    
    main()
    
    with open(mock_data["output"], 'r') as f:
        report = json.load(f)
    
    assert "mae_semi" in report
    assert "mae_dft" in report
    assert isinstance(report["mae_semi"], float)
    assert isinstance(report["mae_dft"], float)
    assert report["mae_semi"] >= 0
    assert report["mae_dft"] >= 0