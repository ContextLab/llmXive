"""
Final Report Aggregation with Data Lineage.

Aggregates all JSON artifacts from data/processed/ into a single
data/processed/final_analysis_report.json. Includes a data_lineage section
tracing every metric back to its source file and the specific task ID.

Depends on: T035
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "final_analysis_report.json"

# Mapping of artifacts to their generating Task IDs
ARTIFACT_LINEAGE = {
    "sample_pool_validation.json": "T013b",
    "power_analysis_report.json": "T020",
    "sample_size_validation.json": "T020b",
    "permanova_pairwise_matrix.json": "T045",
    "diversity_metrics.json": "T024",
    "modularity_delta.json": "T031",
    "network_sensitivity_report.json": "T030b",
    "correlation_cv_results.json": "T034",
    "correlation_results.json": "T034",
    "correlation_vif_flags.json": "T046",
    "network_analysis.json": "T035",
    "exclusion_log.json": "T015b",
    "robustness_verification_report.json": "T014b",
    "audit_trail.json": "T043"
}

def load_json_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, otherwise return None."""
    if not filepath.exists():
        logger.warning(f"Artifact not found: {filepath.name}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {filepath.name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {filepath.name}: {e}")
        return None

def aggregate_reports() -> Dict[str, Any]:
    """Aggregate all processed JSON artifacts into a final report."""
    logger.info("Starting Final Report Aggregation (Task T047)...")
    
    report = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generator_task_id": "T047",
            "description": "Aggregated analysis report with data lineage",
            "project_id": "PROJ-280-investigating-microbial-community-succes"
        },
        "data_lineage": [],
        "aggregated_data": {}
    }

    missing_artifacts = []
    
    for filename, task_id in ARTIFACT_LINEAGE.items():
        filepath = PROCESSED_DIR / filename
        data = load_json_file(filepath)
        
        lineage_entry = {
            "artifact_name": filename,
            "source_file": str(filepath),
            "generating_task_id": task_id,
            "status": "present" if data is not None else "missing",
            "record_count": len(data) if isinstance(data, dict) and "samples" in data else 1
        }
        
        if data is not None:
            # Flatten structure slightly for easier consumption
            report["aggregated_data"][filename] = data
        else:
            missing_artifacts.append(filename)
            lineage_entry["error"] = "File not found or invalid JSON"
        
        report["data_lineage"].append(lineage_entry)

    # Summary section
    report["summary"] = {
        "total_artifacts_tracked": len(ARTIFACT_LINEAGE),
        "artifacts_present": len(ARTIFACT_LINEAGE) - len(missing_artifacts),
        "artifacts_missing": len(missing_artifacts),
        "missing_files": missing_artifacts
    }

    if missing_artifacts:
        logger.warning(f"Missing {len(missing_artifacts)} artifacts. Report generated with gaps.")
        logger.warning(f"Missing: {', '.join(missing_artifacts)}")
    else:
        logger.info("All tracked artifacts successfully aggregated.")

    return report

def main():
    """Entry point for the final report generation."""
    if not PROCESSED_DIR.exists():
        logger.error(f"CRITICAL: Processed data directory not found: {PROCESSED_DIR}")
        sys.exit(1)

    try:
        report = aggregate_reports()
        
        # Ensure output directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Final report successfully written to: {OUTPUT_FILE}")
        logger.info(f"Data lineage section contains {len(report['data_lineage'])} entries.")
        
    except Exception as e:
        logger.critical(f"Failed to generate final report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()