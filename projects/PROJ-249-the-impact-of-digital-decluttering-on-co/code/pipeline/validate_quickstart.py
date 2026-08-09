"""
T048: Quickstart Validation Script
Validates end-to-end reproducibility by running the full pipeline defined in quickstart.md.
"""
import os
import sys
import subprocess
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return True if successful."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.stdout:
            logger.info(result.stdout.strip())
        if result.stderr:
            logger.warning(result.stderr.strip())
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Command timed out")
        return False

def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists."""
    exists = os.path.isfile(path)
    if exists:
        logger.info(f"✓ Found: {description} ({path})")
    else:
        logger.error(f"✗ Missing: {description} ({path})")
    return exists

def validate_output_file(path: str, min_size: int = 0) -> bool:
    """Validate that an output file exists and has content."""
    if not os.path.isfile(path):
        logger.error(f"Output file missing: {path}")
        return False
    
    size = os.path.getsize(path)
    if size < min_size:
        logger.error(f"Output file too small: {path} ({size} bytes)")
        return False
    
    logger.info(f"✓ Validated output: {path} ({size} bytes)")
    return True

def main():
    """Run the full quickstart validation pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation (T048)")
    logger.info("=" * 60)

    # Define the pipeline steps based on quickstart.md
    pipeline_steps = [
        {
            "name": "Setup Data Directories",
            "command": [sys.executable, "-m", "code.setup.setup_data_dirs"],
            "check_files": ["data/raw", "data/processed", "data/compliance"]
        },
        {
            "name": "Generate Synthetic Baseline Data",
            "command": [sys.executable, "-m", "code.validation.synthetic_baseline"],
            "check_files": ["data/raw/synthetic_baseline.csv"]
        },
        {
            "name": "Validate Instruments",
            "command": [sys.executable, "-m", "code.validation.validate_instruments"],
            "check_files": []
        },
        {
            "name": "Collect Baseline Data Pipeline",
            "command": [sys.executable, "-m", "code.pipeline.collect_baseline"],
            "check_files": ["data/raw/baseline_data.csv"]
        },
        {
            "name": "Parse Compliance Logs",
            "command": [sys.executable, "-m", "code.compliance.parse_logs"],
            "check_files": ["data/processed/parsed_logs.csv"]
        },
        {
            "name": "Aggregate Compliance",
            "command": [sys.executable, "-m", "code.pipeline.aggregate_compliance"],
            "check_files": ["data/processed/compliance_scores.csv"]
        },
        {
            "name": "Merge Data",
            "command": [sys.executable, "-m", "code.pipeline.merge_data"],
            "check_files": ["data/processed/merged_data.csv"]
        },
        {
            "name": "Calculate Change Scores",
            "command": [sys.executable, "-m", "code.analysis.change_scores"],
            "check_files": ["data/processed/change_scores.csv"]
        },
        {
            "name": "Bootstrap CI Analysis",
            "command": [sys.executable, "-m", "code.analysis.bootstrap_ci"],
            "check_files": ["data/processed/bootstrap_results.json"]
        },
        {
            "name": "Effect Sizes",
            "command": [sys.executable, "-m", "code.analysis.effect_sizes"],
            "check_files": ["data/processed/effect_sizes.json"]
        },
        {
            "name": "Holm-Bonferroni Correction",
            "command": [sys.executable, "-m", "code.analysis.holm_bonferroni"],
            "check_files": ["data/processed/holm_corrected.json"]
        },
        {
            "name": "Statistical Summary",
            "command": [sys.executable, "-m", "code.analysis.statistical_summary"],
            "check_files": ["results/statistical_summary.json"]
        },
        {
            "name": "Generate Sensitivity Report",
            "command": [sys.executable, "-m", "code.analysis.generate_sensitivity_report"],
            "check_files": ["results/sensitivity_analysis_report.md"]
        },
        {
            "name": "Power Simulation",
            "command": [sys.executable, "-m", "code.analysis.power_simulation"],
            "check_files": ["results/power_analysis.json"]
        },
        {
            "name": "Generate Plots",
            "command": [sys.executable, "-m", "code.viz.generate_plots"],
            "check_files": ["figures/change_scores_boxplot.png"]
        },
        {
            "name": "Validate Success Criteria",
            "command": [sys.executable, "-m", "code.validation.validate_success_criteria"],
            "check_files": ["results/validation_report.json"]
        },
        {
            "name": "Generate Final Report",
            "command": [sys.executable, "-m", "code.report.generate_report"],
            "check_files": ["results/final_report.md"]
        }
    ]

    failed_steps = []
    passed_steps = []

    for step in pipeline_steps:
        step_name = step["name"]
        cmd = step["command"]
        check_files = step.get("check_files", [])

        # Run the command
        if not run_command(cmd, step_name):
            logger.error(f"Step failed: {step_name}")
            failed_steps.append(step_name)
            continue

        # Check output files
        files_ok = True
        for file_path in check_files:
            full_path = Path(file_path)
            if not check_file_exists(str(full_path), f"{step_name} output"):
                files_ok = False
                break

        if files_ok:
            passed_steps.append(step_name)
        else:
            logger.error(f"Step output validation failed: {step_name}")
            failed_steps.append(step_name)

    # Summary
    logger.info("=" * 60)
    logger.info("Quickstart Validation Summary")
    logger.info("=" * 60)
    logger.info(f"Passed: {len(passed_steps)}/{len(pipeline_steps)}")
    logger.info(f"Failed: {len(failed_steps)}/{len(pipeline_steps)}")

    if failed_steps:
        logger.error("Failed steps:")
        for step in failed_steps:
            logger.error(f"  - {step}")
        logger.error("Validation FAILED")
        return 1
    else:
        logger.info("All steps passed successfully!")
        logger.info("Validation PASSED")
        
        # Validate key output files have content
        key_outputs = [
            ("results/statistical_summary.json", 100),
            ("results/final_report.md", 500),
            ("results/power_analysis.json", 100)
        ]
        
        all_outputs_ok = True
        for path, min_size in key_outputs:
            if not validate_output_file(path, min_size):
                all_outputs_ok = False
        
        if all_outputs_ok:
            logger.info("All key outputs validated successfully.")
            return 0
        else:
            logger.error("Some key outputs failed validation.")
            return 1

if __name__ == "__main__":
    sys.exit(main())