import os
import sys
import json
import time
from pathlib import Path
from utils.logging import get_logger, set_seeds
from utils.timer import start_phase, stop_phase, save_runtime_report
from data.pipeline import run_pipeline
from models.train import run_training_pipeline
from models.evaluate import run_evaluation_pipeline
from models.metrics_writer import write_metrics_json
from models.report_generator import write_report
from models.power_analysis import write_power_analysis
from models.runtime_tracker import track_runtime, save_runtime
from data.status_writer import write_data_status
from utils.config import get_config
from data.download import download_dataset

def main():
    logger = get_logger(__name__)
    logger.info("Starting full pipeline execution for T117")

    # Set seeds for reproducibility
    set_seeds(42)

    start_time = time.time()
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)

    # Phase 1: Data Acquisition
    logger.info("Phase 1: Data Acquisition")
    start_phase("data_acquisition")
    try:
        download_status = download_dataset()
        if download_status == "NO_DATA":
            logger.error("No data found. Aborting pipeline.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Data acquisition failed: {e}")
        sys.exit(1)
    stop_phase("data_acquisition")

    # Phase 2: Data Processing (Pipeline)
    logger.info("Phase 2: Data Processing")
    start_phase("data_processing")
    try:
        pipeline_status = run_pipeline()
        if pipeline_status != "SUCCESS":
            logger.error(f"Data processing failed with status: {pipeline_status}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Data processing failed: {e}")
        sys.exit(1)
    stop_phase("data_processing")

    # Phase 3: Power Analysis
    logger.info("Phase 3: Power Analysis")
    start_phase("power_analysis")
    try:
        write_power_analysis()
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        sys.exit(1)
    stop_phase("power_analysis")

    # Phase 4: Model Training
    logger.info("Phase 4: Model Training")
    start_phase("model_training")
    try:
        run_training_pipeline()
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        sys.exit(1)
    stop_phase("model_training")

    # Phase 5: Evaluation and Statistical Validation
    logger.info("Phase 5: Evaluation and Statistical Validation")
    start_phase("evaluation")
    try:
        run_evaluation_pipeline()
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)
    stop_phase("evaluation")

    # Phase 6: Metrics Writing
    logger.info("Phase 6: Metrics Writing")
    start_phase("metrics_writing")
    try:
        write_metrics_json()
    except Exception as e:
        logger.error(f"Metrics writing failed: {e}")
        sys.exit(1)
    stop_phase("metrics_writing")

    # Phase 7: Report Generation
    logger.info("Phase 7: Report Generation")
    start_phase("report_generation")
    try:
        write_report()
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)
    stop_phase("report_generation")

    # Phase 8: Runtime Tracking
    logger.info("Phase 8: Runtime Tracking")
    start_phase("runtime_tracking")
    try:
        track_runtime()
        save_runtime()
    except Exception as e:
        logger.error(f"Runtime tracking failed: {e}")
        sys.exit(1)
    stop_phase("runtime_tracking")

    total_time = time.time() - start_time
    logger.info(f"Full pipeline completed successfully in {total_time:.2f} seconds")

    # Write final status
    status = {
        "status": "SUCCESS",
        "total_runtime_seconds": total_time,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(output_dir / "pipeline_final_status.json", "w") as f:
        json.dump(status, f, indent=2)

    return 0

if __name__ == "__main__":
    sys.exit(main())