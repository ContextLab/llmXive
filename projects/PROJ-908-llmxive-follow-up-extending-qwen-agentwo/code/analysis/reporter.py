"""
Final Report Generator: Aggregates all intermediate artifacts into a single report.
"""
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from utils.checksums import compute_file_sha256

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_git_commit_hash() -> str:
    """Get the current git commit hash."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception as e:
        logger.warning(f"Could not get git commit hash: {e}")
        return "unknown"

def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, otherwise return None."""
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")
    return None

def main():
    PROJECT_ROOT = Path(__file__).parent.parent
    processed_dir = PROJECT_ROOT / "data" / "processed"
    output_file = processed_dir / "final_report.json"
    
    logger.info("Generating final report...")
    
    # List of potential intermediate files to aggregate
    intermediate_files = {
        "divergence_report": processed_dir / "divergence_report.json",
        "rule_precision": processed_dir / "rule_precision.json",
        "cot_quality_scores": processed_dir / "cot_quality_scores.json",
        "correlation_result": processed_dir / "correlation_result.json",
        "boundary_conditions": processed_dir / "boundary_conditions.json",
        "rate_metrics": processed_dir / "rate_metrics.json",
        "excluded_metrics": processed_dir / "exclusion_audit.json"
    }
    
    report: Dict[str, Any] = {
        "metadata": {
            "git_commit_hash": get_git_commit_hash(),
            "execution_timestamp": subprocess.check_output(['date', '-Iseconds']).decode('ascii').strip(),
            "dataset_checksums": {}
        },
        "divergence_report": None,
        "excluded_metrics": None,
        "correlation": None,
        "boundaries": None,
        "precision": None,
        "quality": None,
        "rates": None
    }
    
    # Aggregate files
    for key, path in intermediate_files.items():
        data = load_json_file(path)
        if data:
            # Map key to report field
            if key == "divergence_report":
                report["divergence_report"] = data
            elif key == "excluded_metrics":
                report["excluded_metrics"] = data
            elif key == "correlation_result":
                report["correlation"] = data
            elif key == "boundary_conditions":
                report["boundaries"] = data
            elif key == "rule_precision":
                report["precision"] = data
            elif key == "cot_quality_scores":
                report["quality"] = data
            elif key == "rate_metrics":
                report["rates"] = data
            
            # Add checksums for processed files
            report["metadata"]["dataset_checksums"][key] = compute_file_sha256(path)
        else:
            logger.warning(f"Intermediate file missing: {path}")
    
    # Write to temp file then rename for atomicity
    temp_file = output_file.with_suffix('.tmp')
    with open(temp_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    os.rename(temp_file, output_file)
    logger.info(f"Final report generated at {output_file}")

if __name__ == "__main__":
    main()
