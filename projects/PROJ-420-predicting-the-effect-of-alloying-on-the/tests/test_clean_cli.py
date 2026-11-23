"""
Tests for the clean CLI (T046).
"""
import pytest
import tempfile
import json
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.clean_cli import main
from data.clean import run_cleaning_pipeline
from logging_config import get_logger

@pytest.fixture
def sample_raw_data():
    """Create sample raw data for testing."""
    data = [
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70000,  # MPa
            "composition": {"Al": 0.90, "Cu": 0.05, "Mg": 0.03, "Si": 0.02},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69000,
            "composition": {"Al": 0.88, "Cu": 0.06, "Mg": 0.04, "Zn": 0.02},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71000,
            "composition": {"Al": 0.87, "Cu": 0.05, "Mg": 0.04, "Si": 0.03, "Mn": 0.01},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.32,
            "young_modulus": 68000,
            "composition": {"Al": 0.86, "Cu": 0.07, "Mg": 0.03, "Zn": 0.04},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.36,
            "young_modulus": 72000,
            "composition": {"Al": 0.85, "Cu": 0.05, "Mg": 0.05, "Si": 0.03, "Mn": 0.02},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69500,
            "composition": {"Al": 0.89, "Cu": 0.04, "Mg": 0.03, "Si": 0.02, "Zn": 0.02},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70500,
            "composition": {"Al": 0.88, "Cu": 0.05, "Mg": 0.04, "Si": 0.02, "Mn": 0.01},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71500,
            "composition": {"Al": 0.87, "Cu": 0.06, "Mg": 0.03, "Zn": 0.03, "Mn": 0.01},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69000,
            "composition": {"Al": 0.86, "Cu": 0.05, "Mg": 0.05, "Si": 0.02, "Mn": 0.02},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70000,
            "composition": {"Al": 0.85, "Cu": 0.06, "Mg": 0.04, "Si": 0.03, "Zn": 0.02},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71000,
            "composition": {"Al": 0.84, "Cu": 0.05, "Mg": 0.05, "Si": 0.03, "Mn": 0.03},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69500,
            "composition": {"Al": 0.83, "Cu": 0.06, "Mg": 0.04, "Zn": 0.04, "Mn": 0.03},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70500,
            "composition": {"Al": 0.82, "Cu": 0.07, "Mg": 0.05, "Si": 0.03, "Mn": 0.03},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71500,
            "composition": {"Al": 0.81, "Cu": 0.06, "Mg": 0.06, "Si": 0.04, "Mn": 0.03},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69000,
            "composition": {"Al": 0.80, "Cu": 0.07, "Mg": 0.05, "Zn": 0.04, "Mn": 0.04},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70000,
            "composition": {"Al": 0.79, "Cu": 0.08, "Mg": 0.06, "Si": 0.04, "Mn": 0.03},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71000,
            "composition": {"Al": 0.78, "Cu": 0.07, "Mg": 0.07, "Si": 0.05, "Mn": 0.03},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69500,
            "composition": {"Al": 0.77, "Cu": 0.08, "Mg": 0.06, "Zn": 0.05, "Mn": 0.04},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70500,
            "composition": {"Al": 0.76, "Cu": 0.09, "Mg": 0.07, "Si": 0.05, "Mn": 0.03},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71500,
            "composition": {"Al": 0.75, "Cu": 0.08, "Mg": 0.08, "Si": 0.06, "Mn": 0.03},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69000,
            "composition": {"Al": 0.74, "Cu": 0.09, "Mg": 0.07, "Zn": 0.06, "Mn": 0.04},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70000,
            "composition": {"Al": 0.73, "Cu": 0.10, "Mg": 0.08, "Si": 0.06, "Mn": 0.03},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71000,
            "composition": {"Al": 0.72, "Cu": 0.09, "Mg": 0.09, "Si": 0.07, "Mn": 0.03},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69500,
            "composition": {"Al": 0.71, "Cu": 0.10, "Mg": 0.08, "Zn": 0.07, "Mn": 0.04},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70500,
            "composition": {"Al": 0.70, "Cu": 0.11, "Mg": 0.09, "Si": 0.07, "Mn": 0.03},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71500,
            "composition": {"Al": 0.69, "Cu": 0.10, "Mg": 0.10, "Si": 0.08, "Mn": 0.03},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69000,
            "composition": {"Al": 0.68, "Cu": 0.11, "Mg": 0.09, "Zn": 0.08, "Mn": 0.04},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70000,
            "composition": {"Al": 0.67, "Cu": 0.12, "Mg": 0.10, "Si": 0.08, "Mn": 0.03},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71000,
            "composition": {"Al": 0.66, "Cu": 0.11, "Mg": 0.11, "Si": 0.09, "Mn": 0.03},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69500,
            "composition": {"Al": 0.65, "Cu": 0.12, "Mg": 0.10, "Zn": 0.09, "Mn": 0.04},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70500,
            "composition": {"Al": 0.64, "Cu": 0.13, "Mg": 0.11, "Si": 0.09, "Mn": 0.03},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71500,
            "composition": {"Al": 0.63, "Cu": 0.12, "Mg": 0.12, "Si": 0.10, "Mn": 0.03},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69000,
            "composition": {"Al": 0.62, "Cu": 0.13, "Mg": 0.11, "Zn": 0.10, "Mn": 0.04},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70000,
            "composition": {"Al": 0.61, "Cu": 0.14, "Mg": 0.12, "Si": 0.10, "Mn": 0.03},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71000,
            "composition": {"Al": 0.60, "Cu": 0.13, "Mg": 0.13, "Si": 0.11, "Mn": 0.03},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69500,
            "composition": {"Al": 0.59, "Cu": 0.14, "Mg": 0.12, "Zn": 0.11, "Mn": 0.04},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70500,
            "composition": {"Al": 0.58, "Cu": 0.15, "Mg": 0.13, "Si": 0.11, "Mn": 0.03},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71500,
            "composition": {"Al": 0.57, "Cu": 0.14, "Mg": 0.14, "Si": 0.12, "Mn": 0.03},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69000,
            "composition": {"Al": 0.56, "Cu": 0.15, "Mg": 0.13, "Zn": 0.12, "Mn": 0.04},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70000,
            "composition": {"Al": 0.55, "Cu": 0.16, "Mg": 0.14, "Si": 0.12, "Mn": 0.03},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71000,
            "composition": {"Al": 0.54, "Cu": 0.15, "Mg": 0.15, "Si": 0.13, "Mn": 0.03},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69500,
            "composition": {"Al": 0.53, "Cu": 0.16, "Mg": 0.14, "Zn": 0.13, "Mn": 0.04},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70500,
            "composition": {"Al": 0.52, "Cu": 0.17, "Mg": 0.15, "Si": 0.13, "Mn": 0.03},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71500,
            "composition": {"Al": 0.51, "Cu": 0.16, "Mg": 0.16, "Si": 0.14, "Mn": 0.03},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69000,
            "composition": {"Al": 0.50, "Cu": 0.17, "Mg": 0.15, "Zn": 0.14, "Mn": 0.04},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70000,
            "composition": {"Al": 0.49, "Cu": 0.18, "Mg": 0.16, "Si": 0.14, "Mn": 0.03},
            "measurement_method": "Direct"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71000,
            "composition": {"Al": 0.48, "Cu": 0.17, "Mg": 0.17, "Si": 0.15, "Mn": 0.03},
            "measurement_method": "Resonant"
        },
        {
            "poisson_ratio": 0.33,
            "young_modulus": 69500,
            "composition": {"Al": 0.47, "Cu": 0.18, "Mg": 0.16, "Zn": 0.15, "Mn": 0.04},
            "measurement_method": "Impulse"
        },
        {
            "poisson_ratio": 0.34,
            "young_modulus": 70500,
            "composition": {"Al": 0.46, "Cu": 0.19, "Mg": 0.17, "Si": 0.15, "Mn": 0.03},
            "measurement_method": "Ultrasonic"
        },
        {
            "poisson_ratio": 0.35,
            "young_modulus": 71500,
            "composition": {"Al": 0.45, "Cu": 0.18, "Mg": 0.18, "Si": 0.16, "Mn": 0.03},
            "measurement_method": "Direct"
        }
    ]
    return data

