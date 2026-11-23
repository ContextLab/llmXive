import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Define the quickstart steps based on the project structure and typical pipeline flow
# These steps must produce the files mentioned in the tasks and quickstart.md
QUICKSTART_STEPS = [
    {
        "name": "Generate Synthetic Baseline Data",
        "command": ["python", "code/validation/synthetic_baseline.py"],
        "expected_outputs": [
            "data/raw/synthetic_baseline.csv"
        ]
    },
    {
        "name": "Validate Instruments",
        "command": ["python", "code/validation/validate_instruments.py"],
        "expected_outputs": []
    },
    {
        "name": "Merge Data",
        "command": ["python", "code/pipeline/merge_data.py"],
        "expected_outputs": [
            "data/processed/merged_data.csv"
        ]
    },
    {
        "name": "Calculate Change Scores",
        "command": ["python", "code/analysis/change_scores.py"],
        "expected_outputs": [
            "data/processed/change_scores.csv"
        ]
    },
    {
        "name": "Run Bootstrap CI Analysis",
        "command": ["python", "code/analysis/bootstrap_ci.py"],
        "expected_outputs": [
            "results/bootstrap_results.json"
        ]
    },
    {
        "name": "Calculate Effect Sizes",
        "command": ["python", "code/analysis/effect_sizes.py"],
        "expected_outputs": [
            "results/effect_sizes.json"
        ]
    },
    {
        "name": "Apply Holm-Bonferroni Correction",
        "command": ["python", "code/analysis/holm_bonferroni.py"],
        "expected_outputs": [
            "results/holm_bonferroni_results.json"
        ]
    },
    {
        "name": "Generate Statistical Summary",
        "command": ["python", "code/analysis/statistical_summary.py"],
        "expected_outputs": [
            "results/statistical_summary.json"
        ]
    },
    {
        "name": "Run Power Simulation",
        "command": ["python", "code/analysis/power_simulation.py"],
        "expected_outputs": [
            "results/power_analysis.json"
        ]
    },
    {
        "name": "Generate Sensitivity Report",
        "command": ["python", "code/analysis/generate_sensitivity_report.py"],
        "expected_outputs": [
            "results/sensitivity_analysis_report.md"
        ]
    },
    {
        "name": "Validate Success Criteria",
        "command": ["python", "code/validation/validate_success_criteria.py"],
        "expected_outputs": [
            "results/validation_report.json"
        ]
    },
    {
        "name": "Generate Final Report",
        "command": ["python", "code/report/generate_report.py"],
        "expected_outputs": [
            "results/final_report.md"
        ]
    },
    {
        "name": "Generate Plots",
        "command": ["python", "code/viz/generate_plots.py"],
        "expected_outputs": [
            "figures/change_scores_boxplot.png",
            "figures/metric_distribution.png"
        ]
    }
]

def run_command(command: List[str], cwd: Optional[Path] = None) -> bool:
    """Run a shell command and return True if successful."""
    logger.info(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout per step
        )
        
        if result.returncode == 0:
            logger.info(f"Success: {' '.join(command)}")
            if result.stdout:
                logger.debug(f"STDOUT: {result.stdout[:500]}...")
            return True
        else:
            logger.error(f"Failed: {' '.join(command)}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout: {' '.join(command)}")
        return False
    except Exception as e:
        logger.error(f"Exception running {' '.join(command)}: {e}")
        return False

def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    return file_path.exists()

def validate_output_file(step_name: str, expected_path: Path, project_root: Path) -> bool:
    """Validate that an expected output file exists."""
    full_path = project_root / expected_path
    exists = check_file_exists(full_path)
    if exists:
        logger.info(f"  ✓ {step_name}: {expected_path} exists")
        return True
    else:
        logger.error(f"  ✗ {step_name}: {expected_path} MISSING")
        return False

def main():
    """Run the full quickstart validation pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation Pipeline")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    results = {
        "start_time": start_time.isoformat(),
        "steps": [],
        "success": True,
        "missing_files": []
    }

    # Ensure required directories exist
    required_dirs = [
        "data/raw", "data/processed", "data/compliance",
        "results", "figures"
    ]
    for dir_path in required_dirs:
        (PROJECT_ROOT / dir_path).mkdir(parents=True, exist_ok=True)

    all_passed = True

    for step in QUICKSTART_STEPS:
        step_name = step["name"]
        command = step["command"]
        expected_outputs = step.get("expected_outputs", [])
        
        logger.info(f"\n--- Step: {step_name} ---")
        
        # Run the command
        success = run_command(command, cwd=PROJECT_ROOT)
        
        step_result = {
            "name": step_name,
            "command": " ".join(command),
            "success": success,
            "outputs_validated": True,
            "missing_outputs": []
        }
        
        if not success:
            all_passed = False
            step_result["outputs_validated"] = False
            logger.error(f"Step failed: {step_name}")
        else:
            # Validate expected outputs
            for output_path in expected_outputs:
                if not validate_output_file(step_name, Path(output_path), PROJECT_ROOT):
                    step_result["outputs_validated"] = False
                    step_result["missing_outputs"].append(output_path)
                    all_passed = False
                    results["missing_files"].append(output_path)
        
        results["steps"].append(step_result)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    results["end_time"] = end_time.isoformat()
    results["duration_seconds"] = duration
    results["success"] = all_passed

    # Write validation report
    report_path = PROJECT_ROOT / "results" / "quickstart_validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("\n" + "=" * 60)
    logger.info("Quickstart Validation Complete")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Overall Status: {'PASSED' if all_passed else 'FAILED'}")
    logger.info(f"Report saved to: {report_path}")
    logger.info("=" * 60)

    if not all_passed:
        logger.warning("\nMissing files:")
        for missing in results["missing_files"]:
            logger.warning(f"  - {missing}")
        sys.exit(1)
    else:
        logger.info("\nAll steps completed and outputs validated successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
