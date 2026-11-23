import json
import os
import hashlib
import platform
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import from existing logging utility to ensure consistency
from utils.logging import get_resource_usage

# Ensure output directories exist
DATA_PROCESSED_BEHAVIORAL = Path("data/processed/behavioral")
DATA_PROCESSED_CENTRALITY = Path("data/processed/centrality")
DATA_PROCESSED_REGRESSION = Path("data/processed/regression")
DATA_PROCESSED_VALIDATION = Path("data/processed/validation")
DATA_PROCESSED_LOGS = Path("data/processed/logs")

# Ensure directories exist
DATA_PROCESSED_BEHAVIORAL.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_CENTRALITY.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_REGRESSION.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_VALIDATION.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_LOGS.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


def get_git_commit() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def get_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    if not file_path.exists():
        return "file_not_found"
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        return "error"


def get_directory_checksums(dir_path: Path, extensions: List[str] = None) -> Dict[str, str]:
    """Calculate checksums for all relevant files in a directory."""
    if not dir_path.exists():
        return {}
    checksums = {}
    if extensions is None:
        extensions = [".csv", ".json", ".tsv"]
    
    for ext in extensions:
        for file_path in dir_path.glob(f"**/*{ext}"):
            checksums[str(file_path)] = get_file_checksum(file_path)
    return checksums


def calculate_artifact_checksums() -> Dict[str, Any]:
    """Calculate checksums for all critical pipeline artifacts."""
    checksums = {
        "behavioral": get_directory_checksums(DATA_PROCESSED_BEHAVIORAL),
        "centrality": get_directory_checksums(DATA_PROCESSED_CENTRALITY),
        "regression": get_directory_checksums(DATA_PROCESSED_REGRESSION),
        "validation": get_directory_checksums(DATA_PROCESSED_VALIDATION),
    }
    return checksums


def load_validation_metrics() -> Optional[Dict[str, Any]]:
    """Load validation metrics from permutation and cross-validation results."""
    results = {}
    
    # Load permutation results
    perm_file = DATA_PROCESSED_VALIDATION / "permutation_results.json"
    if perm_file.exists():
        try:
            with open(perm_file, "r") as f:
                results["permutation"] = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load permutation results: {e}")
    
    # Load cross-validation results
    cv_file = DATA_PROCESSED_VALIDATION / "cv_results.json"
    if cv_file.exists():
        try:
            with open(cv_file, "r") as f:
                results["cross_validation"] = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load CV results: {e}")
    
    return results if results else None


def load_cv_metrics() -> Optional[Dict[str, Any]]:
    """Load cross-validation metrics."""
    cv_file = DATA_PROCESSED_VALIDATION / "cv_results.json"
    if cv_file.exists():
        try:
            with open(cv_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load CV metrics: {e}")
    return None


def load_permutation_results() -> Optional[Dict[str, Any]]:
    """Load permutation test results."""
    perm_file = DATA_PROCESSED_VALIDATION / "permutation_results.json"
    if perm_file.exists():
        try:
            with open(perm_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load permutation results: {e}")
    return None


def load_baseline_r2() -> Optional[float]:
    """Load baseline R² from null model residuals if available."""
    # This would typically be calculated during null model fitting
    # For now, return None as a placeholder
    return None


def load_regression_summary() -> Optional[Dict[str, Any]]:
    """Load regression model summary."""
    summary_file = DATA_PROCESSED_REGRESSION / "linear_model_summary.csv"
    if summary_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(summary_file)
            # Convert to dict for JSON serialization
            return df.to_dict(orient='records')
        except Exception as e:
            logger.warning(f"Could not load regression summary: {e}")
    return None


def generate_report() -> Dict[str, Any]:
    """Generate the complete reproducibility report structure."""
    start_time = time.time()
    commit = get_git_commit()
    platform_info = platform.platform()
    python_version = platform.python_version()
    
    # Get resource usage
    resource_usage = get_resource_usage()
    
    # Calculate checksums
    checksums = calculate_artifact_checksums()
    
    # Load validation metrics
    validation_metrics = load_validation_metrics()
    
    # Load regression summary
    regression_summary = load_regression_summary()
    
    # Calculate wall clock time
    wall_clock_time = time.time() - start_time
    
    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "git_commit": commit,
            "platform": platform_info,
            "python_version": python_version,
            "wall_clock_time_seconds": wall_clock_time,
            "ram_usage_mb": resource_usage.get("ram_mb", 0),
            "cpu_percent": resource_usage.get("cpu_percent", 0)
        },
        "pipeline_metrics": {
            "multicollinearity_check": {},  # Will be populated by T027c
            "power_warning": False,  # Will be populated by T004b
            "retention_rate": None,  # Will be populated by T003
            "n_subjects": None  # Will be populated by T004a
        },
        "validation_metrics": validation_metrics or {},
        "regression_summary": regression_summary,
        "artifact_checksums": checksums,
        "status": "incomplete"  # Updated to "complete" when all tasks finish
    }
    
    return report


def save_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Save the reproducibility report to JSON."""
    if output_path is None:
        output_path = Path("data/artifacts/reproducibility_report.json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Saved reproducibility report to {output_path}")
    return output_path


def load_reproducibility_report() -> Optional[Dict[str, Any]]:
    """Load the existing reproducibility report if it exists."""
    report_path = Path("data/artifacts/reproducibility_report.json")
    if report_path.exists():
        try:
            with open(report_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading reproducibility report: {e}")
    return None


def update_reproducibility_report(updates: Dict[str, Any]) -> Path:
    """Update the reproducibility report with new metrics."""
    report = load_reproducibility_report()
    if report is None:
        report = generate_report()
    
    # Deep update the report
    for key, value in updates.items():
        if isinstance(value, dict) and key in report:
            report[key].update(value)
        else:
            report[key] = value
    
    # Update status if all critical metrics are present
    if (report["pipeline_metrics"].get("n_subjects") is not None and
        report["pipeline_metrics"].get("retention_rate") is not None):
        report["status"] = "complete"
    
    return save_report(report)


def run_reproducibility_report() -> Path:
    """Main entry point to generate and save the reproducibility report."""
    logger.info("Generating reproducibility report...")
    report = generate_report()
    return save_report(report)


def main():
    """CLI entry point for metrics utility."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate reproducibility report")
    parser.add_argument("--update", action="store_true", help="Update existing report with new metrics")
    args = parser.parse_args()
    
    if args.update:
        # Load existing report and update with latest metrics
        report = load_reproducibility_report()
        if report:
            # Refresh checksums and resource usage
            report["artifact_checksums"] = calculate_artifact_checksums()
            report["metadata"]["wall_clock_time_seconds"] = time.time() - time.time()  # Reset
            report["metadata"]["ram_usage_mb"] = get_resource_usage().get("ram_mb", 0)
            save_report(report)
        else:
            logger.warning("No existing report found to update.")
    else:
        run_reproducibility_report()


if __name__ == "__main__":
    main()