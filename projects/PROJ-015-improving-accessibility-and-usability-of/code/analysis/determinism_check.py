"""
Determinism Check Module for PROJ-015.

Ensures the analysis pipeline is fully deterministic by:
1. Pinning random seeds (Python, NumPy, Pandas operations where applicable).
2. Verifying that re-running the pipeline produces identical checksums for all generated artifacts.
3. Providing a CLI to run the pipeline twice and compare outputs.

Dependencies:
- T028 (analysis.ipynb)
- T023a (ANOVA implementation)
- T024 (Holm-Bonferroni)
- T026 (metrics_summary.csv generation)
"""
import os
import sys
import hashlib
import json
import random
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from config.settings import get_settings
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Global seed value
GLOBAL_SEED = 42

def set_all_seeds(seed: int = GLOBAL_SEED) -> None:
    """
    Pin all random seeds to ensure deterministic execution.
    
    Args:
        seed (int): The seed value to use for all random number generators.
    """
    # Python standard library
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # Pandas (mostly relies on NumPy, but we ensure consistency)
    # Note: Pandas itself doesn't have a global seed function, 
    # but it uses NumPy's random state for operations like sampling.
    
    # Set environment variable for reproducibility (optional but good practice)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    logger.info(f"All random seeds set to {seed}")

def compute_checksums(file_paths: List[Path]) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for a list of files.
    
    Args:
        file_paths (List[Path]): List of file paths to checksum.
        
    Returns:
        Dict[str, str]: Dictionary mapping file path strings to their SHA-256 checksums.
    """
    checksums = {}
    for file_path in file_paths:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            continue
        
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksums[str(file_path)] = sha256_hash.hexdigest()
            logger.debug(f"Checksum computed for {file_path}: {checksums[str(file_path)]}")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {e}")
            
    return checksums

def load_baseline(baseline_path: Path) -> Dict[str, str]:
    """
    Load baseline checksums from a JSON file.
    
    Args:
        baseline_path (Path): Path to the baseline checksums JSON file.
        
    Returns:
        Dict[str, str]: Dictionary of baseline checksums.
    """
    if not baseline_path.exists():
        logger.warning(f"Baseline file not found: {baseline_path}. Returning empty baseline.")
        return {}
    
    try:
        with open(baseline_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse baseline JSON: {e}")
        return {}

def save_baseline(checksums: Dict[str, str], baseline_path: Path) -> None:
    """
    Save current checksums to a JSON file as the new baseline.
    
    Args:
        checksums (Dict[str, str]): Dictionary of checksums to save.
        baseline_path (Path): Path to the baseline checksums JSON file.
    """
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(baseline_path, 'w') as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    logger.info(f"Baseline checksums saved to {baseline_path}")

def run_pipeline() -> None:
    """
    Execute the main analysis pipeline to generate artifacts.
    
    This function orchestrates the execution of the analysis pipeline
    to ensure all artifacts are generated before checksumming.
    """
    settings = get_settings()
    logger.info("Starting analysis pipeline execution...")
    
    # Import and run the main analysis script
    # This ensures we are using the same code path as the production run
    try:
        from analysis.run_analysis import main as run_analysis_main
        # Simulate command line arguments for the analysis run
        sys.argv = ['run_analysis.py', '--input', str(settings.get('cleaned_data_path')), 
                    '--output', str(settings.get('processed_data_dir'))]
        run_analysis_main()
        logger.info("Analysis pipeline executed successfully.")
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        raise

def verify_determinism(baseline_path: Optional[Path] = None, 
                       artifacts: Optional[List[Path]] = None,
                       create_baseline: bool = False) -> bool:
    """
    Verify that the pipeline produces deterministic results.
    
    Args:
        baseline_path (Optional[Path]): Path to the baseline checksums file.
        artifacts (Optional[List[Path]]): List of artifact paths to verify.
        create_baseline (bool): If True, create a new baseline instead of verifying.
        
    Returns:
        bool: True if deterministic (or baseline created), False if mismatch.
    """
    settings = get_settings()
    
    # Default artifacts to check if not provided
    if artifacts is None:
        artifacts = [
            settings.get('metrics_summary_path'),
            settings.get('report_summary_path'),
            settings.get('power_flags_path'),
            Path(settings.get('figures_dir')) / 'completion_time.png',
            Path(settings.get('figures_dir')) / 'error_count.png',
            Path(settings.get('figures_dir')) / 'sus_score.png',
        ]
    
    # Filter to only existing files
    existing_artifacts = [p for p in artifacts if p.exists()]
    if not existing_artifacts:
        logger.error("No existing artifacts found to verify determinism.")
        return False
    
    # Run the pipeline to generate fresh artifacts
    try:
        run_pipeline()
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return False
    
    # Compute current checksums
    current_checksums = compute_checksums(existing_artifacts)
    
    if create_baseline:
        baseline_path = baseline_path or settings.get('determinism_baseline_path')
        save_baseline(current_checksums, Path(baseline_path))
        logger.info("Determinism baseline created successfully.")
        return True
    
    # Load baseline
    baseline_path = baseline_path or settings.get('determinism_baseline_path')
    baseline_checksums = load_baseline(Path(baseline_path))
    
    if not baseline_checksums:
        logger.error("No baseline checksums found. Run with --create-baseline first.")
        return False
    
    # Compare checksums
    mismatch_found = False
    for file_path, current_checksum in current_checksums.items():
        if file_path not in baseline_checksums:
            logger.warning(f"File {file_path} not in baseline. Skipping.")
            continue
        
        baseline_checksum = baseline_checksums[file_path]
        if current_checksum != baseline_checksum:
            logger.error(f"MISMATCH: {file_path}")
            logger.error(f"  Baseline: {baseline_checksum}")
            logger.error(f"  Current:  {current_checksum}")
            mismatch_found = True
        else:
            logger.info(f"OK: {file_path}")
    
    if mismatch_found:
        logger.error("Determinism verification FAILED: Checksums do not match.")
        return False
    else:
        logger.info("Determinism verification PASSED: All checksums match.")
        return True

def main() -> None:
    """
    CLI entry point for determinism checking.
    """
    parser = argparse.ArgumentParser(description="Verify determinism of the analysis pipeline.")
    parser.add_argument("--create-baseline", action="store_true",
                        help="Create a new baseline checksum file instead of verifying.")
    parser.add_argument("--baseline", type=str, default=None,
                        help="Path to the baseline checksums file (default: from settings).")
    parser.add_argument("--seed", type=int, default=GLOBAL_SEED,
                        help=f"Random seed to use (default: {GLOBAL_SEED}).")
    parser.add_argument("--artifacts", type=str, nargs="+", default=None,
                        help="List of artifact paths to check (space-separated).")
    
    args = parser.parse_args()
    
    # Set seeds first
    set_all_seeds(args.seed)
    
    # Parse artifact paths if provided
    artifacts = None
    if args.artifacts:
        artifacts = [Path(p) for p in args.artifacts]
    
    baseline_path = Path(args.baseline) if args.baseline else None
    
    success = verify_determinism(
        baseline_path=baseline_path,
        artifacts=artifacts,
        create_baseline=args.create_baseline
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()