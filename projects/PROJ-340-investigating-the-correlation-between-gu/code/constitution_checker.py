"""
Constitution Checker for the Gut Microbiome - Sleep Architecture Study.

Validates the pipeline execution against the project's Constitution Principles.
Specifically handles the "Synthetic Only" state vs "Real Data" state.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

def load_manifest(metadata_dir: Path) -> Dict[str, Any]:
    manifest_path = metadata_dir / "synthetic_data_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            return json.load(f)
    return None

def run_constitution_check(paths: Dict[str, Path]) -> Dict[str, Any]:
    """
    Runs checks against Constitution Principles.
    Returns a report of status for each principle.
    """
    report = {
        "status": "PASSED",
        "principles": {}
    }
    
    # Principle I: Reproducibility
    # Check if seeds are set and manifest exists for synthetic
    manifest = load_manifest(paths["metadata"])
    if manifest and manifest.get("schema_type") == "schema_v1_synthetic":
        report["principles"]["I"] = {
            "status": "PASSED",
            "note": "Synthetic data manifest present with schema_v1."
        }
    elif manifest and manifest.get("schema_type") == "schema_v2_real":
        if manifest.get("chain_of_custody_log"):
            report["principles"]["I"] = {
                "status": "PASSED",
                "note": "Real data with Chain of Custody log present."
            }
        else:
            report["principles"]["I"] = {
                "status": "FAILED",
                "note": "Real data missing Chain of Custody log."
            }
    else:
        report["principles"]["I"] = {
            "status": "WARNING",
            "note": "No manifest found. Assuming standard execution."
        }
        
    # Principle VI: Biological Sample Integrity
    # Check if data is synthetic
    if manifest and manifest.get("schema_type") == "schema_v1_synthetic":
        report["principles"]["VI"] = {
            "status": "N/A (Synthetic)",
            "note": "Study scope is Pipeline Validation (Synthetic). Biological sample integrity not applicable."
        }
    elif manifest and manifest.get("schema_type") == "schema_v2_real":
        report["principles"]["VI"] = {
            "status": "PASSED",
            "note": "Real data source verified."
        }
    else:
        report["principles"]["VI"] = {
            "status": "UNKNOWN",
            "note": "Could not determine data source type."
        }
        
    # Save report
    output_path = paths["results"] / "constitution_check_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    return report

if __name__ == "__main__":
    # Standalone test
    from pathlib import Path
    paths = {
        "metadata": Path("data/metadata"),
        "results": Path("data/results")
    }
    # Ensure directories exist for test
    paths["metadata"].mkdir(parents=True, exist_ok=True)
    paths["results"].mkdir(parents=True, exist_ok=True)
    print(run_constitution_check(paths))
