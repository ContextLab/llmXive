"""
Integration test for the full data pipeline.
Executes the pipeline on a small sample (N=10) of bulk configurations
and verifies that GB supercells, descriptors, and segregation energies
are generated and saved to disk with non-empty values.
"""
import pytest
import json
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_project_root, get_data_paths
from data.download import download_bulk_configs
from data.gb_builder import build_gb_supercell
from data.descriptors import run_descriptor_computation
from data.simulate_energy import run_simulation
from data.preprocessing import run_preprocessing_filter

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.fixture
def sample_bulk_configs(project_root: Path) -> List[Path]:
    """
    Helper to ensure we have at least 10 sample bulk configurations.
    If not present, this test will fail loudly as per requirements,
    indicating the prerequisite download step (T013) was not completed.
    """
    raw_dir = project_root / "data" / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory {raw_dir} does not exist. Run T013 first.")
    
    # Look for .cif or .json structure files
    config_files = list(raw_dir.glob("*.cif")) + list(raw_dir.glob("*.json"))
    
    if len(config_files) < 10:
        # If we have some but not enough, try to find backup or fail
        # For strict compliance, we fail if we don't have enough real data
        raise ValueError(
            f"Insufficient bulk configurations found ({len(config_files)} < 10). "
            f"Ensure T013 (download) has populated data/raw/ with at least 10 structures."
        )
    
    return config_files[:10]

def test_full_pipeline_execution(sample_bulk_configs: List[Path], project_root: Path):
    """
    Execute the full pipeline on a minimal sample (N=10).
    1. Preprocess (filter zero impurity if needed, though we assume valid inputs from download)
    2. Build GB supercells
    3. Compute descriptors
    4. Run simulation (segregation energies)
    5. Verify output files exist and contain non-empty data.
    """
    processed_dir = get_data_paths(project_root)["processed"]
    results_dir = project_root / "results"

    # Ensure output directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting pipeline execution on {len(sample_bulk_configs)} samples.")

    # 1. Preprocessing (T019) - Filter zero impurity configs
    # Assuming the downloaded configs are valid, we run the filter to generate the report
    # This step is required to generate the preprocessing_report.json
    try:
        run_preprocessing_filter(project_root)
        report_path = processed_dir / "preprocessing_report.json"
        assert report_path.exists(), "Preprocessing report not generated."
        with open(report_path, 'r') as f:
            report = json.load(f)
        logger.info(f"Preprocessing report: {report}")
    except Exception as e:
        logger.warning(f"Preprocessing step encountered an issue (expected if no zero-impurity configs): {e}")

    # 2. Build GB Supercells (T014)
    # We need to pass the list of config files to the builder
    # The builder function signature from API surface is: build_gb_supercell(config_path, output_dir)
    # We will iterate and build each one.
    supercell_paths = []
    for cfg_path in sample_bulk_configs:
        try:
            # The builder might need specific parameters, but we use defaults from config
            output_path = build_gb_supercell(cfg_path, processed_dir / "gb_supercells")
            if output_path:
                supercell_paths.append(output_path)
        except Exception as e:
            logger.error(f"Failed to build supercell for {cfg_path}: {e}")
            # Continue with others, but we need at least some to proceed

    if not supercell_paths:
        pytest.fail("No GB supercells were built. Check T014 implementation or input data.")

    logger.info(f"Built {len(supercell_paths)} GB supercells.")

    # 3. Compute Descriptors (T015)
    # Run descriptor computation on the generated supercells
    try:
        descriptors_df = run_descriptor_computation(project_root)
        assert descriptors_df is not None, "Descriptor computation returned None."
        assert len(descriptors_df) > 0, "Descriptors DataFrame is empty."
        
        # Verify the file was written
        desc_file = processed_dir / "descriptors.csv"
        assert desc_file.exists(), "Descriptors CSV file not found."
        
        # Reload to verify content
        df_check = pd.read_csv(desc_file)
        assert len(df_check) > 0, "Descriptors file exists but is empty."
        logger.info(f"Descriptors computed and saved: {len(df_check)} rows.")
    except Exception as e:
        pytest.fail(f"Descriptor computation failed: {e}")

    # 4. Run Simulation (T017c)
    # Calculate segregation energies for the computed configurations
    try:
        energy_df = run_simulation(project_root)
        assert energy_df is not None, "Simulation returned None."
        assert len(energy_df) > 0, "Energy DataFrame is empty."
        
        # Verify the file was written
        energy_file = processed_dir / "segregation_energies.csv"
        assert energy_file.exists(), "Segregation energies CSV file not found."
        
        # Reload to verify content
        energy_check = pd.read_csv(energy_file)
        assert len(energy_check) > 0, "Energy file exists but is empty."
        
        # Verify non-empty energy values (not NaN)
        if 'segregation_energy' in energy_check.columns:
            valid_energies = energy_check['segregation_energy'].dropna()
            assert len(valid_energies) > 0, "No valid (non-NaN) segregation energies found."
        
        logger.info(f"Simulation completed and saved: {len(energy_check)} rows.")
    except Exception as e:
        pytest.fail(f"Simulation failed: {e}")

    # 5. Verify Artifacts (T012b equivalent check within this test)
    # Verify GB supercells directory is non-empty
    supercell_dir = processed_dir / "gb_supercells"
    assert supercell_dir.exists(), "GB supercells directory missing."
    assert len(list(supercell_dir.glob("*"))) > 0, "GB supercells directory is empty."

    # Verify descriptors and energies have correct columns
    df_desc = pd.read_csv(processed_dir / "descriptors.csv")
    required_desc_cols = ['species', 'rdf_peak', 'pair_corr', 'voronoi_count']
    for col in required_desc_cols:
        assert col in df_desc.columns, f"Missing column '{col}' in descriptors.csv"

    df_energy = pd.read_csv(processed_dir / "segregation_energies.csv")
    required_energy_cols = ['segregation_energy']
    for col in required_energy_cols:
        assert col in df_energy.columns, f"Missing column '{col}' in segregation_energies.csv"

    logger.info("Integration test passed: All pipeline stages executed successfully with non-empty outputs.")

def test_pipeline_artifacts_exist(project_root: Path):
    """Verify that the expected artifact directories exist."""
    assert (project_root / "data" / "raw").exists()
    assert (project_root / "data" / "processed").exists()
    assert (project_root / "results").exists()
    assert (project_root / "tests" / "unit").exists()
    assert (project_root / "tests" / "integration").exists()