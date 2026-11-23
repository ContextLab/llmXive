import os
import sys
import json
import hashlib
import logging
import time
import configparser
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_config, DatasetPaths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        raise


def load_recorded_checksums(state_path: Path) -> Dict[str, str]:
    """Load recorded checksums from the project state YAML file."""
    import yaml
    try:
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
            return state_data.get('artifact_hashes', {})
    except FileNotFoundError:
        logger.error(f"State file not found: {state_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        raise


def load_pytest_seed(config_path: Path) -> int:
    """
    Extract the random seed from pytest.ini.
    Looks for 'addopts = --random-seed=<int>' pattern.
    """
    if not config_path.exists():
        logger.warning(f"pytest.ini not found at {config_path}, defaulting to 42")
        return 42

    config = configparser.ConfigParser()
    try:
        # ConfigParser needs sections, but pytest.ini is often just key=value pairs or [pytest]
        # We'll read manually to be safe with the specific format
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Look for the specific pattern
        import re
        match = re.search(r'--random-seed=(\d+)', content)
        if match:
            seed = int(match.group(1))
            logger.info(f"Found pinned random seed in pytest.ini: {seed}")
            return seed
        else:
            logger.warning("Could not find --random-seed in pytest.ini, defaulting to 42")
            return 42
    except Exception as e:
        logger.error(f"Error reading pytest.ini: {e}")
        return 42


def verify_artifacts(
    artifacts: Dict[str, str],
    data_dir: Path,
    state_dir: Path,
    project_root: Path
) -> List[Dict[str, Any]]:
    """
    Verify that the current artifacts match the recorded checksums.
    Returns a list of verification results.
    """
    results = []
    
    for relative_path, expected_hash in artifacts.items():
        # Construct full path
        if relative_path.startswith('data/'):
            full_path = project_root / relative_path
        elif relative_path.startswith('state/'):
            full_path = project_root / relative_path
        else:
            # Try data first, then state
            full_path = data_dir / relative_path
            if not full_path.exists():
                full_path = state_dir / relative_path
                if not full_path.exists():
                    full_path = project_root / relative_path

        if not full_path.exists():
            results.append({
                "path": relative_path,
                "status": "fail",
                "reason": "File not found",
                "expected_hash": expected_hash,
                "actual_hash": None
            })
            logger.error(f"Artifact missing: {full_path}")
            continue

        try:
            actual_hash = compute_file_sha256(full_path)
            if actual_hash == expected_hash:
                results.append({
                    "path": relative_path,
                    "status": "pass",
                    "reason": "Hash matches",
                    "expected_hash": expected_hash,
                    "actual_hash": actual_hash
                })
                logger.info(f"Verified: {relative_path}")
            else:
                results.append({
                    "path": relative_path,
                    "status": "fail",
                    "reason": "Hash mismatch",
                    "expected_hash": expected_hash,
                    "actual_hash": actual_hash
                })
                logger.error(f"Hash mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}")
        except Exception as e:
            results.append({
                "path": relative_path,
                "status": "fail",
                "reason": f"Error computing hash: {str(e)}",
                "expected_hash": expected_hash,
                "actual_hash": None
            })
            logger.error(f"Error verifying {relative_path}: {e}")

    return results


def run_full_pipeline_for_repro(
    pipeline_script: Path,
    args: List[str] = None
) -> bool:
    """
    Re-run the pipeline script to regenerate artifacts.
    Returns True if successful, False otherwise.
    """
    import subprocess
    
    if not pipeline_script.exists():
        logger.error(f"Pipeline script not found: {pipeline_script}")
        return False

    cmd = [sys.executable, str(pipeline_script)]
    if args:
        cmd.extend(args)
    
    logger.info(f"Re-running pipeline: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Pipeline failed with code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info("Pipeline re-run completed successfully")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Pipeline re-run timed out")
        return False
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        return False


def generate_report(
    verification_results: List[Dict[str, Any]],
    random_seed: int,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate the reproducibility report JSON.
    """
    mismatches = [r for r in verification_results if r['status'] == 'fail']
    passed = [r for r in verification_results if r['status'] == 'pass']
    
    report = {
        "status": "pass" if len(mismatches) == 0 else "fail",
        "artifacts_checked": len(verification_results),
        "passed_count": len(passed),
        "failed_count": len(mismatches),
        "random_seed": random_seed,
        "mismatches": [
            {
                "path": m['path'],
                "reason": m['reason'],
                "expected": m['expected_hash'],
                "actual": m['actual_hash']
            }
            for m in mismatches
        ],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Reproducibility report written to {output_path}")
    return report


def main():
    """Main entry point for reproducibility verification."""
    config = get_config()
    paths: DatasetPaths = config.paths
    
    # Define paths
    state_file = paths.state_dir / "projects" / "PROJ-139-the-influence-of-emotional-contagion-on-.yaml"
    pytest_config = project_root / "pytest.ini"
    pipeline_script = project_root / "code" / "analysis" / "run_pipeline.py"
    output_report = paths.state_dir / "reproducibility_report.json"
    
    # Load recorded checksums
    logger.info("Loading recorded checksums...")
    recorded_checksums = load_recorded_checksums(state_file)
    
    # Get the random seed from pytest.ini
    logger.info("Loading random seed from pytest.ini...")
    random_seed = load_pytest_seed(pytest_config)
    
    # Re-run the pipeline to regenerate artifacts
    logger.info("Re-running pipeline to regenerate artifacts...")
    pipeline_success = run_full_pipeline_for_repro(pipeline_script, ["--threads"])
    
    if not pipeline_success:
        logger.error("Pipeline re-run failed. Cannot verify reproducibility.")
        # Generate a failure report anyway
        report = generate_report([], random_seed, output_report)
        report["status"] = "fail"
        report["reason"] = "Pipeline re-run failed"
        with open(output_report, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    # Verify artifacts
    logger.info("Verifying artifacts...")
    verification_results = verify_artifacts(
        recorded_checksums,
        paths.data_processed_dir,
        paths.state_dir,
        project_root
    )
    
    # Generate report
    logger.info("Generating reproducibility report...")
    report = generate_report(verification_results, random_seed, output_report)
    
    if report["status"] == "fail":
        logger.error("Reproducibility check FAILED. See mismatches in report.")
        sys.exit(1)
    else:
        logger.info("Reproducibility check PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()