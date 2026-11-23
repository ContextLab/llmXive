"""
Unit tests for the validate_split module.
"""
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from rdkit import Chem

# Import the module under test
from code.modeling.validate_split import (
    load_dataset,
    get_murcko_scaffold,
    verify_zero_overlap,
    save_overlap_report,
    run_validation
)


@pytest.fixture
def sample_dataset_csv(tmp_path):
    """Create a sample dataset CSV file for testing."""
    data = {
        'smiles': [
            'CCO',  # Ethanol
            'CC(=O)O',  # Acetic acid
            'c1ccccc1',  # Benzene
            'c1ccccc1C',  # Toluene
            'CCN(CC)CC',  # Triethylamine
        ]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "test_dataset.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def sample_split_indices():
    """Create sample split indices for testing."""
    return {
        'train': [0, 2, 4],
        'test': [1, 3]
    }


@pytest.fixture
def overlapping_split_indices():
    """Create split indices with intentional scaffold overlap."""
    # Both benzene (index 2) and toluene (index 3) have the same scaffold
    return {
        'train': [2],  # Benzene scaffold
        'test': [3]    # Toluene has same scaffold
    }


def test_load_dataset(sample_dataset_csv):
    """Test loading a dataset from CSV."""
    df = load_dataset(sample_dataset_csv)
    assert len(df) == 5
    assert 'smiles' in df.columns


def test_load_dataset_missing_file():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_dataset("/nonexistent/path.csv")


def test_load_dataset_missing_column(tmp_path):
    """Test loading a dataset missing required columns."""
    data = {'other_column': [1, 2, 3]}
    df = pd.DataFrame(data)
    csv_path = tmp_path / "bad_dataset.csv"
    df.to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        load_dataset(str(csv_path))


def test_get_murcko_scaffold_valid():
    """Test scaffold generation for valid SMILES."""
    # Benzene should have a benzene scaffold
    scaffold = get_murcko_scaffold('c1ccccc1')
    assert scaffold is not None
    assert 'c1ccccc1' in scaffold or scaffold == 'c1ccccc1'

    # Ethanol has no ring system, scaffold is just the chain
    scaffold = get_murcko_scaffold('CCO')
    assert scaffold is not None


def test_get_murcko_scaffold_invalid():
    """Test scaffold generation for invalid SMILES."""
    scaffold = get_murcko_scaffold('invalid_smiles_xyz')
    assert scaffold is None


def test_verify_zero_overlap_no_overlap(sample_dataset_csv, sample_split_indices):
    """Test verification when there is no scaffold overlap."""
    df = load_dataset(sample_dataset_csv)
    is_valid, report = verify_zero_overlap(df, sample_split_indices)

    assert is_valid is True
    assert report['overlap_count'] == 0
    assert report['train_size'] == 3
    assert report['test_size'] == 2


def test_verify_zero_overlap_with_overlap(sample_dataset_csv, overlapping_split_indices):
    """Test verification when there is scaffold overlap."""
    df = load_dataset(sample_dataset_csv)
    is_valid, report = verify_zero_overlap(df, overlapping_split_indices)

    assert is_valid is False
    assert report['overlap_count'] > 0


def test_verify_zero_overlap_with_tolerance(sample_dataset_csv, overlapping_split_indices):
    """Test verification with non-zero tolerance."""
    df = load_dataset(sample_dataset_csv)
    is_valid, report = verify_zero_overlap(df, overlapping_split_indices, tolerance=1)

    # With tolerance=1, if overlap is 1, it should pass
    if report['overlap_count'] <= 1:
        assert is_valid is True
    else:
        assert is_valid is False


def test_save_overlap_report(tmp_path):
    """Test saving overlap report to JSON."""
    report = {
        'train_size': 10,
        'test_size': 5,
        'overlap_count': 0,
        'is_valid': True
    }
    output_path = str(tmp_path / "overlap_report.json")
    save_overlap_report(report, output_path)

    assert Path(output_path).exists()
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    assert saved_report['overlap_count'] == 0


def test_run_validation_success(sample_dataset_csv, sample_split_indices, tmp_path):
    """Test successful validation run."""
    split_path = str(tmp_path / "splits.json")
    output_path = str(tmp_path / "report.json")

    with open(split_path, 'w') as f:
        json.dump(sample_split_indices, f)

    is_valid = run_validation(
        dataset_path=sample_dataset_csv,
        split_indices_path=split_path,
        output_path=output_path
    )

    assert is_valid is True
    assert Path(output_path).exists()


def test_run_validation_failure(sample_dataset_csv, overlapping_split_indices, tmp_path):
    """Test failed validation run due to overlap."""
    split_path = str(tmp_path / "splits.json")
    output_path = str(tmp_path / "report.json")

    with open(split_path, 'w') as f:
        json.dump(overlapping_split_indices, f)

    is_valid = run_validation(
        dataset_path=sample_dataset_csv,
        split_indices_path=split_path,
        output_path=output_path
    )

    assert is_valid is False
    assert Path(output_path).exists()