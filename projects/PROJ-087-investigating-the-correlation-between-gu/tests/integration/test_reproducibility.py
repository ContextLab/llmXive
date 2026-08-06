"""
Integration tests for reproducibility (SC-005).

This test suite verifies that the full pipeline produces deterministic outputs
across multiple runs by comparing SHA-256 hashes of key artifacts.

Artifacts checked:
- data/processed/cleaned_microbiome_sleep.csv
- All files in data/processed/plots/
"""
import os
import shutil
import subprocess
import hashlib
import tempfile
from pathlib import Path
import pytest
from src.utils.hashing import compute_sha256


# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
PLOTS_DIR = DATA_PROCESSED / "plots"
CLEANED_CSV = DATA_PROCESSED / "cleaned_microbiome_sleep.csv"
CORRELATION_CSV = DATA_PROCESSED / "correlation_results.csv"

# Scripts to run (entry points)
INGESTION_SCRIPT = PROJECT_ROOT / "code" / "src" / "ingestion.py"
DIVERSITY_SCRIPT = PROJECT_ROOT / "code" / "src" / "diversity.py"
CORRELATION_SCRIPT = PROJECT_ROOT / "code" / "src" / "correlation.py"
VIZ_SCRIPT = PROJECT_ROOT / "code" / "src" / "viz.py"
REPORT_SCRIPT = PROJECT_ROOT / "code" / "src" / "report.py"

# Backup paths
BACKUP_DIR = PROJECT_ROOT / "data" / "processed" / ".backup_reproducibility"


def setup_module(module):
    """Ensure backup directory exists."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def teardown_module(module):
    """Clean up backup directory after all tests in this module."""
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)


def run_pipeline():
    """
    Execute the full pipeline: Ingestion -> Diversity -> Correlation -> Viz -> Report.
    Raises subprocess.CalledProcessError if any step fails.
    """
    scripts = [
        ("ingestion", INGESTION_SCRIPT),
        ("diversity", DIVERSITY_SCRIPT),
        ("correlation", CORRELATION_SCRIPT),
        ("viz", VIZ_SCRIPT),
        ("report", REPORT_SCRIPT),
    ]
    
    for name, script in scripts:
        if not script.exists():
            pytest.skip(f"Script not found: {script}. Skipping reproducibility test.")
        
        # Run script
        result = subprocess.run(
            ["python", str(script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"Pipeline step '{name}' failed with exit code {result.returncode}.\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )


def get_artifact_hashes():
    """
    Compute SHA-256 hashes for all critical artifacts.
    Returns a dict mapping relative path to hash.
    """
    hashes = {}
    
    # Check cleaned CSV
    if CLEANED_CSV.exists():
        hashes[str(CLEANED_CSV.relative_to(PROJECT_ROOT))] = compute_sha256(str(CLEANED_CSV))
    else:
        raise FileNotFoundError(f"Cleaned CSV not found: {CLEANED_CSV}")
    
    # Check correlation CSV
    if CORRELATION_CSV.exists():
        hashes[str(CORRELATION_CSV.relative_to(PROJECT_ROOT))] = compute_sha256(str(CORRELATION_CSV))
    else:
        # Correlation might not exist if no significant associations, but we still check
        # If it doesn't exist, we assume the pipeline handled it gracefully
        pass

    # Check all plots
    if PLOTS_DIR.exists():
        for plot_file in PLOTS_DIR.glob("*"):
            if plot_file.is_file():
                rel_path = str(plot_file.relative_to(PROJECT_ROOT))
                hashes[rel_path] = compute_sha256(str(plot_file))
    else:
        # Plots dir might be empty or not exist if no significant correlations
        # We'll treat an empty/missing plots dir as valid if it's consistent
        pass
        
    return hashes


def save_current_artifacts():
    """Save current artifacts to backup directory for comparison."""
    artifacts_to_backup = [CLEANED_CSV, CORRELATION_CSV]
    
    if PLOTS_DIR.exists():
        for plot_file in PLOTS_DIR.glob("*"):
            if plot_file.is_file():
                dest = BACKUP_DIR / plot_file.name
                shutil.copy2(plot_file, dest)
    
    for artifact in artifacts_to_backup:
        if artifact.exists():
            dest = BACKUP_DIR / artifact.name
            shutil.copy2(artifact, dest)


def restore_artifacts():
    """Restore artifacts from backup (for manual inspection if needed, not strictly used in assert flow)."""
    # Not strictly needed for the test logic as we compare hashes directly, 
    # but useful for debugging if hashes differ.
    pass


@pytest.mark.reproducibility
def test_pipeline_reproducibility():
    """
    Run the full pipeline twice and assert that SHA-256 hashes of all output artifacts match.
    This verifies SC-005: Reproducibility.
    """
    # --- Run 1 ---
    try:
        run_pipeline()
    except FileNotFoundError as e:
        pytest.skip(f"Required input data or script missing: {e}")
    except RuntimeError as e:
        pytest.fail(f"Pipeline run 1 failed: {e}")
    
    # Capture hashes from Run 1
    try:
        hashes_run1 = get_artifact_hashes()
    except FileNotFoundError as e:
        pytest.fail(f"Artifact missing after run 1: {e}")
    
    # Save Run 1 artifacts to backup for reference (optional, for debugging)
    save_current_artifacts()
    
    # --- Cleanup for Run 2 ---
    # Remove outputs to force regeneration
    files_to_remove = [CLEANED_CSV, CORRELATION_CSV]
    if PLOTS_DIR.exists():
        for f in PLOTS_DIR.iterdir():
            if f.is_file():
                f.unlink()
    
    for f in files_to_remove:
        if f.exists():
            f.unlink()
    
    # --- Run 2 ---
    try:
        run_pipeline()
    except RuntimeError as e:
        pytest.fail(f"Pipeline run 2 failed: {e}")
    
    # Capture hashes from Run 2
    try:
        hashes_run2 = get_artifact_hashes()
    except FileNotFoundError as e:
        pytest.fail(f"Artifact missing after run 2: {e}")
    
    # --- Comparison ---
    # Check that the set of files is identical
    if set(hashes_run1.keys()) != set(hashes_run2.keys()):
        missing_in_run2 = set(hashes_run1.keys()) - set(hashes_run2.keys())
        extra_in_run2 = set(hashes_run2.keys()) - set(hashes_run1.keys())
        pytest.fail(
            f"Artifact sets differ.\n"
            f"Missing in run 2: {missing_in_run2}\n"
            f"Extra in run 2: {extra_in_run2}"
        )
    
    # Check that hashes match for each file
    mismatches = []
    for file_path, hash_run1 in hashes_run1.items():
        hash_run2 = hashes_run2.get(file_path)
        if hash_run1 != hash_run2:
            mismatches.append((file_path, hash_run1, hash_run2))
    
    if mismatches:
        error_msg = "Reproducibility check failed. Hash mismatches:\n"
        for file_path, h1, h2 in mismatches:
            error_msg += f"  {file_path}\n    Run 1: {h1}\n    Run 2: {h2}\n"
        pytest.fail(error_msg)
    
    # If we reach here, all hashes match
    assert True, "Pipeline is reproducible: All artifact hashes match between runs."