def test_run_cleaning_pipeline_creates_output(sample_raw_data, tmp_path):
    """Test that run_cleaning_pipeline creates the output parquet file."""
    input_file = tmp_path / "raw_data.json"
    output_file = tmp_path / "cleaned_data.parquet"
    
    # Write sample data
    with open(input_file, "w") as f:
        json.dump(sample_raw_data, f)
    
    # Run pipeline
    df = run_cleaning_pipeline(input_file, output_file)
    
    # Verify output exists
    assert output_file.exists(), "Output parquet file was not created"
    
    # Verify content
    loaded_df = pd.read_parquet(output_file)
    assert len(loaded_df) >= 50, f"Expected at least 50 rows, got {len(loaded_df)}"
    assert "ilr_0" in loaded_df.columns, "ILR transformation not applied"
    assert "poisson_ratio" in loaded_df.columns, "Target column missing"

def test_clean_cli_main(sample_raw_data, tmp_path, monkeypatch):
    """Test the CLI main function."""
    input_file = tmp_path / "raw_data.json"
    output_file = tmp_path / "cleaned_data.parquet"
    
    # Write sample data
    with open(input_file, "w") as f:
        json.dump(sample_raw_data, f)
    
    # Mock sys.argv
    monkeypatch.setattr(sys, 'argv', [
        'clean_cli.py',
        '--input', str(input_file),
        '--output', str(output_file),
        '--log-level', 'INFO'
    ])
    
    # Run main
    main()
    
    # Verify output exists
    assert output_file.exists(), "Output parquet file was not created by CLI"

