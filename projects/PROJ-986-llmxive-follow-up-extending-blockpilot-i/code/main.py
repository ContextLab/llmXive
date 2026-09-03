import logging
import sys
import os
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime
import signal
import json

# Import configuration
from config import load_config, get_config, DatasetConfig, SweepConfig, FeatureConfig, TrainingConfig, PathsConfig

# Import pipeline components
from sweep import run_sweep, save_checkpoint, load_checkpoint
from features import run_feature_extraction
from train import run_training
from evaluate import evaluate_and_report
from utils.data_loader import process_streamed_dataset_with_logging
from utils.join_utils import join_ground_truth_and_features, join_uncertainty_metrics

# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataLoadError(PipelineError):
    """Error during data loading."""
    pass

class FeatureExtractionError(PipelineError):
    """Error during feature extraction."""
    pass

class ModelTrainingError(PipelineError):
    """Error during model training."""
    pass

class EvaluationError(PipelineError):
    """Error during evaluation."""
    pass

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for the pipeline."""
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def handle_oom_error(logger: logging.Logger, sample_id: Optional[str] = None):
    """Handle Out Of Memory errors gracefully."""
    logger.warning(f"OOM detected. Sample ID: {sample_id}. Skipping or reducing batch size.")
    # In a real implementation, this might trigger a retry with batch_size=1
    # or skip the sample depending on the strategy defined in config.

def safe_execute(func: Callable, *args, logger: logging.Logger, **kwargs) -> bool:
    """Execute a function with error handling and logging."""
    try:
        func(*args, **kwargs)
        return True
    except DataLoadError as e:
        logger.error(f"Data loading failed: {e}")
        return False
    except FeatureExtractionError as e:
        logger.error(f"Feature extraction failed: {e}")
        return False
    except ModelTrainingError as e:
        logger.error(f"Model training failed: {e}")
        return False
    except EvaluationError as e:
        logger.error(f"Evaluation failed: {e}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error in {func.__name__}: {e}")
        return False

def setup_signal_handlers(logger: logging.Logger):
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(sig, frame):
        logger.warning("Received interrupt signal. Saving checkpoints and exiting...")
        # Logic to save state could go here if global state exists
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def run_pipeline(config_path: Optional[str] = None):
    """
    Execute the full BlockPilot pipeline in the correct order:
    1. Load Config
    2. Sweep (Ground Truth) -> writes ground_truth.jsonl
    3. Feature Extraction -> reads from data, writes features.jsonl
    4. Join Data
    5. Train Models
    6. Evaluate & Report
    """
    logger = setup_logging("data/processed/pipeline.log")
    setup_signal_handlers(logger)

    logger.info("Loading configuration...")
    try:
        config = load_config(config_path)
    except Exception as e:
        logger.critical(f"Failed to load config: {e}")
        return False

    paths = config.paths
    paths.data_root.mkdir(parents=True, exist_ok=True)
    paths.processed_dir.mkdir(parents=True, exist_ok=True)
    paths.models_dir.mkdir(parents=True, exist_ok=True)

    # --- STEP 1: Ground Truth Generation (Sweep) ---
    # T012 / T014: Run exhaustive sweep.
    # CRITICAL: This MUST complete and write ground_truth.jsonl BEFORE features are extracted.
    logger.info("Starting Ground Truth Generation (Sweep)...")
    ground_truth_path = paths.processed_dir / "ground_truth.jsonl"
    
    if not safe_execute(
        run_sweep,
        config=config,
        output_path=str(ground_truth_path),
        logger=logger
    ):
        logger.error("Sweep failed. Cannot proceed to feature extraction.")
        return False

    if not ground_truth_path.exists():
        logger.error("Sweep completed but ground_truth.jsonl was not created.")
        return False
    
    logger.info(f"Ground Truth generated successfully at {ground_truth_path}")

    # --- STEP 2: Static Feature Extraction ---
    # T020 / T022: Extract features.
    # This step relies on the existence of the dataset, but logically in the pipeline
    # we ensure the sweep (which establishes the target B*) is done first.
    # Some implementations might run this in parallel on the raw data, but the 
    # orchestration here ensures the *order of operations* for the full run.
    logger.info("Starting Static Feature Extraction...")
    features_path = paths.processed_dir / "features.jsonl"
    
    if not safe_execute(
        run_feature_extraction,
        config=config,
        output_path=str(features_path),
        logger=logger
    ):
        logger.error("Feature extraction failed.")
        return False

    if not features_path.exists():
        logger.error("Feature extraction completed but features.jsonl was not created.")
        return False

    logger.info(f"Features extracted successfully at {features_path}")

    # --- STEP 3: Join Ground Truth and Features ---
    # T031: Join the datasets.
    logger.info("Joining Ground Truth and Features...")
    training_set_path = paths.processed_dir / "training_set.jsonl"
    
    try:
        # We assume run_feature_extraction and run_sweep tag samples with IDs
        # that allow a join. The join_utils handles the logic.
        join_ground_truth_and_features(
            ground_truth_path=str(ground_truth_path),
            features_path=str(features_path),
            output_path=str(training_set_path),
            logger=logger
        )
        if not training_set_path.exists():
            raise FileNotFoundError("Training set join failed to create output file.")
    except Exception as e:
        logger.error(f"Failed to join datasets: {e}")
        return False

    logger.info(f"Training set created at {training_set_path}")

    # --- STEP 4: Uncertainty Metrics (Optional but ordered) ---
    # T031a: Generate uncertainty data if configured.
    if config.training.get("generate_uncertainty", False):
        logger.info("Generating Uncertainty Metrics...")
        uncertainty_path = paths.processed_dir / "uncertainty_metrics.jsonl"
        # Assuming a function exists or is part of sweep/features logic
        # For now, we assume it's handled or skipped if not implemented in this specific task scope
        # but the order is maintained.
        # If T031a was implemented as a separate script, it would run here.
        pass

    # --- STEP 5: Model Training ---
    # T027: Train models.
    logger.info("Starting Model Training...")
    if not safe_execute(
        run_training,
        config=config,
        training_data_path=str(training_set_path),
        logger=logger
    ):
        logger.error("Model training failed.")
        return False

    logger.info("Model training completed.")

    # --- STEP 6: Evaluation and Reporting ---
    # T029 / T032: Evaluate and calculate correlations.
    logger.info("Starting Evaluation and Reporting...")
    if not safe_execute(
        evaluate_and_report,
        config=config,
        training_data_path=str(training_set_path),
        logger=logger
    ):
        logger.error("Evaluation failed.")
        return False

    logger.info("Pipeline completed successfully.")
    return True

def main():
    """Entry point for the pipeline."""
    config_path = os.getenv("LLMXIVE_CONFIG", "config.yaml")
    success = run_pipeline(config_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
