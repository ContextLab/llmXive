"""
Integration test for the full data pipeline.
Verifies that the pipeline produces non-empty outputs when run on sample data.
"""
import pytest
import json
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_project_root
from data.download import download_bulk_configs
from data.gb_builder import build_gb_supercell
from data.descriptors import run_descriptor_computation
from data.simulate_energy import run_simulation

def test_full_pipeline_execution(project_root, data_paths):
    """
    Execute the full pipeline on a minimal sample.
    Note: This test assumes T013 (download) has been run and data exists,
    or mocks the download step to use local fallback.
    """
    # This is a skeleton integration test.
    # In a real scenario, we would:
    # 1. Call download_bulk_configs (or ensure data exists)
    # 2. Call build_gb_supercell
    # 3. Call run_descriptor_computation
    # 4. Call run_simulation
    # 5. Verify output files exist and are non-empty

    # For T009 scaffolding, we verify the structure exists.
    assert project_root.exists()
    assert data_paths["processed"].exists()
    assert data_paths["results"].exists()

    # Verify that if data files exist, they can be loaded
    descriptors_path = data_paths["processed"] / "descriptors.csv"
    if descriptors_path.exists():
        import pandas as pd
        df = pd.read_csv(descriptors_path)
        assert len(df) > 0, "Descriptors file exists but is empty"

def test_pipeline_artifacts_exist(project_root):
    """Verify that the expected artifact directories exist."""
    assert (project_root / "data" / "raw").exists()
    assert (project_root / "data" / "processed").exists()
    assert (project_root / "results").exists()
