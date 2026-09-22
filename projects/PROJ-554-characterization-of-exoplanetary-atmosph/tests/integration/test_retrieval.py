"""
Integration test for retrieval on sample spectrum (T017).

This test verifies that the retrieval pipeline can process a single spectrum
file and produce valid output according to the retrieval schema.

It depends on T012 (metadata.csv) and T018c (retrieval schema contract).
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
import numpy as np
import pandas as pd

# Import from existing API surface
from retrieval import (
    run_single_spectrum_retrieval,
    detect_low_snr_spectrum,
    calculate_mdc,
    derive_upper_limit,
    configure_petitradtrans_cpu_optimized,
    get_petitradtrans_config,
)
from config import get_config
from utils import RetrievalError, CensoredDataError


@pytest.fixture
def temp_spectrum_file(tmp_path: Path):
    """Create a temporary spectrum file for testing."""
    # Create a minimal synthetic spectrum file for testing purposes only.
    # This is allowed because it is strictly for testing the retrieval
    # pipeline logic, not for research results.
    spectrum_data = {
        "wavelength": np.linspace(1.0, 5.0, 50),
        "transmission": 0.95 + 0.05 * np.random.random(50),
        "error": 0.01 * np.ones(50),
    }
    spectrum_file = tmp_path / "test_spectrum.csv"
    df = pd.DataFrame(spectrum_data)
    df.to_csv(spectrum_file, index=False)
    return str(spectrum_file)


@pytest.fixture
def retrieval_config():
    """Get retrieval configuration."""
    return configure_petitradtrans_cpu_optimized()


def test_retrieval_single_spectrum_valid(temp_spectrum_file: str, retrieval_config: Dict[str, Any]):
    """Test that retrieval runs on a valid spectrum file."""
    result = run_single_spectrum_retrieval(temp_spectrum_file, retrieval_config)

    # Verify result structure
    assert isinstance(result, dict)
    assert "water_mixing_ratio" in result
    assert "uncertainty" in result
    assert "is_upper_limit" in result
    assert "convergence_status" in result
    assert "planet_name" in result

    # Verify types
    assert isinstance(result["water_mixing_ratio"], (int, float))
    assert isinstance(result["uncertainty"], (int, float))
    assert isinstance(result["is_upper_limit"], bool)
    assert isinstance(result["convergence_status"], str)

    # Verify logical consistency
    if result["is_upper_limit"]:
        # If it's an upper limit, the value should be negative (log scale)
        assert result["water_mixing_ratio"] < 0.0


def test_retrieval_handles_low_snr(temp_path: Path, retrieval_config: Dict[str, Any]):
    """Test that low SNR spectra are handled as upper limits."""
    # Create a low SNR spectrum
    spectrum_data = {
        "wavelength": np.linspace(1.0, 5.0, 50),
        "transmission": 0.95 + 0.5 * np.random.random(50),  # High noise
        "error": 0.1 * np.ones(50),  # High error
    }
    spectrum_file = temp_path / "low_snr_spectrum.csv"
    df = pd.DataFrame(spectrum_data)
    df.to_csv(spectrum_file, index=False)

    # Detect low SNR
    is_low_snr, snr_value = detect_low_snr_spectrum(str(spectrum_file))
    assert is_low_snr, "Should detect low SNR spectrum"
    assert snr_value < 5.0, "SNR should be below threshold"

    # Run retrieval - should handle gracefully
    result = run_single_spectrum_retrieval(str(spectrum_file), retrieval_config)
    assert result is not None
    assert "water_mixing_ratio" in result


def test_retrieval_mdc_calculation(temp_spectrum_file: str):
    """Test that MDC is calculated correctly."""
    mdc = calculate_mdc(temp_spectrum_file)
    assert isinstance(mdc, float)
    assert mdc > 0.0, "MDC should be positive"


def test_retrieval_upper_limit_derivation(temp_spectrum_file: str):
    """Test that upper limits are derived correctly for low SNR."""
    # Simulate a case where retrieval fails or SNR is too low
    upper_limit = derive_upper_limit(temp_spectrum_file, snr=2.0)
    assert isinstance(upper_limit, float)
    assert upper_limit < 0.0, "Upper limit should be negative in log scale"


def test_retrieval_config_cpu_optimized(retrieval_config: Dict[str, Any]):
    """Test that retrieval config is CPU-optimized."""
    assert retrieval_config.get("threads", 1) == 1
    assert retrieval_config.get("max_memory_gb", 6) <= 6


def test_retrieval_schema_compliance(temp_spectrum_file: str, retrieval_config: Dict[str, Any]):
    """Test that retrieval output complies with the schema contract (T018c)."""
    result = run_single_spectrum_retrieval(temp_spectrum_file, retrieval_config)

    # Schema from contracts/retrieval.schema.yaml (T018c)
    required_fields = [
        "planet_name",
        "water_mixing_ratio",
        "uncertainty",
        "is_upper_limit",
        "convergence_status",
    ]

    for field in required_fields:
        assert field in result, f"Missing required field: {field}"

    # Type checks per schema
    assert isinstance(result["water_mixing_ratio"], (int, float))
    assert isinstance(result["uncertainty"], (int, float))
    assert isinstance(result["is_upper_limit"], bool)
    assert isinstance(result["convergence_status"], str)
    assert result["convergence_status"] in ["converged", "failed", "upper_limit"]


def test_retrieval_error_handling(temp_path: Path, retrieval_config: Dict[str, Any]):
    """Test that retrieval handles invalid input gracefully."""
    # Create an invalid spectrum file
    invalid_file = temp_path / "invalid_spectrum.csv"
    invalid_file.write_text("invalid,data\n1,2,3")  # Malformed

    try:
        result = run_single_spectrum_retrieval(str(invalid_file), retrieval_config)
        # If it returns, it should be a failure result
        assert result is not None
        assert result.get("convergence_status") in ["failed", "upper_limit"]
    except Exception as e:
        # Expected to raise an error for invalid input
        assert isinstance(e, (RetrievalError, CensoredDataError, ValueError))


def test_retrieval_integration_with_metadata(temp_path: Path, retrieval_config: Dict[str, Any]):
    """Test retrieval integration with metadata (T012)."""
    # Create a mock metadata.csv
    metadata_data = {
        "planet_name": ["HD_209458_b"],
        "temperature": [1300.0],
        "metallicity": [0.0],
        "snr": [15.0],
        "resolution": [50.0],
        "planet_category": ["Hot Jupiter"],
        "instrument": ["HST"],
        "wavelength_range": ["1.0-5.0"],
    }
    metadata_file = temp_path / "metadata.csv"
    pd.DataFrame(metadata_data).to_csv(metadata_file, index=False)

    # Create a corresponding spectrum file
    spectrum_data = {
        "wavelength": np.linspace(1.0, 5.0, 50),
        "transmission": 0.95 + 0.05 * np.random.random(50),
        "error": 0.01 * np.ones(50),
    }
    spectrum_file = temp_path / "HD_209458_b_spectrum.csv"
    pd.DataFrame(spectrum_data).to_csv(spectrum_file, index=False)

    # Run retrieval
    result = run_single_spectrum_retrieval(str(spectrum_file), retrieval_config)

    # Verify result
    assert result is not None
    assert result["planet_name"] == "HD_209458_b"
    assert "water_mixing_ratio" in result
    assert "uncertainty" in result