def test_independence_filter_excludes_missing_method(sample_raw_data, tmp_path):
    """Test that records with missing measurement_method are excluded."""
    # Add a record with missing measurement_method
    sample_raw_data.append({
        "poisson_ratio": 0.34,
        "young_modulus": 70000,
        "composition": {"Al": 0.90, "Cu": 0.05, "Mg": 0.05},
        "measurement_method": None
    })
    
    input_file = tmp_path / "raw_data.json"
    output_file = tmp_path / "cleaned_data.parquet"
    
    with open(input_file, "w") as f:
        json.dump(sample_raw_data, f)
    
    # Run pipeline
    df = run_cleaning_pipeline(input_file, output_file)
    
    # Verify the record with None measurement_method is excluded
    assert len(df) == len(sample_raw_data) - 1, "Record with missing measurement_method was not excluded"

def test_major_element_filter_excludes_low_sum(sample_raw_data, tmp_path):
    """Test that records with major element sum < 0.95 are excluded."""
    # Add a record with low major element sum
    sample_raw_data.append({
        "poisson_ratio": 0.34,
        "young_modulus": 70000,
        "composition": {"Al": 0.50, "Cu": 0.05, "Mg": 0.05},  # Sum = 0.60 < 0.95
        "measurement_method": "Ultrasonic"
    })
    
    input_file = tmp_path / "raw_data.json"
    output_file = tmp_path / "cleaned_data.parquet"
    
    with open(input_file, "w") as f:
        json.dump(sample_raw_data, f)
    
    # Run pipeline
    df = run_cleaning_pipeline(input_file, output_file)
    
    # Verify the record with low major sum is excluded
    assert len(df) == len(sample_raw_data) - 1, "Record with low major sum was not excluded"