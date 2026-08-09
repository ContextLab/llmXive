"""Integration test for the full data pipeline.

This test verifies that the orchestration logic in `code/main.py` correctly
connects the download, GB builder, descriptor computation, and energy simulation
modules. It expects the pipeline to produce `data/processed/descriptors.csv`
and `data/processed/segregation_energies.csv`.

Note: This test may be skipped in CI if real data access is restricted or if
the download step fails due to missing credentials/whitelist violations,
but it verifies the orchestration logic connects all modules correctly.
"""
import pytest
import sys
import os
from pathlib import Path
import json
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.main import run_pipeline
from code.config import get_project_root, get_data_paths

@pytest.mark.integration
def test_full_pipeline_execution():
    """
    Integration test: Run the full pipeline from download to simulation.
    
    Verifies:
    1. The pipeline orchestration runs without crashing (assuming data is available).
    2. Expected output files are created on disk.
    3. Output files are non-empty.
    """
    root = get_project_root()
    data_paths = get_data_paths()
    
    # Ensure output directories exist
    data_paths['processed'].mkdir(parents=True, exist_ok=True)
    
    # Clean up any previous outputs to ensure we are testing a fresh run
    descriptors_path = data_paths['processed'] / "descriptors.csv"
    energies_path = data_paths['processed'] / "segregation_energies.csv"
    
    if descriptors_path.exists():
        descriptors_path.unlink()
    if energies_path.exists():
        energies_path.unlink()
    
    pipeline_success = False
    
    try:
        # Run the pipeline
        # This will trigger: download -> gb_builder -> descriptors -> simulate_energy
        # The function is expected to return True on success or raise an exception on failure
        run_pipeline()
        pipeline_success = True
        
    except Exception as e:
        error_msg = str(e)
        # If the pipeline fails due to data unavailability (expected in test env without credentials),
        # we check that the error is handled gracefully or skipped appropriately.
        if "DATA_UNAVAILABLE" in error_msg:
            pytest.skip(f"Data unavailable in test environment (expected): {error_msg}")
        elif "Whitelist" in error_msg or "URL" in error_msg:
            pytest.skip(f"URL validation failed (expected in isolated test): {error_msg}")
        else:
            # Re-raise unexpected errors
            raise e
    
    if pipeline_success:
        # Verify expected outputs exist
        assert descriptors_path.exists(), \
            "Descriptors CSV not found after pipeline run"
        
        assert energies_path.exists(), \
            "Segregation energies CSV not found after pipeline run"
        
        # Verify files are non-empty
        assert descriptors_path.stat().st_size > 0, \
            "Descriptors CSV is empty"
        
        assert energies_path.stat().st_size > 0, \
            "Segregation energies CSV is empty"
        
        # Optional: Verify CSV structure (basic header check)
        with open(descriptors_path, 'r') as f:
            header = f.readline().strip()
            assert 'species' in header, "Descriptors CSV missing 'species' column"
            assert 'rdf_peak' in header, "Descriptors CSV missing 'rdf_peak' column"
        
        with open(energies_path, 'r') as f:
            header = f.readline().strip()
            assert 'segregation_energy' in header, "Energies CSV missing 'segregation_energy' column"
