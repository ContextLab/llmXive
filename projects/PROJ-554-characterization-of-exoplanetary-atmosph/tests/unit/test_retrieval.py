import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import from the project modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from retrieval import (
    configure_petitradtrans_cpu_optimized,
    get_petitradtrans_config,
    validate_spectrum_file,
    detect_low_snr_spectrum,
    calculate_mdc,
    derive_upper_limit,
    run_single_spectrum_retrieval,
    save_retrieval_results,
    process_retrieval_results
)
from utils import RetrievalError

@pytest.fixture
def temp_spectrum_dir():
    """Create a temporary directory with mock spectrum files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock spectrum files
        for i in range(3):
            filepath = Path(tmpdir) / f"spectrum_{i}.csv"
            df = pd.DataFrame({
                'wavelength': np.linspace(0.5, 5.0, 100),
                'transit_depth': np.random.rand(100) * 0.01
            })
            df.to_csv(filepath, index=False)
        yield tmpdir

def test_configure_petitradtrans_cpu_optimized():
    """Test CPU optimization configuration."""
    config = configure_petitradtrans_cpu_optimized()
    assert config["threads"] == 1
    assert config["max_memory_gb"] == 6
    assert config["mode"] == "cpu_optimized"

def test_get_petitradtrans_config():
    """Test getting petitRADTRANS configuration."""
    config = get_petitradtrans_config()
    assert "threads" in config
    assert "max_memory_gb" in config

def test_validate_spectrum_file_valid(temp_spectrum_dir):
    """Test validation of valid spectrum file."""
    spectrum_path = Path(temp_spectrum_dir) / "spectrum_0.csv"
    assert validate_spectrum_file(str(spectrum_path)) is True

def test_validate_spectrum_file_invalid():
    """Test validation of invalid spectrum file."""
    with pytest.raises(RetrievalError):
        validate_spectrum_file("nonexistent_file.csv")

def test_detect_low_snr_spectrum():
    """Test low SNR detection."""
    assert detect_low_snr_spectrum(3.0, 100.0) is True
    assert detect_low_snr_spectrum(10.0, 100.0) is False
    assert detect_low_snr_spectrum(5.0, 100.0) is False  # threshold is 5.0

def test_calculate_mdc():
    """Test MDC calculation."""
    mdc = calculate_mdc(10.0, 100.0)
    assert mdc > 0
    assert np.isfinite(mdc)
    
    # Test edge cases
    assert np.isnan(calculate_mdc(0.0, 100.0))
    assert np.isnan(calculate_mdc(10.0, 0.0))

def test_derive_upper_limit():
    """Test upper limit derivation."""
    upper_limit, uncertainty = derive_upper_limit(3.0, 100.0)
    assert upper_limit > 0
    assert uncertainty > 0
    assert upper_limit > uncertainty

def test_save_retrieval_results(temp_spectrum_dir):
    """Test saving retrieval results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results = [
            {
                "planet_name": "test_planet_1",
                "water_mixing_ratio": -4.5,
                "uncertainty": 0.2,
                "is_upper_limit": False,
                "detection_limit": 1e-5,
                "min_detectable_concentration": 3e-6,
                "convergence_status": "converged"
            },
            {
                "planet_name": "test_planet_2",
                "water_mixing_ratio": -3.0,
                "uncertainty": 0.3,
                "is_upper_limit": True,
                "detection_limit": 2e-5,
                "min_detectable_concentration": 7e-6,
                "convergence_status": "upper_limit"
            }
        ]
        
        output_path = Path(tmpdir) / "retrieval_results.csv"
        save_retrieval_results(results, str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert "planet_name" in df.columns
        assert "water_mixing_ratio" in df.columns
        assert "is_upper_limit" in df.columns
        assert df.iloc[0]["planet_name"] == "test_planet_1"
        assert df.iloc[1]["is_upper_limit"] is True

def test_process_retrieval_results(temp_spectrum_dir):
    """Test processing all spectrum files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "results"
        output_path.mkdir()
        
        results = process_retrieval_results(temp_spectrum_dir, str(output_path))
        
        assert len(results) == 3
        assert all("planet_name" in r for r in results)
        assert all("water_mixing_ratio" in r for r in results)
        
        # Verify output file was created
        output_file = output_path / "retrieval_results.csv"
        assert output_file.exists()
        
        df = pd.read_csv(output_file)
        assert len(df) == 3
        assert list(df.columns) == [
            'planet_name', 'water_mixing_ratio', 'uncertainty', 
            'is_upper_limit', 'detection_limit', 'min_detectable_concentration'
        ]
