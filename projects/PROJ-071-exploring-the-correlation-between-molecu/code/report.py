from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Helper Functions ---

def get_data_path() -> Path:
    return Path(__file__).parent.parent / "data"

def load_gate_status() -> Dict[str, Any]:
    path = get_data_path() / "gate_status.json"
    if not path.exists():
        return {"status": "FAIL"}
    with open(path, "r") as f:
        return json.load(f)

def load_stat_gate_status() -> Dict[str, Any]:
    path = get_data_path() / "stat_gate_status.json"
    if not path.exists():
        return {"status": "FAIL"}
    with open(path, "r") as f:
        return json.load(f)

def calculate_file_hash(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def collect_reproducibility_metadata() -> Dict[str, Any]:
    """Collects versions, hashes, and lineage."""
    data_path = get_data_path()
    
    artifacts = []
    files_to_hash = [
        data_path / "processed" / "merged_drugs.csv",
        data_path / "processed" / "standard_subset.csv",
        data_path / "processed" / "analysis_results.json",
        data_path / "gate_status.json",
        data_path / "stat_gate_status.json"
    ]
    
    for f in files_to_hash:
        if f.exists():
            artifacts.append({
                "path": str(f.relative_to(data_path.parent)),
                "hash": calculate_file_hash(f),
                "lineage": {"source": "pipeline", "transformation": "processed"}
            })
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "artifacts": artifacts,
        "versions": {
            "python": sys.version,
            "rdkit": "unknown", # Would import rdkit.__version__
            "pandas": "unknown"
        }
    }

def verify_artifact_integrity() -> bool:
    """
    T035c: Checks file size of analysis_results.json or data_insufficiency_report.md.
    """
    gate = load_gate_status()
    stat_gate = load_stat_gate_status()
    
    if gate.get("status") == "PASS" and stat_gate.get("status") == "PASS":
        # Check analysis_results.json
        path = get_data_path() / "processed" / "analysis_results.json"
        if not path.exists():
            return False
        if path.stat().st_size == 0:
            return False
        # Check content
        with open(path, "r") as f:
            try:
                data = json.load(f)
                if data.get("N", 0) == 0:
                    return False
                if data.get("R2") is None:
                    return False
            except:
                return False
        return True
    else:
        # Check data_insufficiency_report.md
        path = get_data_path() / "data_insufficiency_report.md"
        if not path.exists():
            return False
        if path.stat().st_size == 0:
            return False
        return True

def generate_results_report():
    """Generates results_report.md."""
    gate = load_gate_status()
    stat_gate = load_stat_gate_status()
    
    if gate.get("status") != "PASS" or stat_gate.get("status") != "PASS":
        # Should not happen if called correctly, but fallback
        generate_data_insufficiency_report()
        return

    results_path = get_data_path() / "processed" / "analysis_results.json"
    results = {}
    if results_path.exists():
        with open(results_path, "r") as f:
            results = json.load(f)
    
    report_content = f"""# Results Report

## Status
Gate Status: {gate.get('status')}
Statistical Gate: {stat_gate.get('status')}

## Methodology
{results.get('methodology', 'N/A')}

## Results
- N Samples: {results.get('N', 'N/A')}
- R2 Score: {results.get('R2', 'N/A')}
- Best Alpha: {results.get('best_alpha', 'N/A')}

## Coefficients
{json.dumps(results.get('coefficients', {}), indent=2)}

## Diagnostics
{json.dumps(results.get('diagnostics', {}), indent=2)}

## Reproducibility
"""
    meta = collect_reproducibility_metadata()
    report_content += f"\n{json.dumps(meta, indent=2)}"

    path = get_data_path().parent / "results_report.md"
    with open(path, "w") as f:
        f.write(report_content)
    print(f"Generated {path}")

def generate_data_insufficiency_report():
    """Generates data_insufficiency_report.md."""
    gate = load_gate_status()
    content = f"""# Data Insufficiency Report

## Reason
{gate.get('reason', 'Unknown')}

## Details
- Status: {gate.get('status')}
"""
    path = get_data_path() / "data_insufficiency_report.md"
    with open(path, "w") as f:
        f.write(content)
    print(f"Generated {path}")

def main():
    """Main entry point for report generation."""
    gate = load_gate_status()
    stat_gate = load_stat_gate_status()
    
    if gate.get("status") == "FAIL" or stat_gate.get("status") == "FAIL":
        generate_data_insufficiency_report()
    else:
        generate_results_report()
    
    # Verify
    if not verify_artifact_integrity():
        print("Warning: Artifact integrity verification failed.")
    else:
        print("Artifact integrity verified.")

if __name__ == "__main__":
    main()