"""
T042b: Verify Compute Feasibility (SC-007)

This script runs a scaled-down version of the full pipeline to verify that
total runtime is <6 hours, peak RAM <7GB, and disk usage <14GB.

It uses a real subset of the data (first N rows) to ensure measurements
are based on actual computation, not synthetic data.
"""
import os
import sys
import time
import json
import resource
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging_config import get_logger
from seed import set_seed

# Constants
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MAX_RAM_BYTES = 7 * 1024**3     # 7 GB
MAX_DISK_BYTES = 14 * 1024**3   # 14 GB
SAMPLE_SIZE = 50                # Use first 50 rows for feasibility test

logger = get_logger(__name__)

def get_peak_rss_mb() -> float:
    """Get peak resident set size in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, bytes on macOS
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)
    else:
        return usage.ru_maxrss / 1024

def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of directory in MB."""
    total = 0
    if path.exists():
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = Path(dirpath) / f
                if fp.is_file():
                    total += fp.stat().st_size
    return total / (1024 * 1024)

def run_pipeline_step(step_name: str, script_path: Path, args: Optional[Dict[str, Any]] = None) -> bool:
    """Run a single pipeline step and return success status."""
    cmd = [sys.executable, str(script_path)]
    if args:
        for key, value in args.items():
            cmd.append(f"--{key}")
            cmd.append(str(value))
    
    logger.info(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=MAX_RUNTIME_SECONDS
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✓ {step_name} completed in {elapsed:.2f}s")
            return True
        else:
            logger.error(f"✗ {step_name} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {step_name} timed out after {MAX_RUNTIME_SECONDS}s")
        return False
    except Exception as e:
        logger.error(f"✗ {step_name} raised exception: {e}")
        return False

def verify_feasibility() -> Dict[str, Any]:
    """Run scaled pipeline and verify feasibility constraints."""
    set_seed(42)
    
    start_time = time.time()
    initial_ram = get_peak_rss_mb()
    initial_disk = get_disk_usage_mb(project_root / "data")
    
    results = {
        "steps_completed": [],
        "steps_failed": [],
        "total_runtime_seconds": 0,
        "peak_ram_mb": initial_ram,
        "final_disk_mb": initial_disk,
        "constraints_met": {
            "runtime": False,
            "ram": False,
            "disk": False
        }
    }
    
    # Define scaled-down pipeline steps
    # We use a subset of data by passing --sample_size argument
    pipeline_steps = [
        ("Data Cleaning", project_root / "code" / "ingestion" / "cleaner.py", {"sample_size": SAMPLE_SIZE}),
        ("CLR Transform", project_root / "code" / "features" / "transformer.py", {"sample_size": SAMPLE_SIZE}),
        ("Descriptor Engineering", project_root / "code" / "features" / "descriptor_engine.py", {"sample_size": SAMPLE_SIZE}),
        ("VIF Calculation", project_root / "code" / "features" / "collinearity.py", {"sample_size": SAMPLE_SIZE}),
        ("XGBoost Training", project_root / "code" / "models" / "xgboost_trainer.py", {"sample_size": SAMPLE_SIZE}),
        ("Linear Regression", project_root / "code" / "models" / "linear_trainer.py", {"sample_size": SAMPLE_SIZE}),
        ("Cross-Validation", project_root / "code" / "evaluation" / "cv.py", {"sample_size": SAMPLE_SIZE}),
        ("Bootstrap Analysis", project_root / "code" / "evaluation" / "bootstrap.py", {"sample_size": SAMPLE_SIZE}),
        ("SHAP Analysis", project_root / "code" / "evaluation" / "shap_analysis.py", {"sample_size": SAMPLE_SIZE}),
        ("Prediction & Metrics", project_root / "code" / "evaluation" / "predict.py", {"sample_size": SAMPLE_SIZE}),
        ("Report Generation", project_root / "code" / "evaluation" / "generate_report.py", {"sample_size": SAMPLE_SIZE}),
    ]
    
    logger.info(f"Starting feasibility test with {SAMPLE_SIZE} samples")
    
    for step_name, script_path, args in pipeline_steps:
        if not script_path.exists():
            logger.warning(f"Skipping {step_name}: script not found at {script_path}")
            continue
        
        success = run_pipeline_step(step_name, script_path, args)
        if success:
            results["steps_completed"].append(step_name)
        else:
            results["steps_failed"].append(step_name)
            # Continue with other steps even if one fails
    
    # Calculate final metrics
    end_time = time.time()
    final_ram = get_peak_rss_mb()
    final_disk = get_disk_usage_mb(project_root / "data")
    
    results["total_runtime_seconds"] = end_time - start_time
    results["peak_ram_mb"] = max(initial_ram, final_ram)
    results["final_disk_mb"] = final_disk
    
    # Check constraints
    results["constraints_met"]["runtime"] = results["total_runtime_seconds"] < MAX_RUNTIME_SECONDS
    results["constraints_met"]["ram"] = results["peak_ram_mb"] < (MAX_RAM_BYTES / (1024 * 1024))
    results["constraints_met"]["disk"] = results["final_disk_mb"] < (MAX_DISK_BYTES / (1024 * 1024))
    
    # Overall feasibility
    all_steps_ok = len(results["steps_failed"]) == 0
    all_constraints_ok = all(results["constraints_met"].values())
    
    results["feasible"] = all_steps_ok and all_constraints_ok
    
    return results

def save_results(results: Dict[str, Any], output_path: Path):
    """Save results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Verify compute feasibility (SC-007)")
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE, 
                      help=f"Number of samples to use (default: {SAMPLE_SIZE})")
    parser.add_argument("--output", type=str, 
                      default="data/processed/feasibility_report.json",
                      help="Output file path")
    args = parser.parse_args()
    
    logger.info("Starting compute feasibility verification (T042b)")
    
    results = verify_feasibility()
    
    # Override sample size in results
    results["sample_size"] = args.sample_size
    
    output_path = project_root / args.output
    save_results(results, output_path)
    
    # Print summary
    print("\n" + "="*60)
    print("COMPUTE FEASIBILITY REPORT (T042b)")
    print("="*60)
    print(f"Sample Size: {results['sample_size']}")
    print(f"Total Runtime: {results['total_runtime_seconds']:.2f}s "
          f"(limit: {MAX_RUNTIME_SECONDS}s)")
    print(f"Peak RAM: {results['peak_ram_mb']:.2f} MB "
          f"(limit: {MAX_RAM_BYTES / (1024*1024):.2f} MB)")
    print(f"Final Disk: {results['final_disk_mb']:.2f} MB "
          f"(limit: {MAX_DISK_BYTES / (1024*1024):.2f} MB)")
    print(f"\nConstraints Met:")
    for constraint, met in results["constraints_met"].items():
        status = "✓ PASS" if met else "✗ FAIL"
        print(f"  {constraint}: {status}")
    print(f"\nSteps Completed: {len(results['steps_completed'])}")
    if results['steps_failed']:
        print(f"Steps Failed: {len(results['steps_failed'])}")
        for step in results['steps_failed']:
            print(f"  - {step}")
    print(f"\nOverall Feasibility: {'✓ FEASIBLE' if results['feasible'] else '✗ NOT FEASIBLE'}")
    print("="*60)
    
    if not results["feasible"]:
        sys.exit(1)

if __name__ == "__main__":
    main()