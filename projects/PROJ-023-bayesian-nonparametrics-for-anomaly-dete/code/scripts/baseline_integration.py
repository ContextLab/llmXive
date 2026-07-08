"""
Integration script for baseline anomaly detection methods.

This script orchestrates the execution of all baseline methods (Shewhart, CUSUM, VAE)
using the shared data loader and anomaly injection pipeline from User Story 1.
It ensures consistent data preprocessing, runs each baseline independently, and
aggregates results for comparison.

Dependencies:
  - T004: code/lib/data_loader.py
  - T006: code/lib/anomaly_injector.py
  - T020: code/scripts/baseline_shewhart.py
  - T021: code/scripts/baseline_cusum.py
  - T022: code/scripts/baseline_vae.py
"""

import os
import sys
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.data_loader import load_time_series
from lib.utils import set_seed, profile_memory_enforcement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define output paths
RESULTS_DIR = project_root / "data" / "results"
PROCESSED_DIR = project_root / "data" / "processed"

# Baseline scripts to execute
BASELINE_SCRIPTS = [
    "baseline_shewhart.py",
    "baseline_cusum.py",
    "baseline_vae.py"
]

def ensure_processed_data_exists(processed_data_path: Path) -> bool:
    """
    Ensure the processed data with injected anomalies exists.
    If not, run the anomaly injection script.
    
    Args:
        processed_data_path: Path to the expected processed data file
        
    Returns:
        True if data exists or was successfully created, False otherwise
    """
    if processed_data_path.exists():
        logger.info(f"Processed data found at {processed_data_path}")
        return True
        
    logger.info(f"Processed data not found at {processed_data_path}. Running anomaly injection...")
    
    injection_script = project_root / "code" / "scripts" / "inject_anomalies.py"
    if not injection_script.exists():
        logger.error(f"Anomaly injection script not found at {injection_script}")
        return False
        
    try:
        result = subprocess.run(
            [sys.executable, str(injection_script)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Anomaly injection failed: {result.stderr}")
            return False
            
        logger.info("Anomaly injection completed successfully")
        return processed_data_path.exists()
        
    except subprocess.TimeoutExpired:
        logger.error("Anomaly injection timed out")
        return False
    except Exception as e:
        logger.error(f"Error running anomaly injection: {str(e)}")
        return False

def run_baseline_script(script_name: str, data_path: Optional[Path] = None) -> bool:
    """
    Execute a single baseline detection script.
    
    Args:
        script_name: Name of the baseline script to run
        data_path: Optional path to specific data file to process
        
    Returns:
        True if script executed successfully, False otherwise
    """
    script_path = project_root / "code" / "scripts" / script_name
    
    if not script_path.exists():
        logger.error(f"Baseline script not found: {script_path}")
        return False
        
    logger.info(f"Running {script_name}...")
    
    cmd = [sys.executable, str(script_path)]
    if data_path:
        cmd.extend(["--input", str(data_path)])
        
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per baseline
        )
        
        if result.returncode != 0:
            logger.error(f"{script_name} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
            
        logger.info(f"{script_name} completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"{script_name} timed out")
        return False
    except Exception as e:
        logger.error(f"Error running {script_name}: {str(e)}")
        return False

def check_output_files(expected_outputs: Dict[str, Path]) -> Dict[str, bool]:
    """
    Verify that all expected output files were created.
    
    Args:
        expected_outputs: Dictionary mapping method names to expected output paths
        
    Returns:
        Dictionary mapping method names to existence status
    """
    results = {}
    for method, path in expected_outputs.items():
        exists = path.exists()
        results[method] = exists
        if exists:
            size = path.stat().st_size
            logger.info(f"{method} output: {path} ({size} bytes)")
        else:
            logger.warning(f"{method} output missing: {path}")
    return results

def main():
    """Main entry point for baseline integration."""
    parser = argparse.ArgumentParser(
        description="Run all baseline anomaly detection methods with shared data pipeline"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--skip-injection",
        action="store_true",
        help="Skip anomaly injection step if data already exists"
    )
    parser.add_argument(
        "--data-file",
        type=str,
        help="Path to specific data file to process (overrides default)"
    )
    
    args = parser.parse_args()
    
    # Set random seed
    set_seed(args.seed)
    logger.info(f"Random seed set to {args.seed}")
    
    # Define data paths
    if args.data_file:
        input_data_path = Path(args.data_file)
        if not input_data_path.exists():
            logger.error(f"Specified data file not found: {input_data_path}")
            sys.exit(1)
    else:
        input_data_path = PROCESSED_DIR / "series_with_anomalies.csv"
    
    # Ensure output directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check or create processed data
    if not args.skip_injection:
        if not ensure_processed_data_exists(input_data_path):
            logger.error("Failed to ensure processed data exists")
            sys.exit(1)
    else:
        if not input_data_path.exists():
            logger.error(f"Processed data not found and --skip-injection specified: {input_data_path}")
            sys.exit(1)
        logger.info(f"Using existing processed data: {input_data_path}")
    
    # Define expected outputs
    expected_outputs = {
        "shewhart": RESULTS_DIR / "shewhart_predictions.csv",
        "cusum": RESULTS_DIR / "cusum_predictions.csv",
        "vae": RESULTS_DIR / "vae_predictions.csv"
    }
    
    # Run each baseline
    success_count = 0
    for script_name in BASELINE_SCRIPTS:
        method_name = script_name.replace("baseline_", "").replace(".py", "")
        if run_baseline_script(script_name, input_data_path):
            success_count += 1
        else:
            logger.error(f"Failed to run {method_name}")
    
    # Verify outputs
    logger.info("\nVerifying output files...")
    output_status = check_output_files(expected_outputs)
    all_present = all(output_status.values())
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("BASELINE INTEGRATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Baselines executed successfully: {success_count}/{len(BASELINE_SCRIPTS)}")
    logger.info(f"All output files present: {all_present}")
    for method, status in output_status.items():
        status_str = "✓" if status else "✗"
        logger.info(f"  {status_str} {method}: {expected_outputs[method].name}")
    logger.info("="*60)
    
    if success_count == len(BASELINE_SCRIPTS) and all_present:
        logger.info("All baselines completed successfully!")
        sys.exit(0)
    else:
        logger.error("Some baselines failed or outputs are missing")
        sys.exit(1)

if __name__ == "__main__":
    main()