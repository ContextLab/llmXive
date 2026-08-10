"""
Contract test for `SpectralFeatures` schema in tests/contract/test_spectral_features.py.

This test validates that the spectral feature extraction pipeline (T012)
produces output conforming to the expected schema defined in the project
specifications. It ensures that the normalized PSD data and derived metrics
are structured correctly before being used in SDC calculations (T013-SDC).
"""
import os
import json
import numpy as np
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Constants matching project config
SEQ_LEN = 512
N_FFT = 256
FREQ_BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma_low": (30, 45),
    "gamma_high": (45, 80),
}

def load_spectral_features(path: Path) -> Dict[str, Any]:
    """
    Load the spectral features file produced by preprocessing.
    
    Expected schema:
    {
        "metadata": {
            "seq_len": int,
            "n_fft": int,
            "sampling_rate": float,
            "normalization": "unit_area"
        },
        "data": [
            {
                "sample_id": str,
                "frequencies": List[float],
                "psd_normalized": List[float],
                "band_power": {
                    "band_name": float,
                    ...
                },
                "peak_frequency": float,
                "peak_power": float
            },
            ...
        ]
    }
    """
    if not path.exists():
        raise FileNotFoundError(f"Spectral features file not found: {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def validate_metadata(metadata: Dict[str, Any]) -> None:
    """Validate the metadata section of the schema."""
    assert "seq_len" in metadata, "Missing 'seq_len' in metadata"
    assert isinstance(metadata["seq_len"], int), "'seq_len' must be an integer"
    assert metadata["seq_len"] > 0, "'seq_len' must be positive"
    
    assert "n_fft" in metadata, "Missing 'n_fft' in metadata"
    assert isinstance(metadata["n_fft"], int), "'n_fft' must be an integer"
    
    assert "sampling_rate" in metadata, "Missing 'sampling_rate' in metadata"
    assert isinstance(metadata["sampling_rate"], (int, float)), "'sampling_rate' must be numeric"
    
    assert "normalization" in metadata, "Missing 'normalization' in metadata"
    assert metadata["normalization"] == "unit_area", "Normalization must be 'unit_area'"

def validate_sample(sample: Dict[str, Any], expected_bands: List[str]) -> None:
    """Validate a single sample's spectral features."""
    assert "sample_id" in sample, "Missing 'sample_id' in sample"
    assert isinstance(sample["sample_id"], str), "'sample_id' must be a string"
    
    assert "frequencies" in sample, "Missing 'frequencies' in sample"
    assert isinstance(sample["frequencies"], list), "'frequencies' must be a list"
    assert len(sample["frequencies"]) > 0, "'frequencies' must not be empty"
    assert all(isinstance(f, (int, float)) for f in sample["frequencies"]), "All frequencies must be numeric"
    
    assert "psd_normalized" in sample, "Missing 'psd_normalized' in sample"
    assert isinstance(sample["psd_normalized"], list), "'psd_normalized' must be a list"
    assert len(sample["psd_normalized"]) == len(sample["frequencies"]), "PSD and frequencies must have same length"
    assert all(p >= 0 for p in sample["psd_normalized"]), "PSD values must be non-negative"
    
    # Check unit area normalization (sum should be ~1.0)
    psd_sum = sum(sample["psd_normalized"])
    assert abs(psd_sum - 1.0) < 1e-6, f"PSD not normalized to unit area: sum={psd_sum}"
    
    assert "band_power" in sample, "Missing 'band_power' in sample"
    assert isinstance(sample["band_power"], dict), "'band_power' must be a dict"
    for band in expected_bands:
        assert band in sample["band_power"], f"Missing band '{band}' in band_power"
        assert isinstance(sample["band_power"][band], (int, float)), f"'{band}' power must be numeric"
        assert sample["band_power"][band] >= 0, f"'{band}' power must be non-negative"
    
    assert "peak_frequency" in sample, "Missing 'peak_frequency' in sample"
    assert isinstance(sample["peak_frequency"], (int, float)), "'peak_frequency' must be numeric"
    assert sample["peak_frequency"] > 0, "'peak_frequency' must be positive"
    
    assert "peak_power" in sample, "Missing 'peak_power' in sample"
    assert isinstance(sample["peak_power"], (int, float)), "'peak_power' must be numeric"
    assert sample["peak_power"] >= 0, "'peak_power' must be non-negative"

def test_spectral_features_file_exists():
    """Verify that the spectral features file exists."""
    project_root = Path(__file__).parent.parent.parent
    spectral_file = project_root / "data" / "processed" / "meg_psd_normalized_features.json"
    assert spectral_file.exists(), f"Spectral features file not found at {spectral_file}"

def test_spectral_features_schema():
    """Verify that the spectral features file conforms to the expected schema."""
    project_root = Path(__file__).parent.parent.parent
    spectral_file = project_root / "data" / "processed" / "meg_psd_normalized_features.json"
    
    try:
        features = load_spectral_features(spectral_file)
    except FileNotFoundError:
        pytest.fail("Spectral features file does not exist. Run T007/T008 preprocessing first.")
    
    # Validate metadata
    assert "metadata" in features, "Missing 'metadata' in spectral features"
    validate_metadata(features["metadata"])
    
    # Validate data
    assert "data" in features, "Missing 'data' in spectral features"
    assert isinstance(features["data"], list), "'data' must be a list"
    assert len(features["data"]) > 0, "'data' must not be empty"
    
    expected_bands = list(FREQ_BANDS.keys())
    for sample in features["data"]:
        validate_sample(sample, expected_bands)

def test_spectral_features_data_types():
    """Verify that all data types in the spectral features are correct."""
    project_root = Path(__file__).parent.parent.parent
    spectral_file = project_root / "data" / "processed" / "meg_psd_normalized_features.json"
    
    try:
        features = load_spectral_features(spectral_file)
    except FileNotFoundError:
        pytest.fail("Spectral features file does not exist. Run T007/T008 preprocessing first.")
    
    # Check metadata types
    metadata = features["metadata"]
    assert isinstance(metadata["seq_len"], int)
    assert isinstance(metadata["n_fft"], int)
    assert isinstance(metadata["sampling_rate"], (int, float))
    assert isinstance(metadata["normalization"], str)
    
    # Check data types
    for sample in features["data"]:
        assert isinstance(sample["sample_id"], str)
        assert isinstance(sample["frequencies"], list)
        assert all(isinstance(f, (int, float)) for f in sample["frequencies"])
        assert isinstance(sample["psd_normalized"], list)
        assert all(isinstance(p, (int, float)) for p in sample["psd_normalized"])
        assert isinstance(sample["band_power"], dict)
        assert all(isinstance(v, (int, float)) for v in sample["band_power"].values())
        assert isinstance(sample["peak_frequency"], (int, float))
        assert isinstance(sample["peak_power"], (int, float))

def test_spectral_features_unit_area_normalization():
    """Verify that all PSDs are normalized to unit area."""
    project_root = Path(__file__).parent.parent.parent
    spectral_file = project_root / "data" / "processed" / "meg_psd_normalized_features.json"
    
    try:
        features = load_spectral_features(spectral_file)
    except FileNotFoundError:
        pytest.fail("Spectral features file does not exist. Run T007/T008 preprocessing first.")
    
    tolerance = 1e-6
    for sample in features["data"]:
        psd_sum = sum(sample["psd_normalized"])
        assert abs(psd_sum - 1.0) < tolerance, \
            f"Sample {sample['sample_id']} PSD sum is {psd_sum}, expected 1.0"

def test_spectral_features_band_power_coverage():
    """Verify that all expected frequency bands are present in band_power."""
    project_root = Path(__file__).parent.parent.parent
    spectral_file = project_root / "data" / "processed" / "meg_psd_normalized_features.json"
    
    try:
        features = load_spectral_features(spectral_file)
    except FileNotFoundError:
        pytest.fail("Spectral features file does not exist. Run T007/T008 preprocessing first.")
    
    expected_bands = set(FREQ_BANDS.keys())
    for sample in features["data"]:
        actual_bands = set(sample["band_power"].keys())
        missing_bands = expected_bands - actual_bands
        assert len(missing_bands) == 0, \
            f"Sample {sample['sample_id']} missing bands: {missing_bands}"

def test_spectral_features_peak_detection():
    """Verify that peak frequency and power are correctly identified."""
    project_root = Path(__file__).parent.parent.parent
    spectral_file = project_root / "data" / "processed" / "meg_psd_normalized_features.json"
    
    try:
        features = load_spectral_features(spectral_file)
    except FileNotFoundError:
        pytest.fail("Spectral features file does not exist. Run T007/T008 preprocessing first.")
    
    for sample in features["data"]:
        frequencies = np.array(sample["frequencies"])
        psd = np.array(sample["psd_normalized"])
        
        # Verify peak frequency is within the frequency range
        assert frequencies.min() <= sample["peak_frequency"] <= frequencies.max(), \
            f"Peak frequency {sample['peak_frequency']} out of range [{frequencies.min()}, {frequencies.max()}]"
        
        # Verify peak power matches the maximum PSD value
        expected_peak_power = psd.max()
        assert abs(sample["peak_power"] - expected_peak_power) < 1e-10, \
            f"Peak power mismatch: {sample['peak_power']} vs {expected_peak_power}"