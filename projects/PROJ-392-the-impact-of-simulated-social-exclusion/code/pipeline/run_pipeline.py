"""
Orchestration skeleton for the fMRI social exclusion and reward analysis pipeline.

This module provides the main entry point for running the full analysis pipeline,
including data download, preprocessing, analysis, and visualization stages.
It implements robust error handling, logging, and progress tracking.
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project root relative to this file (code/pipeline -> root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "data" / "results" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            LOGS_DIR / f"pipeline_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)
logger = logging.getLogger("run_pipeline")


class PipelineError(Exception):
    """Custom exception for pipeline execution failures."""
    pass


class Stage:
    """Represents a single stage in the pipeline."""

    def __init__(self, name: str, func: callable, required: bool = True):
        self.name = name
        self.func = func
        self.required = required
        self.status = "pending"  # pending, running, success, failed
        self.duration: Optional[float] = None
        self.error: Optional[str] = None

    def run(self, context: Dict[str, Any]) -> bool:
        """Execute the stage and update status."""
        self.status = "running"
        start_time = time.time()
        try:
            logger.info(f"Starting stage: {self.name}")
            result = self.func(context)
            if result is not None:
                context.update(result)
            self.status = "success"
            logger.info(f"Stage {self.name} completed successfully.")
            return True
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            self.duration = time.time() - start_time
            logger.error(f"Stage {self.name} failed: {e}", exc_info=True)
            if self.required:
                raise PipelineError(f"Required stage '{self.name}' failed: {e}") from e
            logger.warning(f"Optional stage '{self.name}' failed, continuing...")
            return False
        finally:
            if self.duration is None:
                self.duration = time.time() - start_time


def run_download_stage(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for data download stage.
    Actual implementation will be provided in T010.
    """
    logger.info("Executing data download stage (placeholder).")
    # TODO: Call code/data_download/download_openneuro.py logic here
    return {"download_stage": "completed"}


def run_preprocess_stage(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for preprocessing stage.
    Actual implementation will be provided in T013.
    """
    logger.info("Executing preprocessing stage (placeholder).")
    # TODO: Call code/preprocess/run_preprocessing.py logic here
    return {"preprocess_stage": "completed"}


def run_analysis_stage(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for analysis stage.
    Actual implementation will be provided in T017-T024.
    """
    logger.info("Executing analysis stage (placeholder).")
    # TODO: Call code/analysis/roi_extraction.py and group_analysis.py logic here
    return {"analysis_stage": "completed"}


def run_visualization_stage(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for visualization stage.
    Actual implementation will be provided in T025.
    """
    logger.info("Executing visualization stage (placeholder).")
    # TODO: Call code/visualization/plot_results.py logic here
    return {"visualization_stage": "completed"}


def run_report_stage(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for reporting stage.
    Actual implementation will be provided in T027.
    """
    logger.info("Executing report generation stage (placeholder).")
    # TODO: Call code/visualization/report generation logic here
    return {"report_stage": "completed"}


def build_pipeline(stages_config: Optional[List[str]] = None) -> List[Stage]:
    """
    Build the ordered list of pipeline stages.

    Args:
        stages_config: Optional list of stage names to include. If None, all stages are included.

    Returns:
        List of Stage objects in execution order.
    """
    all_stages = [
        Stage("download", run_download_stage, required=True),
        Stage("preprocess", run_preprocess_stage, required=True),
        Stage("analysis", run_analysis_stage, required=True),
        Stage("visualization", run_visualization_stage, required=False),
        Stage("report", run_report_stage, required=False),
    ]

    if stages_config:
        filtered_stages = [s for s in all_stages if s.name in stages_config]
        if len(filtered_stages) != len(stages_config):
            missing = set(stages_config) - {s.name for s in filtered_stages}
            logger.warning(f"Unknown stages ignored: {missing}")
        return filtered_stages
    return all_stages


def execute_pipeline(stages_config: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Execute the full pipeline with error handling and logging.

    Args:
        stages_config: Optional list of stage names to execute.

    Returns:
        Dictionary containing execution results and metadata.
    """
    logger.info("Initializing pipeline execution...")
    start_time = time.time()

    context: Dict[str, Any] = {
        "start_time": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "stages": [],
        "status": "running",
    }

    stages = build_pipeline(stages_config)
    context["stages"] = [s.name for s in stages]

    try:
        for stage in stages:
            stage.run(context)
            if stage.status == "failed" and stage.required:
                context["status"] = "failed"
                return context

        context["status"] = "success"
        logger.info("Pipeline execution completed successfully.")

    except PipelineError as e:
        context["status"] = "failed"
        context["error"] = str(e)
        logger.error(f"Pipeline execution failed: {e}")

    finally:
        context["end_time"] = datetime.now(timezone.utc).isoformat()
        context["total_duration_seconds"] = time.time() - start_time
        context["stage_details"] = [
            {
                "name": s.name,
                "status": s.status,
                "duration_seconds": s.duration,
                "error": s.error,
            }
            for s in stages
        ]

    return context


def main():
    """Main entry point for the pipeline script."""
    parser = argparse.ArgumentParser(
        description="Run the fMRI social exclusion and reward analysis pipeline."
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=["download", "preprocess", "analysis", "visualization", "report"],
        help="Specific stages to run (default: all).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (debug level).",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Running pipeline with stages: {args.stages or 'all'}")
    result = execute_pipeline(stages_config=args.stages)

    # Print summary
    print("\n--- Pipeline Execution Summary ---")
    print(f"Status: {result['status']}")
    print(f"Duration: {result['total_duration_seconds']:.2f} seconds")
    for stage in result["stage_details"]:
        print(f"  {stage['name']}: {stage['status']} ({stage['duration_seconds']:.2f}s)")
        if stage["error"]:
            print(f"    Error: {stage['error']}")
    print("----------------------------------")

    if result["status"] == "failed":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()