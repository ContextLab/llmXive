"""
Unit tests for the sample_check module (T037).
"""
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Adjust imports to match project structure
from code.data_ingestion.sample_check import (
    load_processed_data,
    check_sample_counts,
    evaluate_data_sufficiency,
    generate_report,
    main
)
from code.utils.config import DATA_PROCESSED_PATH

@pytest.fixture
def sample_csv_path(tmp_path):
    """Create a temporary CSV file with sample data."""
    data = {
        "SampleID": [f"S{i}" for i in range(20)],
        "Species": (
            ["Arabidopsis"] * 6 +
            ["Rice"] * 6 +
            ["Wheat"] * 6 +
            ["Arabidopsis"] * 2  # Extra to test counts
        ),
        "StressCondition": (
            ["Drought"] * 3 +
            ["Heat"] * 3 +
            ["Salinity"] * 3 +
            ["Drought"] * 3 +
            ["Heat"] * 3 +
            ["Salinity"] * 3 +
            ["Drought"] * 2
        ),
        "Protein1": [1.0] * 20,
        "Protein2": [2.0] * 20
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "processed_data.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def insufficient_csv_path(tmp_path):
    """Create a temporary CSV with insufficient samples."""
    data = {
        "SampleID": [f"S{i}" for i in range(6)],
        "Species": ["Arabidopsis"] * 6,
        "StressCondition": ["Drought"] * 3 + ["Heat"] * 3,
        "Protein1": [1.0] * 6,
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "insufficient_data.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def missing_species_csv_path(tmp_path):
    """Create a temporary CSV with no target species."""
    data = {
        "SampleID": [f"S{i}" for i in range(10)],
        "Species": ["Maize"] * 10,
        "StressCondition": ["Drought"] * 10,
        "Protein1": [1.0] * 10,
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "no_target_species.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

def test_load_processed_data(sample_csv_path):
    """Test loading a valid CSV."""
    df = load_processed_data(sample_csv_path)
    assert not df.empty
    assert "Species" in df.columns
    assert "StressCondition" in df.columns

def test_check_sample_counts_sufficient(sample_csv_path):
    """Test counting samples when data is sufficient."""
    df = load_processed_data(sample_csv_path)
    results = check_sample_counts(df)

    # Check that we found the species
    assert "Arabidopsis" in results["total_species_found"]
    assert "Rice" in results["total_species_found"]
    assert "Wheat" in results["total_species_found"]

    # Check counts
    # Arabidopsis Drought: 3 + 2 = 5
    key_arab_drought = ("Arabidopsis", "Drought")
    assert results["counts"][key_arab_drought] == 5
    assert key_arab_drought in results["passed"]

    # Rice Salinity: 3
    key_rice_sal = ("Rice", "Salinity")
    assert results["counts"][key_rice_sal] == 3
    assert key_rice_sal in results["failed"]

def test_check_sample_counts_insufficient(insufficient_csv_path):
    """Test counting samples when data is insufficient."""
    df = load_processed_data(insufficient_csv_path)
    results = check_sample_counts(df)

    # Arabidopsis Drought: 3 (Fail)
    key = ("Arabidopsis", "Drought")
    assert results["counts"][key] == 3
    assert key in results["failed"]

def test_evaluate_data_sufficiency_sufficient(sample_csv_path):
    """Test evaluation when data is sufficient."""
    df = load_processed_data(sample_csv_path)
    results = check_sample_counts(df)
    is_sufficient, message = evaluate_data_sufficiency(results)
    assert is_sufficient is True
    assert "verified" in message.lower()

def test_evaluate_data_sufficiency_insufficient(insufficient_csv_path):
    """Test evaluation when data is insufficient for ALL species/conditions."""
    df = load_processed_data(insufficient_csv_path)
    results = check_sample_counts(df)
    is_sufficient, message = evaluate_data_sufficiency(results)
    assert is_sufficient is False
    assert "halt" in message.lower() or "insufficient" in message.lower()

def test_evaluate_data_sufficiency_no_target_species(missing_species_csv_path):
    """Test evaluation when no target species are found."""
    df = load_processed_data(missing_species_csv_path)
    results = check_sample_counts(df)
    is_sufficient, message = evaluate_data_sufficiency(results)
    assert is_sufficient is False
    assert "No target species" in message

def test_generate_report(sample_csv_path, tmp_path):
    """Test report generation."""
    df = load_processed_data(sample_csv_path)
    results = check_sample_counts(df)
    output_path = tmp_path / "report.json"
    generate_report(results, output_path)

    assert output_path.exists()
    with open(output_path) as f:
        report = json.load(f)
    assert "status" in report
    assert "counts" in report
    assert "passed_conditions" in report

def test_main_success(sample_csv_path, tmp_path, monkeypatch):
    """Test main function returning 0."""
    # Mock the config paths to use tmp dir
    monkeypatch.patch("code.data_ingestion.sample_check.DATA_PROCESSED_PATH", lambda: Path(tmp_path))
    # We need to copy the file to the expected location or mock load_processed_data
    # For simplicity, we'll just test the logic flow by passing the path directly
    # But main() uses load_processed_data() without args, so it looks in default.
    # Let's create the file in the default location for the test.
    default_path = Path(tmp_path) / "processed_data.csv"
    df = pd.read_csv(sample_csv_path)
    df.to_csv(default_path, index=False)

    # Mock PROJECT_ROOT
    monkeypatch.patch("code.data_ingestion.sample_check.PROJECT_ROOT", str(tmp_path))

    exit_code = main()
    assert exit_code == 0

def test_main_failure(missing_species_csv_path, tmp_path, monkeypatch):
    """Test main function returning 1 when data is insufficient."""
    default_path = Path(tmp_path) / "processed_data.csv"
    df = pd.read_csv(missing_species_csv_path)
    df.to_csv(default_path, index=False)

    monkeypatch.patch("code.data_ingestion.sample_check.PROJECT_ROOT", str(tmp_path))

    exit_code = main()
    assert exit_code == 1
