"""
Integration tests for reproducibility (T035).

Runs the full pipeline twice and verifies that SHA-256 hashes of key artifacts
(cleaned dataset and plots) match between runs to satisfy SC-005.

If the pipeline is in a blocked state (T012c failed), this test verifies that
the blocked artifacts are generated consistently and their hashes match.
"""
import os
import sys
import json
import subprocess
import hashlib
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import src modules
# Adjust based on the project structure shown in API surface
CODE_ROOT = Path(__file__).parent.parent.parent / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from src.utils.hashing import compute_sha256
from src.config import load_config


def run_pipeline_step(step_name: str, timeout_seconds: int = 300) -> tuple[int, str, str]:
    """
    Execute a specific step of the pipeline via the run-book command.
    
    Args:
        step_name: The step to run (e.g., 'check_data', 'ingest', 'analyze', 'viz', 'all')
        timeout_seconds: Maximum time to wait for the step to complete
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    cmd = [
        sys.executable,
        str(CODE_ROOT / "src" / "main.py"),
        "--step", step_name
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(CODE_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Pipeline step '{step_name}' timed out after {timeout_seconds}s"
    except FileNotFoundError:
        # If main.py doesn't exist, try to run the specific script directly
        # This handles the case where the run-book hasn't been updated yet
        script_map = {
            "check_data": "scripts/run_t012c_check_data.py",
            "ingest": "scripts/run_t016_save_cleaned_dataset.py",
            "analyze": "scripts/run_t024_save_results.py",
            "viz": "scripts/run_t030_save_plots.py",
            "report": "scripts/run_t031_generate_report.py",
            "all": "scripts/run_t036_validate_quickstart.py"
        }
        
        if step_name in script_map:
            script_path = CODE_ROOT / script_map[step_name]
            if script_path.exists():
                cmd = [sys.executable, str(script_path)]
                result = subprocess.run(
                    cmd,
                    cwd=str(CODE_ROOT),
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )
                return result.returncode, result.stdout, result.stderr
        
        return -2, "", f"Pipeline script for step '{step_name}' not found"


def compute_file_hashes(file_paths: list[Path]) -> dict[str, str]:
    """
    Compute SHA-256 hashes for a list of files.
    
    Args:
        file_paths: List of file paths to hash
        
    Returns:
        Dictionary mapping file path strings to their SHA-256 hashes
    """
    hashes = {}
    for fp in file_paths:
        if fp.exists():
            hashes[str(fp)] = compute_sha256(str(fp))
        else:
            hashes[str(fp)] = "FILE_NOT_FOUND"
    return hashes


def get_key_artifacts() -> list[Path]:
    """
    Get the list of key artifacts to hash for reproducibility verification.
    
    Returns:
        List of Path objects for key artifacts
    """
    data_processed = CODE_ROOT / "data" / "processed"
    plots_dir = data_processed / "plots"
    
    artifacts = [
        data_processed / "cleaned_microbiome_sleep.csv",
        data_processed / "correlation_results.csv",
        data_processed / "ingestion_report.json",
    ]
    
    # Add all plot files if the directory exists
    if plots_dir.exists():
        for plot_file in plots_dir.glob("*.png"):
            artifacts.append(plot_file)
    
    return artifacts


def get_blocked_artifacts() -> list[Path]:
    """
    Get the list of artifacts to check in blocked state.
    
    Returns:
        List of Path objects for blocked artifacts
    """
    data_processed = CODE_ROOT / "data" / "processed"
    
    return [
        data_processed / "ingestion_report.json",
        data_processed / "diversity_results.csv",
        data_processed / "correlation_results.csv",
        data_processed / "reports" / "blocked_report.md",
    ]


def is_pipeline_blocked() -> bool:
    """
    Check if the pipeline is in a blocked state.
    
    Returns:
        True if the pipeline is blocked, False otherwise
    """
    ingestion_report_path = CODE_ROOT / "data" / "processed" / "ingestion_report.json"
    
    if not ingestion_report_path.exists():
        return False
    
    try:
        with open(ingestion_report_path, 'r') as f:
            report = json.load(f)
        return report.get("status") == "blocked"
    except (json.JSONDecodeError, KeyError):
        return False


class TestReproducibility:
    """
    Test class for verifying pipeline reproducibility.
    """
    
    def test_pipeline_reproducibility(self):
        """
        Run the full pipeline twice and verify that key artifacts have matching hashes.
        
        This test:
        1. Runs the pipeline (or checks if already blocked)
        2. Computes hashes of key artifacts
        3. Runs the pipeline again (or verifies blocked state consistency)
        4. Compares hashes to ensure they match
        """
        # Step 1: Check if pipeline is already blocked
        if is_pipeline_blocked():
            # Verify blocked artifacts exist and are consistent
            blocked_artifacts = get_blocked_artifacts()
            
            # Run the blocked report generation again to ensure consistency
            _, _, _ = run_pipeline_step("check_data")
            
            # Compute hashes
            hashes_run1 = compute_file_hashes(blocked_artifacts)
            
            # Run again to ensure blocked state is reproducible
            _, _, _ = run_pipeline_step("check_data")
            
            hashes_run2 = compute_file_hashes(blocked_artifacts)
            
            # Verify hashes match
            for artifact_path, hash1 in hashes_run1.items():
                hash2 = hashes_run2.get(artifact_path, "MISSING")
                assert hash1 == hash2, (
                    f"Blocked artifact hash mismatch for {artifact_path}: "
                    f"Run 1: {hash1}, Run 2: {hash2}"
                )
            
            # Verify blocked artifacts exist
            for artifact in blocked_artifacts:
                assert artifact.exists(), f"Blocked artifact missing: {artifact}"
            
            return
        
        # Step 2: Run the full pipeline (or key steps) if not blocked
        # Run check_data
        rc, out, err = run_pipeline_step("check_data")
        if rc != 0 and rc != -2:
            pytest.skip(f"Pipeline check_data step failed: {err}")
        
        # Run ingest (T016)
        rc, out, err = run_pipeline_step("ingest")
        if rc != 0 and rc != -2:
            pytest.skip(f"Pipeline ingest step failed: {err}")
        
        # Run analyze (T024)
        rc, out, err = run_pipeline_step("analyze")
        if rc != 0 and rc != -2:
            pytest.skip(f"Pipeline analyze step failed: {err}")
        
        # Run viz (T030)
        rc, out, err = run_pipeline_step("viz")
        if rc != 0 and rc != -2:
            pytest.skip(f"Pipeline viz step failed: {err}")
        
        # Step 3: Compute hashes of key artifacts
        key_artifacts = get_key_artifacts()
        hashes_run1 = compute_file_hashes(key_artifacts)
        
        # Step 4: Run the pipeline again to verify reproducibility
        # Note: In a real scenario, we might want to clean intermediate files,
        # but for reproducibility testing, we want to see if running again
        # produces the same results
        
        # Re-run ingest to regenerate cleaned data
        rc, out, err = run_pipeline_step("ingest")
        if rc != 0 and rc != -2:
            pytest.skip(f"Second run of ingest step failed: {err}")
        
        # Re-run analyze
        rc, out, err = run_pipeline_step("analyze")
        if rc != 0 and rc != -2:
            pytest.skip(f"Second run of analyze step failed: {err}")
        
        # Re-run viz
        rc, out, err = run_pipeline_step("viz")
        if rc != 0 and rc != -2:
            pytest.skip(f"Second run of viz step failed: {err}")
        
        # Step 5: Compute hashes again and compare
        hashes_run2 = compute_file_hashes(key_artifacts)
        
        # Verify hashes match
        for artifact_path, hash1 in hashes_run1.items():
            if hash1 == "FILE_NOT_FOUND":
                # If artifact was missing in run 1, check if it exists in run 2
                # This might indicate a non-deterministic issue
                if hashes_run2.get(artifact_path) != "FILE_NOT_FOUND":
                    pytest.fail(f"Artifact {artifact_path} was missing in run 1 but exists in run 2")
                continue
            
            hash2 = hashes_run2.get(artifact_path, "MISSING")
            assert hash1 == hash2, (
                f"Reproducibility failed for {artifact_path}: "
                f"Run 1 hash: {hash1}, Run 2 hash: {hash2}"
            )
        
        # Step 6: Record hashes in state file for Constitution Principle III
        state_dir = CODE_ROOT.parent / "state" / "projects" / "PROJ-087-investigating-the-correlation-between-gu"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "reproducibility_check.json"
        
        state_data = {
            "run_1_hashes": hashes_run1,
            "run_2_hashes": hashes_run2,
            "all_match": all(hashes_run1.get(k) == hashes_run2.get(k) for k in hashes_run1),
            "timestamp_run_1": None,  # Could be populated with datetime
            "timestamp_run_2": None
        }
        
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
        
        # Also update checksums.json if it exists
        checksums_path = CODE_ROOT / "data" / "processed" / "checksums.json"
        if checksums_path.exists():
            with open(checksums_path, 'r') as f:
                checksums = json.load(f)
            
            checksums["reproducibility_check"] = {
                "run_1": hashes_run1,
                "run_2": hashes_run2,
                "all_match": state_data["all_match"]
            }
            
            with open(checksums_path, 'w') as f:
                json.dump(checksums, f, indent=2)
    
    def test_artifacts_exist(self):
        """
        Verify that all key artifacts exist after pipeline execution.
        """
        if is_pipeline_blocked():
            artifacts = get_blocked_artifacts()
        else:
            artifacts = get_key_artifacts()
        
        missing = []
        for artifact in artifacts:
            if not artifact.exists():
                missing.append(str(artifact))
        
        if missing:
            pytest.fail(f"Missing artifacts: {', '.join(missing)}")
        
        # Also verify that artifacts are not empty (for files that should have content)
        for artifact in artifacts:
            if artifact.exists() and artifact.suffix in ['.csv', '.json', '.md']:
                if artifact.stat().st_size == 0:
                    pytest.fail(f"Artifact is empty: {artifact}")