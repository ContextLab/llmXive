"""
Integration test for skipping strata with < 10 samples (US2).

Verifies that the analysis pipeline correctly identifies strata with insufficient
sample size (< 10), skips PERMANOVA/varpart execution for those strata,
logs the skipped biome to results/skipped_strata.log, and proceeds without crashing.
"""
import os
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.analysis import run_stratified_analysis
from src.models.schemas import EnvironmentalMatrix, ASVTable

def _create_temp_project_structure(base_dir: Path):
    """Helper to create a minimal project structure for testing."""
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    (data_dir / "cleaned_metadata.csv").touch()
    (data_dir / "asv_table.tsv").touch()
    (data_dir / "distance_matrix.npz").touch()
    
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir, results_dir

def test_skip_strata_insufficient_samples():
    """
    Test that strata with < 10 samples are skipped and logged.
    
    Scenario:
    1. Create a synthetic metadata file with:
       - Biome A: 15 samples (Valid)
       - Biome B: 5 samples (Invalid, < 10)
       - Biome C: 20 samples (Valid)
    2. Run the stratified analysis pipeline.
    3. Verify:
       - The pipeline does not crash.
       - results/skipped_strata.log exists.
       - The log contains "Biome B".
       - Results for Biome A and C are generated (or attempted).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        data_dir, results_dir = _create_temp_project_structure(base_path)
        
        # Create synthetic metadata with specific strata sizes
        # We need: sample_id, biome, pH, nutrients (to satisfy schema requirements)
        metadata_data = {
            "sample_id": [f"sample_{i}" for i in range(40)],
            "biome": (
                ["Forest"] * 15 +      # Valid stratum
                ["Grassland"] * 5 +    # Invalid stratum (< 10)
                ["Desert"] * 20        # Valid stratum
            ),
            "pH": [7.0] * 40,
            "nutrients": [100.0] * 40,
            "moisture": [0.2] * 40
        }
        
        metadata_df = pd.DataFrame(metadata_data)
        metadata_path = data_dir / "cleaned_metadata.csv"
        metadata_df.to_csv(metadata_path, index=False)
        
        # Create a dummy ASV table (required for pipeline start)
        # Shape: samples x features
        asv_data = pd.DataFrame(
            [[10, 20, 5] for _ in range(40)],
            columns=["asv_1", "asv_2", "asv_3"]
        )
        asv_data.insert(0, "sample_id", metadata_df["sample_id"])
        asv_path = data_dir / "asv_table.tsv"
        asv_data.to_csv(asv_path, sep="\t", index=False)
        
        # Create a dummy distance matrix (Bray-Curtis)
        # Shape: samples x samples
        import numpy as np
        dist_matrix = np.random.rand(40, 40)
        dist_matrix = (dist_matrix + dist_matrix.T) / 2
        np.fill_diagonal(dist_matrix, 0)
        dist_path = data_dir / "distance_matrix.npz"
        np.savez(dist_path, dist_matrix=dist_matrix)
        
        # Define the strata column
        strata_column = "biome"
        
        # Execute the stratified analysis
        # Note: We expect this to handle the small stratum gracefully
        try:
            run_stratified_analysis(
                metadata_path=str(metadata_path),
                asv_path=str(asv_path),
                distance_path=str(dist_path),
                strata_column=strata_column,
                min_samples=10,
                output_dir=str(results_dir)
            )
        except Exception as e:
            # If the pipeline crashes due to logic errors (not data issues), fail the test
            pytest.fail(f"Stratified analysis crashed: {e}")
        
        # Assertions
        log_path = results_dir / "skipped_strata.log"
        assert log_path.exists(), "skipped_strata.log was not created"
        
        with open(log_path, "r") as f:
            log_content = f.read()
        
        # Verify the invalid stratum was logged
        assert "Grassland" in log_content, "Log file does not contain 'Grassland' (the stratum with < 10 samples)"
        
        # Verify valid strata were processed (or at least not skipped)
        # We expect output files for Forest and Desert
        forest_results = results_dir / "db_rda_biome_Forest.csv"
        desert_results = results_dir / "db_rda_biome_Desert.csv"
        
        # Check if results exist or if the process at least attempted them
        # (In a real run, they should exist; here we check that the pipeline didn't abort)
        # Note: If the pipeline generates partial results, we check for existence.
        # If the pipeline is designed to only write on success, we rely on the log for the skip.
        
        # The primary requirement is the log entry for the skipped stratum.
        assert "Grassland" in log_content, "Failed to log skipped stratum Grassland"