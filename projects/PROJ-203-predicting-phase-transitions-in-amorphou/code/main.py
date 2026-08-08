"""
Main entry point for the full pipeline: Predicting Phase Transitions in Amorphous Solids.
Orchestrates data generation, model training, evaluation, and report generation.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, reset_config
from utils.logging_config import setup_pipeline_logging, export_events_to_json
from utils.timeout_enforcer import TimeoutEnforcer, PipelineTimeoutError
from data.validate_literature_subset import main as validate_literature
from data.simulate import main as run_simulations
from data.descriptor_utils import main as extract_descriptors
from data.merge import main as merge_datasets
from data.finalize_dataset import main as finalize_dataset
from models.train import main as train_models
from models.generate_metrics_report import main as generate_metrics
from models.generate_shap_plots import main as generate_shap
from models.partial_dependence_analysis import main as generate_pdp
from models.multiple_comparison_correction import main as multiple_comparison
from models.stability_analysis import main as stability_analysis
from models.sensitivity_analysis import main as sensitivity_analysis
from models.collinearity_analysis import main as collinearity_analysis
from models.generate_metrics_report import main as metrics_report
from models.null_model_analysis import main as null_model_analysis
from utils.timeout_enforcer import get_remaining_time

logger = logging.getLogger(__name__)

def run_pipeline():
    """Execute the full pipeline with timeout enforcement."""
    config = get_config()
    reset_config()

    # Setup logging
    log_dir = Path(config.paths.data_logs)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    setup_pipeline_logging(log_file)

    logger.info("=" * 80)
    logger.info("STARTING FULL PIPELINE: Predicting Phase Transitions in Amorphous Solids")
    logger.info(f"Pilot Scope: N=24 compositions")
    logger.info("=" * 80)

    # Initialize timeout enforcer (6 hour limit)
    timeout_seconds = 6 * 60 * 60  # 6 hours
    with TimeoutEnforcer(timeout_seconds) as enforcer:
        try:
            # Step 1: Validate literature subset
            logger.info("STEP 1: Validating literature subset data...")
            validate_literature()
            logger.info("✓ Literature subset validated.")

            # Step 2: Run MD simulations
            logger.info("STEP 2: Running MD simulations for pilot compositions...")
            run_simulations()
            logger.info("✓ Simulations completed.")

            # Step 3: Extract structural descriptors
            logger.info("STEP 3: Extracting structural descriptors from trajectories...")
            extract_descriptors()
            logger.info("✓ Descriptors extracted.")

            # Step 4: Merge simulation descriptors with experimental labels
            logger.info("STEP 4: Merging datasets...")
            merge_datasets()
            logger.info("✓ Datasets merged.")

            # Step 5: Finalize and validate dataset
            logger.info("STEP 5: Finalizing dataset with labeling and validation...")
            finalize_dataset()
            logger.info("✓ Dataset finalized: data/processed/final_dataset.parquet")

            # Step 6: Train models
            logger.info("STEP 6: Training Random Forest models...")
            train_models()
            logger.info("✓ Models trained and saved.")

            # Step 7: Generate metrics report
            logger.info("STEP 7: Generating performance metrics report...")
            generate_metrics()
            logger.info("✓ Metrics report generated.")

            # Step 8: Generate SHAP plots
            logger.info("STEP 8: Generating SHAP interpretability plots...")
            generate_shap()
            logger.info("✓ SHAP plots generated.")

            # Step 9: Generate partial dependence plots
            logger.info("STEP 9: Generating partial dependence plots...")
            generate_pdp()
            logger.info("✓ Partial dependence plots generated.")

            # Step 10: Multiple comparison correction
            logger.info("STEP 10: Applying Bonferroni correction to SHAP ranks...")
            multiple_comparison()
            logger.info("✓ Multiple comparison correction applied.")

            # Step 11: Stability analysis (LOO jackknife)
            logger.info("STEP 11: Running LOO jackknife stability analysis...")
            stability_analysis()
            logger.info("✓ Stability analysis completed.")

            # Step 12: Sensitivity analysis
            logger.info("STEP 12: Running threshold sensitivity analysis...")
            sensitivity_analysis()
            logger.info("✓ Sensitivity analysis completed.")

            # Step 13: Collinearity analysis
            logger.info("STEP 13: Running collinearity (VIF) analysis...")
            collinearity_analysis()
            logger.info("✓ Collinearity analysis completed.")

            # Step 14: Null model and permutation test
            logger.info("STEP 14: Running null model and permutation tests...")
            null_model_analysis()
            logger.info("✓ Null model analysis completed.")

            # Step 15: Aggregate timing
            logger.info("STEP 15: Aggregating pipeline timing...")
            timing_data = {
                "total_wall_clock_seconds": enforcer.elapsed_seconds,
                "limit_seconds": timeout_seconds,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            timing_path = Path(config.paths.artifacts_reports) / "pipeline_timing.json"
            timing_path.parent.mkdir(parents=True, exist_ok=True)
            with open(timing_path, 'w') as f:
                json.dump(timing_data, f, indent=2)
            logger.info(f"✓ Pipeline timing saved: {timing_path}")

            logger.info("=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info(f"Total Runtime: {enforcer.elapsed_seconds:.2f} seconds")
            logger.info(f"Within Budget: {enforcer.elapsed_seconds <= timeout_seconds}")
            logger.info("=" * 80)

        except PipelineTimeoutError as e:
            logger.error(f"PIPELINE TIMEOUT: {e}")
            logger.error("Saving partial results before exit...")
            export_events_to_json()
            sys.exit(1)
        except Exception as e:
            logger.error(f"PIPELINE ERROR: {e}", exc_info=True)
            export_events_to_json()
            sys.exit(1)
        finally:
            # Final cleanup
            export_events_to_json()

    return 0

if __name__ == "__main__":
    sys.exit(run_pipeline())
