"""
T038: Run quickstart.md validation to ensure full pipeline reproducibility.

This script executes the pipeline steps defined in quickstart.md (simulated via 
the available scripts), captures execution logs, exit codes, and computes 
hashes for generated artifacts to produce a validation report.
"""
import os
import sys
import json
import logging
import subprocess
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lib import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data/logs/validation_execution.log')
    ]
)
logger = logging.getLogger(__name__)

# Define the pipeline steps to validate
PIPELINE_STEPS = [
    {
        "name": "Setup Project Structure",
        "script": "scripts.setup_project",
        "args": []
    },
    {
        "name": "Ingest and Build Subgraph",
        "script": "scripts.save_graph",
        "args": []
    },
    {
        "name": "Generate Final Dataset",
        "script": "scripts.save_final_dataset",
        "args": []
    },
    {
        "name": "Run Statistical Analysis",
        "script": "scripts.save_statistical_metrics",
        "args": []
    },
    {
        "name": "Generate Analysis Report",
        "script": "scripts.generate_analysis_report",
        "args": []
    }
]

ARTIFACT_PATHS = [
    "data/processed/subgraph_with_clusters.parquet",
    "data/processed/final_analysis_dataset.parquet",
    "artifacts/results/statistical_metrics.json",
    "artifacts/results/analysis_report.md"
]

def compute_file_hash(file_path: Path) -> Optional[str]:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        return None
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute hash for {file_path}: {e}")
        return None

def run_pipeline_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single pipeline step and capture results."""
    script_name = step["script"]
    script_path = project_root / script_name.replace(".", "/") + ".py"
    
    if not script_path.exists():
        logger.warning(f"Script not found: {script_path}")
        return {
            "name": step["name"],
            "status": "skipped",
            "reason": "Script not found",
            "exit_code": -1,
            "output": "",
            "duration": 0
        }

    logger.info(f"Running: {step['name']} ({script_name})")
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)] + step.get("args", []),
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per step
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "name": step["name"],
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr,
            "duration": duration
        }
    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        return {
            "name": step["name"],
            "status": "timeout",
            "exit_code": -1,
            "output": "",
            "error": "Execution timed out",
            "duration": duration
        }
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return {
            "name": step["name"],
            "status": "error",
            "exit_code": -1,
            "output": "",
            "error": str(e),
            "duration": duration
        }

def validate_artifacts() -> Dict[str, Any]:
    """Check that all expected artifacts were created and compute hashes."""
    results = {}
    for rel_path in ARTIFACT_PATHS:
        full_path = project_root / rel_path
        exists = full_path.exists()
        file_hash = compute_file_hash(full_path) if exists else None
        
        results[rel_path] = {
            "exists": exists,
            "hash": file_hash,
            "size_bytes": full_path.stat().st_size if exists else 0
        }
    
    return results

def generate_validation_report(execution_results: List[Dict], artifact_results: Dict) -> str:
    """Generate the final validation report in Markdown."""
    timestamp = datetime.now().isoformat()
    all_success = all(
        r["status"] == "success" for r in execution_results
    )
    all_artifacts_exist = all(
        v["exists"] for v in artifact_results.values()
    )
    
    report_lines = [
        "# Pipeline Validation Report",
        "",
        f"**Generated**: {timestamp}",
        f"**Overall Status**: {'✅ PASS' if (all_success and all_artifacts_exist) else '❌ FAIL'}",
        "",
        "## Execution Log",
        ""
    ]
    
    for result in execution_results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        report_lines.append(f"### {status_icon} {result['name']}")
        report_lines.append(f"- **Status**: {result['status']}")
        report_lines.append(f"- **Exit Code**: {result['exit_code']}")
        report_lines.append(f"- **Duration**: {result['duration']:.2f}s")
        if result.get("error"):
            report_lines.append(f"- **Error**: {result['error']}")
        report_lines.append("")
    
    report_lines.extend([
        "## Artifact Verification",
        ""
    ])
    
    for path, info in artifact_results.items():
        status_icon = "✅" if info["exists"] else "❌"
        report_lines.append(f"- {status_icon} `{path}`")
        if info["exists"]:
            report_lines.append(f"  - **Size**: {info['size_bytes']} bytes")
            report_lines.append(f"  - **SHA-256**: `{info['hash']}`")
        else:
            report_lines.append(f"  - **Status**: Missing")
    
    report_lines.extend([
        "",
        "## Summary",
        "",
        f"- **Pipeline Steps Executed**: {len(execution_results)}",
        f"- **Successful Steps**: {sum(1 for r in execution_results if r['status'] == 'success')}",
        f"- **Failed Steps**: {sum(1 for r in execution_results if r['status'] != 'success')}",
        f"- **Artifacts Present**: {sum(1 for v in artifact_results.values() if v['exists'])}/{len(artifact_results)}",
        "",
        f"**Conclusion**: {'The pipeline executed successfully and all artifacts were generated.' if (all_success and all_artifacts_exist) else 'The pipeline validation failed. Review errors above.'}"
    ])
    
    return "\n".join(report_lines)

def main():
    """Main entry point for validation script."""
    logger.info("Starting pipeline validation (T038)...")
    
    # Ensure log directory exists
    (project_root / "data/logs").mkdir(parents=True, exist_ok=True)
    
    execution_results = []
    for step in PIPELINE_STEPS:
        result = run_pipeline_step(step)
        execution_results.append(result)
        # Continue even if a step fails to get full picture
    
    # Validate artifacts
    artifact_results = validate_artifacts()
    
    # Generate report
    report_content = generate_validation_report(execution_results, artifact_results)
    
    # Save report
    report_path = project_root / "artifacts/validation_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.info(f"Validation report saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    print(report_content)
    print("="*50)
    
    # Determine exit code
    all_success = all(r["status"] == "success" for r in execution_results)
    all_artifacts_exist = all(v["exists"] for v in artifact_results.values())
    
    if all_success and all_artifacts_exist:
        logger.info("Validation PASSED")
        sys.exit(0)
    else:
        logger.warning("Validation FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
