"""
Integration tests for reproducibility verification (SC-005).

This module implements T035: Run the full pipeline twice, compute SHA-256 hashes
of the cleaned dataset and all plot artifacts, and assert the hashes match between runs.

Prerequisites:
- T009: Hashing utility (src/utils/hashing.py)
- T016: Cleaned dataset generation (data/processed/cleaned_microbiome_sleep.csv)
- T030: Plot artifacts generation (data/processed/plots/*.png)
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any

import pytest

# Import project utilities and pipeline stages
from src.utils.hashing import compute_sha256
from src.ingestion import run_ingestion_pipeline
from src.diversity import main as run_diversity
from src.correlation import main as run_correlation
from src.viz import save_all_plot_artifacts
from src.report_final import run_final_report_generation
from src.config import load_config


class TestReproducibility:
    """
    Tests to verify that the pipeline produces deterministic outputs.
    
    SC-005 Requirement:
    - Run the full pipeline twice.
    - Compute SHA-256 hashes of:
      - data/processed/cleaned_microbiome_sleep.csv
      - All files in data/processed/plots/
    - Assert hashes match between runs.
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """
        Set up a temporary environment to run the pipeline twice in isolation.
        
        This ensures we don't interfere with the main project's data directory
        during testing, and allows us to capture outputs for comparison.
        """
        self.tmp_base = tmp_path
        self.run1_dir = self.tmp_base / "run1"
        self.run2_dir = self.tmp_base / "run2"
        self.run1_dir.mkdir()
        self.run2_dir.mkdir()

        # Create subdirectories matching project structure
        (self.run1_dir / "data" / "processed" / "plots").mkdir(parents=True)
        (self.run2_dir / "data" / "processed" / "plots").mkdir(parents=True)

        # Save original environment variables to restore later
        self.original_env = os.environ.copy()

        yield

        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def _configure_env_for_run(self, run_dir: Path, run_id: int):
        """
        Configure environment variables for a specific pipeline run.
        
        Args:
            run_dir: The directory where this run will write outputs.
            run_id: Identifier for this run (1 or 2).
        """
        os.environ["DATA_DIR"] = str(run_dir / "data")
        os.environ["PROCESSED_DIR"] = str(run_dir / "data" / "processed")
        os.environ["PLOTS_DIR"] = str(run_dir / "data" / "processed" / "plots")
        os.environ["RANDOM_SEED"] = "42"  # Fixed seed for reproducibility
        os.environ["LOG_LEVEL"] = "WARNING"  # Suppress logs during test

    def _run_pipeline_stage(self, run_dir: Path, stage_name: str):
        """
        Execute a specific stage of the pipeline.
        
        Args:
            run_dir: Base directory for the run.
            stage_name: Name of the stage ('ingestion', 'diversity', 'correlation', 'viz', 'report').
        
        Raises:
            RuntimeError: If the stage fails to execute.
        """
        try:
            if stage_name == "ingestion":
                # Run ingestion pipeline to generate cleaned data
                run_ingestion_pipeline()
            elif stage_name == "diversity":
                # Run diversity analysis
                run_diversity()
            elif stage_name == "correlation":
                # Run correlation analysis
                run_correlation()
            elif stage_name == "viz":
                # Generate visualizations
                save_all_plot_artifacts()
            elif stage_name == "report":
                # Generate final report
                run_final_report_generation()
        except Exception as e:
            raise RuntimeError(f"Pipeline stage '{stage_name}' failed in {run_dir}: {e}")

    def _compute_artifact_hashes(self, run_dir: Path) -> Dict[str, str]:
        """
        Compute SHA-256 hashes for all critical artifacts in a run.
        
        Args:
            run_dir: The directory containing the run's outputs.
        
        Returns:
            Dictionary mapping artifact relative paths to their SHA-256 hashes.
        """
        hashes = {}
        processed_dir = run_dir / "data" / "processed"

        # Hash the cleaned dataset
        cleaned_file = processed_dir / "cleaned_microbiome_sleep.csv"
        if cleaned_file.exists():
            hashes["cleaned_microbiome_sleep.csv"] = compute_sha256(str(cleaned_file))
        else:
            # If the file doesn't exist, record as missing
            hashes["cleaned_microbiome_sleep.csv"] = "MISSING"

        # Hash all plot files
        plots_dir = processed_dir / "plots"
        if plots_dir.exists():
            for plot_file in sorted(plots_dir.glob("*.png")):
                rel_path = f"plots/{plot_file.name}"
                hashes[rel_path] = compute_sha256(str(plot_file))

        # Hash the correlation results
        corr_file = processed_dir / "correlation_results.csv"
        if corr_file.exists():
            hashes["correlation_results.csv"] = compute_sha256(str(corr_file))
        else:
            hashes["correlation_results.csv"] = "MISSING"

        return hashes

    def test_reproducibility_full_pipeline(self):
        """
        Verify that running the full pipeline twice produces identical artifacts.
        
        This test:
        1. Runs the full pipeline in run1_dir.
        2. Runs the full pipeline in run2_dir.
        3. Computes SHA-256 hashes of all critical artifacts in both runs.
        4. Asserts that the hashes match exactly.
        
        If the pipeline is non-deterministic (e.g., due to random seeds not being set,
        or floating-point inconsistencies), this test will fail.
        """
        # --- Run 1 ---
        self._configure_env_for_run(self.run1_dir, 1)
        try:
            self._run_pipeline_stage(self.run1_dir, "ingestion")
            self._run_pipeline_stage(self.run1_dir, "diversity")
            self._run_pipeline_stage(self.run1_dir, "correlation")
            self._run_pipeline_stage(self.run1_dir, "viz")
            self._run_pipeline_stage(self.run1_dir, "report")
        except RuntimeError as e:
            pytest.fail(f"Run 1 failed: {e}")

        hashes_run1 = self._compute_artifact_hashes(self.run1_dir)

        # --- Run 2 ---
        self._configure_env_for_run(self.run2_dir, 2)
        try:
            self._run_pipeline_stage(self.run2_dir, "ingestion")
            self._run_pipeline_stage(self.run2_dir, "diversity")
            self._run_pipeline_stage(self.run2_dir, "correlation")
            self._run_pipeline_stage(self.run2_dir, "viz")
            self._run_pipeline_stage(self.run2_dir, "report")
        except RuntimeError as e:
            pytest.fail(f"Run 2 failed: {e}")

        hashes_run2 = self._compute_artifact_hashes(self.run2_dir)

        # --- Compare Hashes ---
        assert set(hashes_run1.keys()) == set(hashes_run2.keys()), (
            f"Artifact sets differ. Run 1: {set(hashes_run1.keys())}, "
            f"Run 2: {set(hashes_run2.keys())}"
        )

        mismatches = []
        for artifact in hashes_run1:
            h1 = hashes_run1[artifact]
            h2 = hashes_run2[artifact]

            if h1 != h2:
                mismatches.append({
                    "artifact": artifact,
                    "run1_hash": h1,
                    "run2_hash": h2
                })

        if mismatches:
            error_msg = "Reproducibility check failed. Mismatches found:\n"
            for m in mismatches:
                error_msg += (
                    f"  - {m['artifact']}:\n"
                    f"      Run 1: {m['run1_hash']}\n"
                    f"      Run 2: {m['run2_hash']}\n"
                )
            pytest.fail(error_msg)

        # If we reach here, all hashes match
        assert len(mismatches) == 0, "Reproducibility check failed with no mismatches recorded."

    def test_reproducibility_cleaned_data_only(self):
        """
        Verify that the cleaned dataset is identical across two runs.
        
        This is a focused test for T016 reproducibility, ensuring that the
        ingestion and filtering logic is deterministic.
        """
        # Run 1
        self._configure_env_for_run(self.run1_dir, 1)
        try:
            self._run_pipeline_stage(self.run1_dir, "ingestion")
        except RuntimeError as e:
            pytest.fail(f"Run 1 ingestion failed: {e}")

        cleaned_file_1 = self.run1_dir / "data" / "processed" / "cleaned_microbiome_sleep.csv"
        assert cleaned_file_1.exists(), "Cleaned dataset not found after Run 1."
        hash_1 = compute_sha256(str(cleaned_file_1))

        # Run 2
        self._configure_env_for_run(self.run2_dir, 2)
        try:
            self._run_pipeline_stage(self.run2_dir, "ingestion")
        except RuntimeError as e:
            pytest.fail(f"Run 2 ingestion failed: {e}")

        cleaned_file_2 = self.run2_dir / "data" / "processed" / "cleaned_microbiome_sleep.csv"
        assert cleaned_file_2.exists(), "Cleaned dataset not found after Run 2."
        hash_2 = compute_sha256(str(cleaned_file_2))

        assert hash_1 == hash_2, (
            f"Cleaned dataset is not reproducible.\n"
            f"Run 1 hash: {hash_1}\n"
            f"Run 2 hash: {hash_2}"
        )

    def test_reproducibility_plot_artifacts(self):
        """
        Verify that all plot artifacts are identical across two runs.
        
        This test ensures that the visualization logic (T027, T028, T030)
        produces deterministic images, given the same input data and random seed.
        """
        # Run 1
        self._configure_env_for_run(self.run1_dir, 1)
        try:
            self._run_pipeline_stage(self.run1_dir, "ingestion")
            self._run_pipeline_stage(self.run1_dir, "diversity")
            self._run_pipeline_stage(self.run1_dir, "correlation")
            self._run_pipeline_stage(self.run1_dir, "viz")
        except RuntimeError as e:
            pytest.fail(f"Run 1 (up to viz) failed: {e}")

        plots_dir_1 = self.run1_dir / "data" / "processed" / "plots"
        plots_1 = {p.name: compute_sha256(str(p)) for p in sorted(plots_dir_1.glob("*.png"))}

        # Run 2
        self._configure_env_for_run(self.run2_dir, 2)
        try:
            self._run_pipeline_stage(self.run2_dir, "ingestion")
            self._run_pipeline_stage(self.run2_dir, "diversity")
            self._run_pipeline_stage(self.run2_dir, "correlation")
            self._run_pipeline_stage(self.run2_dir, "viz")
        except RuntimeError as e:
            pytest.fail(f"Run 2 (up to viz) failed: {e}")

        plots_dir_2 = self.run2_dir / "data" / "processed" / "plots"
        plots_2 = {p.name: compute_sha256(str(p)) for p in sorted(plots_dir_2.glob("*.png"))}

        assert set(plots_1.keys()) == set(plots_2.keys()), (
            f"Plot file sets differ. Run 1: {set(plots_1.keys())}, "
            f"Run 2: {set(plots_2.keys())}"
        )

        mismatches = []
        for plot_name in plots_1:
            if plots_1[plot_name] != plots_2[plot_name]:
                mismatches.append({
                    "plot": plot_name,
                    "run1_hash": plots_1[plot_name],
                    "run2_hash": plots_2[plot_name]
                })

        if mismatches:
            error_msg = "Plot reproducibility check failed. Mismatches:\n"
            for m in mismatches:
                error_msg += (
                    f"  - {m['plot']}:\n"
                    f"      Run 1: {m['run1_hash']}\n"
                    f"      Run 2: {m['run2_hash']}\n"
                )
            pytest.fail(error_msg)

        assert len(mismatches) == 0, "Plot reproducibility check failed with no mismatches recorded."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])