"""
Orchestrator for the Neural Correlates of Simulated Social Exclusion pipeline.
Integrates data loading, QC, and prepares the subject metadata for downstream analysis.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import from local project modules based on provided API surface
from src.config import load_config
from src.data_loader import load_openneuro_dataset, ERR_DATA_UNAVAILABLE
from src.qc import run_qc_pipeline, check_subject_count, InsufficientDataError, verify_conditions
from src.integrity import update_hashes, get_logger as get_integrity_logger, IntegrityError
from src.utils import setup_logging, get_logger, log_exception, PipelineError

def main():
    """
    Main entry point for the pipeline.
    1. Load configuration.
    2. Download/OpenNeuro dataset.
    3. Run QC pipeline (Motion, Count, Conditions).
    4. Generate subjects_metadata.json.
    5. Update integrity hashes.
    """
    # Setup logging
    log_dir = Path("code/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=log_dir / "pipeline.log")
    logger = get_logger("main")

    logger.info("Starting Neural Correlates Pipeline (T017 Orchestrator)")

    try:
        # 1. Load Configuration
        logger.info("Loading configuration...")
        config = load_config()
        motion_threshold = config.get("qc", {}).get("motion_threshold_mm", 3.0)
        min_subjects = config.get("qc", {}).get("min_subjects", 10)
        dataset_id = config.get("data", {}).get("openneuro_dataset_id", "ds000030")
        
        # 2. Data Ingestion
        logger.info(f"Fetching dataset {dataset_id} from OpenNeuro...")
        try:
            data_root = load_openneuro_dataset(dataset_id)
        except ERR_DATA_UNAVAILABLE as e:
            logger.critical(f"Data fetch failed: {e}")
            raise PipelineError("Failed to retrieve real data from OpenNeuro.") from e

        if not data_root or not data_root.exists():
            raise PipelineError("Data loader returned invalid path.")

        logger.info(f"Data located at: {data_root}")

        # 3. Run QC Pipeline
        # This encapsulates T013 (Motion Calc), T014 (Filter), T015 (Count Check), T016 (Condition Check)
        logger.info("Running QC pipeline...")
        
        # run_qc_pipeline handles motion calculation, filtering, and outputting subject_qc_list.json
        qc_results = run_qc_pipeline(
            data_root=data_root,
            motion_threshold=motion_threshold,
            logger=logger
        )

        # T015: Check subject count (raises InsufficientDataError if < 10)
        retained_subjects = qc_results.get("retained_subjects", [])
        check_subject_count(len(retained_subjects), min_subjects, logger)

        # T016: Verify conditions for retained subjects
        # verify_conditions returns a list of subjects that passed condition checks
        final_subjects = verify_conditions(
            data_root=data_root,
            subject_list=retained_subjects,
            logger=logger
        )

        if not final_subjects:
            raise PipelineError("No subjects passed condition verification after QC.")

        logger.info(f"QC Complete. {len(final_subjects)} subjects retained.")

        # 4. Generate Output Artifact: data/processed/subjects_metadata.json
        output_dir = Path("code/data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "subjects_metadata.json"

        metadata = {
            "dataset_id": dataset_id,
            "motion_threshold_mm": motion_threshold,
            "min_subjects_required": min_subjects,
            "total_subjects_processed": len(retained_subjects),
            "final_retained_count": len(final_subjects),
            "subjects": final_subjects
        }

        with open(output_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Successfully wrote {output_file}")

        # 5. Update Integrity Hashes (T007)
        logger.info("Updating integrity hashes...")
        try:
            # Scan the data directory to update hashes in the state file
            update_hashes()
            logger.info("Integrity hashes updated successfully.")
        except IntegrityError as e:
            logger.warning(f"Integrity update warning (non-fatal): {e}")

        logger.info("Pipeline completed successfully.")
        return 0

    except InsufficientDataError as e:
        logger.critical(f"Pipeline halted due to insufficient data: {e}")
        return 1
    except ERR_DATA_UNAVAILABLE as e:
        logger.critical(f"Data unavailable error: {e}")
        return 1
    except PipelineError as e:
        logger.critical(f"Pipeline error: {e}")
        log_exception(logger)
        return 1
    except Exception as e:
        logger.critical("Unexpected error in main orchestrator.")
        log_exception(logger)
        return 1

if __name__ == "__main__":
    sys.exit(main())