"""
Execution Order Validator

This module provides a standalone utility to validate the execution order
of the pipeline tasks. It ensures that all required dependencies (output files)
from previous tasks exist before allowing the pipeline to proceed.

This prevents the pipeline from running with stale or missing data,
which was the root cause of the previous execution failures.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskOrderError(Exception):
    """
    Exception raised when a task dependency is missing or invalid.
    This halts the pipeline execution to prevent analysis on stale/missing data.
    """
    def __init__(self, message: str, missing_files: Optional[List[str]] = None):
        super().__init__(message)
        self.missing_files = missing_files or []


class ExecutionOrderValidator:
    """
    Validates that all required output files from previous tasks exist
    before allowing the pipeline to proceed.

    This validator is called by `code/main.py` as a pre-flight check.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the validator.

        Args:
            base_path: The base directory for the project (defaults to project root).
        """
        self.base_path = base_path or Path(__file__).resolve().parent.parent.parent
        self.required_dependencies: Dict[str, List[str]] = self._define_dependencies()

    def _define_dependencies(self) -> Dict[str, str]:
        """
        Defines the mapping of task IDs to their required output files.
        These are the critical artifacts that must exist before specific phases can run.

        Returns:
            Dict mapping task_id to list of required file paths (relative to base_path).
        """
        return {
            # T004: Seed Manager (no specific file output, but ensures config exists)
            # T005: Memory Monitor (no specific file output)
            # T008: OpenNeuro Fetcher
            "T008_fetch": [
                "data/raw/ds000030/dataset_description.json"
            ],
            # T009: Data Validator
            "T009_validate": [
                "data/raw/ds000030/.bidsignore", # Or a specific validation report if generated
                "data/raw/ds000030/sub-01/anat/sub-01_T1w.nii.gz" # Example: ensure at least one subject exists
            ],
            # T012: ROI Extractor
            "T012_roi": [
                "data/derived/roi_timeseries.csv"
            ],
            # T013: Temporal Smoothing
            "T013_smooth": [
                "data/derived/smoothed_roi_timeseries.csv"
            ],
            # T014: Noise Estimator
            "T014_noise": [
                "data/derived/noise_parameters.json"
            ],
            # T016: GLM Fitter (Convergence Log)
            "T016_glm": [
                "data/aggregated/convergence_log.json"
            ],
            # T017: Split Half Validator
            "T017_split": [
                "data/aggregated/split_half_results.json"
            ],
            # T022: Power Curve Generator
            "T022_power": [
                "data/aggregated/power_curves.json"
            ],
            # T029: Multi-Paradigm Runner
            "T029_multi": [
                "data/aggregated/multi_paradigm_results.json"
            ],
            # T055: Result Finalizer
            "T055_final": [
                "results/paper/final_analysis_report.md"
            ]
        }

    def check_dependencies(self, task_id: str) -> bool:
        """
        Checks if all dependencies for a specific task ID exist.

        Args:
            task_id: The ID of the task to check (e.g., "T017").

        Returns:
            True if all dependencies exist, False otherwise.

        Raises:
            TaskOrderError: If any dependency is missing.
        """
        # Map task ID to dependency key (handle potential suffixes like _fetch, _validate)
        dependency_key = None
        for key in self.required_dependencies.keys():
            if key.startswith(task_id):
                dependency_key = key
                break

        if not dependency_key:
            logger.warning(f"No explicit dependency definition found for task {task_id}. Skipping check.")
            return True

        required_files = self.required_dependencies[dependency_key]
        missing_files = []

        for rel_path in required_files:
            full_path = self.base_path / rel_path
            if not full_path.exists():
                missing_files.append(str(full_path.relative_to(self.base_path)))

        if missing_files:
            error_msg = (
                f"Task {task_id} cannot proceed. Missing required dependencies:\n"
                + "\n".join([f"  - {f}" for f in missing_files])
            )
            logger.error(error_msg)
            raise TaskOrderError(error_msg, missing_files)

        logger.info(f"Task {task_id} dependencies verified successfully.")
        return True

    def validate_pipeline_start(self) -> bool:
        """
        Performs a pre-flight check for the entire pipeline start.
        Ensures that the foundational tasks (T008, T009) have completed.

        Returns:
            True if pipeline can start, False otherwise.

        Raises:
            TaskOrderError: If foundational tasks are incomplete.
        """
        logger.info("Running pre-flight execution order validation...")
        
        # Check foundational data availability
        try:
            self.check_dependencies("T008")
            self.check_dependencies("T009")
        except TaskOrderError as e:
            logger.error("Pipeline startup blocked: Missing foundational data.")
            raise e

        logger.info("Pipeline startup validation passed.")
        return True

    def validate_analysis_phase(self) -> bool:
        """
        Validates dependencies before the main analysis phase (T012-T017).
        
        Returns:
            True if analysis phase can start.
            
        Raises:
            TaskOrderError: If preprocessing outputs are missing.
        """
        logger.info("Running pre-flight validation for analysis phase...")
        
        try:
            self.check_dependencies("T012")
            self.check_dependencies("T013")
            self.check_dependencies("T014")
        except TaskOrderError as e:
            logger.error("Analysis phase blocked: Missing preprocessing outputs.")
            raise e

        logger.info("Analysis phase validation passed.")
        return True

    def validate_power_analysis_phase(self) -> bool:
        """
        Validates dependencies before the power analysis phase (T017, T022).
        
        Returns:
            True if power analysis phase can start.
            
        Raises:
            TaskOrderError: If GLM or split-half results are missing.
        """
        logger.info("Running pre-flight validation for power analysis phase...")
        
        try:
            # T016 is required for T017
            self.check_dependencies("T016")
            # T017 is required for T022
            self.check_dependencies("T017")
        except TaskOrderError as e:
            logger.error("Power analysis phase blocked: Missing intermediate results.")
            raise e

        logger.info("Power analysis phase validation passed.")
        return True


def main():
    """
    Entry point for the validator when run as a script.
    Useful for manual verification or CI checks.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate execution order dependencies")
    parser.add_argument(
        "--phase",
        choices=["start", "analysis", "power", "full"],
        default="full",
        help="Which phase of dependencies to validate"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="Base path for the project (default: auto-detect)"
    )

    args = parser.parse_args()
    
    base = Path(args.base_path) if args.base_path else None
    validator = ExecutionOrderValidator(base_path=base)

    try:
        if args.phase == "start":
            validator.validate_pipeline_start()
        elif args.phase == "analysis":
            validator.validate_analysis_phase()
        elif args.phase == "power":
            validator.validate_power_analysis_phase()
        elif args.phase == "full":
            validator.validate_pipeline_start()
            validator.validate_analysis_phase()
            validator.validate_power_analysis_phase()
        
        print("SUCCESS: All dependencies validated.")
        sys.exit(0)

    except TaskOrderError as e:
        print(f"FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()