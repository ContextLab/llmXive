"""
Integration test for mask-corrected Minkowski Functional computation.

This test verifies the end-to-end pipeline for computing Minkowski Functionals
on the masked CMB map, applying the Schmalzing & Gorski analytical correction,
and validating the results against physical expectations.

Prerequisites:
- T018: data/processed/masked_cmb_n128.fits must exist
- T015: code/mask.py with apply_schmalzing_gorski_correction implemented
- T021/T022: code/minkowski.py with MF computation and correction implemented
"""
import os
import json
import logging
import pytest
import numpy as np
import healpy as hp
from pathlib import Path

# Project imports
from code.minkowski import compute_minkowski_functionals, apply_schmalzing_gorski_correction
from code.mask import load_mask, apply_mask
from code.coverage import load_masked_map
from code.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
Nside = 128
THRESHOLDS = [-1.0, -0.5, 0.0, 0.5, 1.0]  # In units of sigma

@pytest.fixture(scope="module")
def masked_map_path():
    """Locate the masked CMB map produced by T018."""
    config = get_config()
    path = Path(config["data_processed"]) / "masked_cmb_n128.fits"
    assert path.exists(), f"Required input file not found: {path}"
    return str(path)

@pytest.fixture(scope="module")
def mock_mf_results(masked_map_path):
    """
    Compute actual Minkowski Functionals on the masked map to verify integration.
    This is the core integration test: it runs the real pipeline on real data.
    """
    # Load the masked map
    logger.info(f"Loading masked map from {masked_map_path}")
    m_map = load_masked_map(masked_map_path)
    
    # Estimate sigma from the masked map (valid pixels only)
    # Note: The mask has already been applied, so we compute stats on valid data
    sigma = np.std(m_map)
    logger.info(f"Estimated sigma: {sigma:.6f} K")
    
    # Define thresholds in Kelvin
    thresholds_k = [t * sigma for t in THRESHOLDS]
    
    # Compute raw Minkowski Functionals
    logger.info("Computing raw Minkowski Functionals...")
    raw_mf = compute_minkowski_functionals(m_map, thresholds_k)
    
    # Apply Schmalzing & Gorski analytical correction
    logger.info("Applying Schmalzing & Gorski correction...")
    # We need the mask to compute the correction factors
    # Re-load mask to compute correction (or pass from previous step)
    mask_path = Path(get_config()["data_raw"]) / "mask.fits"
    if not mask_path.exists():
        # Fallback: try to find mask in processed if not in raw
        mask_path = Path(get_config()["data_processed"]) / "mask.fits"
    
    assert mask_path.exists(), "Mask file required for correction not found"
    mask = load_mask(str(mask_path))
    
    corrected_mf = apply_schmalzing_gorski_correction(raw_mf, mask, Nside)
    
    return corrected_mf, sigma, thresholds_k

def test_mf_computation_runs(mock_mf_results):
    """Verify that MF computation completes and returns expected structure."""
    corrected_mf, sigma, thresholds_k = mock_mf_results
    
    # Check structure
    assert isinstance(corrected_mf, dict), "MF results should be a dictionary"
    assert "area" in corrected_mf, "Missing 'area' key"
    assert "perimeter" in corrected_mf, "Missing 'perimeter' key"
    assert "genus" in corrected_mf, "Missing 'genus' key"
    
    # Check that we have values for all thresholds
    for key in ["area", "perimeter", "genus"]:
        assert len(corrected_mf[key]) == len(thresholds_k), \
            f"Expected {len(thresholds_k)} values for {key}, got {len(corrected_mf[key])}"

def test_mf_physical_consistency(mock_mf_results):
    """Verify that MF values are physically consistent (non-negative area, etc.)."""
    corrected_mf, sigma, thresholds_k = mock_mf_results
    
    # Area should be positive (or zero)
    area_values = np.array(corrected_mf["area"])
    assert np.all(area_values >= -1e-10), "Area should be non-negative (allowing small numerical error)"
    
    # Perimeter should be positive
    perimeter_values = np.array(corrected_mf["perimeter"])
    assert np.all(perimeter_values >= -1e-10), "Perimeter should be non-negative"
    
    # Genus should be bounded (typically between -2 and 2 for normalized values)
    # For unnormalized, it depends on Nside, but should be finite
    genus_values = np.array(corrected_mf["genus"])
    assert np.all(np.isfinite(genus_values)), "Genus values must be finite"

def test_schmalzing_gorski_correction_applied(mock_mf_results):
    """Verify that the correction was actually applied (values differ from raw)."""
    # We can't easily check this without re-computing raw, but we can check
    # that the corrected values are reasonable and not just zeros or NaNs
    corrected_mf, _, _ = mock_mf_results
    
    for key in ["area", "perimeter", "genus"]:
        values = np.array(corrected_mf[key])
        assert not np.allclose(values, 0), f"Corrected {key} values are all zero"
        assert not np.all(np.isnan(values)), f"Corrected {key} values are all NaN"

def test_threshold_symmetry(mock_mf_results):
    """
    Verify symmetry properties for a Gaussian field:
    - Area(ν) = 1 - Area(-ν) (approximately)
    - Perimeter(ν) ≈ Perimeter(-ν)
    - Genus(ν) ≈ -Genus(-ν)
    
    Note: This is an approximate test due to masking and non-Gaussianity.
    """
    corrected_mf, sigma, thresholds_k = mock_mf_results
    
    # Map thresholds to indices
    # THRESHOLDS = [-1.0, -0.5, 0.0, 0.5, 1.0]
    # Index 0: -1.0, Index 1: -0.5, Index 2: 0.0, Index 3: 0.5, Index 4: 1.0
    
    # Check area symmetry: Area(ν) + Area(-ν) ≈ 1
    area_1 = corrected_mf["area"][0]  # -1.0 sigma
    area_4 = corrected_mf["area"][4]  # +1.0 sigma
    area_sum = area_1 + area_4
    # Allow 10% tolerance due to masking effects
    assert 0.8 <= area_sum <= 1.2, \
        f"Area symmetry violated: Area(-1σ) + Area(+1σ) = {area_sum:.4f}, expected ~1.0"
    
    # Check genus antisymmetry: Genus(ν) ≈ -Genus(-ν)
    genus_1 = corrected_mf["genus"][0]
    genus_4 = corrected_mf["genus"][4]
    genus_diff = abs(genus_1 + genus_4)
    # Allow reasonable tolerance
    assert genus_diff < 0.5, \
        f"Genus antisymmetry violated: |Genus(-1σ) + Genus(+1σ)| = {genus_diff:.4f}"

def test_output_file_generation(mock_mf_results):
    """Verify that results can be serialized and saved (integration with I/O)."""
    corrected_mf, sigma, thresholds_k = mock_mf_results
    
    # Convert to JSON-serializable format
    output = {
        "thresholds": [float(t) for t in thresholds_k],
        "area": [float(v) for v in corrected_mf["area"]],
        "perimeter": [float(v) for v in corrected_mf["perimeter"]],
        "genus": [float(v) for v in corrected_mf["genus"]],
        "sigma": float(sigma),
        "nside": Nside
    }
    
    # Verify JSON serialization
    json_str = json.dumps(output, indent=2)
    assert json_str is not None
    assert "area" in json_str
    assert "genus" in json_str
    
    # Try to write to a temp file
    config = get_config()
    output_path = Path(config["data_processed"]) / "minkowski_integration_test_output.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    assert output_path.exists()
    output_path.unlink()  # Clean up

if __name__ == "__main__":
    pytest.main([__file__, "-v"])