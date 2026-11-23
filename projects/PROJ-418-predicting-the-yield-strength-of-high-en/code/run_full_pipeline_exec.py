"""
T117: Execute the full pipeline end-to-end and generate all required artifacts.

This script orchestrates the execution of the complete HEA yield strength prediction
pipeline, ensuring all dependencies (T021, T030, T044, T131, T144, T145, T146, T147, T148)
are executed in the correct order and that all required artifacts are generated.

Required artifacts:
- manifest.json
- report.md
- metrics.json
- stability_rankings.json
- external_metrics.json
- pipeline_runtime.json
- final_validation_report.json
"""
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, set_seeds
from data.pipeline import run_pipeline
from models.train import run_training_pipeline
from models.evaluate import run_evaluation_pipeline
from models.report_generator import write_report
from models.runtime_tracker import save_runtime
from run_full_pipeline import build_manifest
from validation.final_validator import run_final_validation

logger = get_logger(__name__)

def main():
    start_time = time.time()
    logger.info("Starting T117: Full Pipeline Execution")
    
    # Set deterministic seeds
    set_seeds(42)
    
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Run Data Pipeline (T008-T015, T200)
    logger.info("Executing data pipeline...")
    pipeline_result = run_pipeline()
    if pipeline_result == "NO_DATA":
        logger.error("Pipeline failed: No data available")
        return False

    # Step 2: Run Training Pipeline (T016, T018, T019, T020, T021)
    logger.info("Executing training pipeline...")
    training_result = run_training_pipeline()
    if not training_result:
        logger.error("Training pipeline failed")
        return False

    # Step 3: Run Evaluation Pipeline (T023, T023b, T030, T044, T131, T135, T143, T145, T146, T147)
    logger.info("Executing evaluation pipeline...")
    eval_result = run_evaluation_pipeline()
    if not eval_result:
        logger.error("Evaluation pipeline failed")
        return False

    # Step 4: Run Stability Assessment (T144)
    logger.info("Executing stability assessment...")
    stability_script = project_root / "scripts" / "run_stability.py"
    if stability_script.exists():
        import subprocess
        result = subprocess.run(
            [sys.executable, str(stability_script)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode != 0:
            logger.error(f"Stability assessment failed: {result.stderr}")
            return False
    else:
        logger.warning("Stability script not found, skipping")

    # Step 5: Generate Report (T028, T133, T148)
    logger.info("Generating final report...")
    report_success = write_report()
    if not report_success:
        logger.error("Report generation failed")
        return False

    # Step 6: Generate Manifest (T062, T122)
    logger.info("Generating manifest...")
    manifest_path = output_dir / "manifest.json"
    build_manifest(str(manifest_path))
    if not manifest_path.exists():
        logger.error("Manifest generation failed")
        return False

    # Step 7: Save Runtime (T120)
    end_time = time.time()
    runtime_seconds = end_time - start_time
    runtime_data = {
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "total_duration_seconds": runtime_seconds,
        "status": "pass" if runtime_seconds <= 7200 else "fail"
    }
    runtime_path = output_dir / "pipeline_runtime.json"
    with open(runtime_path, "w") as f:
        json.dump(runtime_data, f, indent=2)
    logger.info(f"Pipeline runtime: {runtime_seconds:.2f}s")

    # Step 8: Run Final Validation (T118-T126)
    logger.info("Running final validation...")
    validation_result = run_final_validation()
    if not validation_result:
        logger.error("Final validation failed")
        return False

    # Verify all required artifacts exist
    required_artifacts = [
        "manifest.json",
        "report.md",
        "metrics.json",
        "stability_rankings.json",
        "external_metrics.json",
        "pipeline_runtime.json",
        "final_validation_report.json"
    ]
    
    all_present = True
    for artifact in required_artifacts:
        path = output_dir / artifact
        if not path.exists():
            logger.error(f"Missing required artifact: {artifact}")
            all_present = False
        else:
            logger.info(f"Found artifact: {artifact}")

    if not all_present:
        return False

    logger.info("T117: Full pipeline execution completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
