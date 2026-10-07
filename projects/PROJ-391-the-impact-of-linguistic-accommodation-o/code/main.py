"""
Main entry point for the Linguistic Accommodation pipeline.
Orchestrates the workflow: Data Ingestion -> Emotion Mapping -> Statistical Analysis.
Includes contract validation hooks at stage boundaries.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow relative imports if run as script
# Note: In a proper package setup, this would be handled by PYTHONPATH or installation.
# We ensure imports work relative to the 'code' directory structure.
if __name__ == "__main__":
    # If running python code/main.py, the current dir is code/
    # If running python -m code.main, we need to adjust
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

from utils import normalize_text, clean_text, jaccard_similarity, is_valid_text
from data.ingestion import (
    load_schema,
    validate_dataframe,
    download_daily_dialog_test,
    load_daily_dialog_test,
    preprocess_dialogue_pair,
    compute_accommodation_metrics,
    main as ingestion_main
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
# Assuming main.py is at code/main.py, project root is parent of code/
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "pipeline_config.json"
SCHEMA_INGESTION = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
SCHEMA_OUTPUT = PROJECT_ROOT / "contracts" / "output.schema.yaml"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load pipeline configuration from a JSON file.
    Defaults to config/pipeline_config.json.
    """
    path = config_path or CONFIG_PATH
    if not path.exists():
        logger.warning(f"Config file not found at {path}. Using defaults.")
        return {
            "data_source": "daily_dialog",
            "split": "test",
            "streaming": True,
            "random_seed": 42,
            "bootstrap_iterations": 1000,
            "target_ci_width": 0.05,
            "max_bootstrap_iterations": 5000
        }
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise


def run_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute the full research pipeline:
    1. Ingest and preprocess DailyDialog data (T016-T022)
    2. Map emotions to intensity scores (T026-T032)
    3. Perform statistical analysis (T036-T047)
    
    Returns a summary of the execution.
    """
    if config is None:
        config = load_config()
    
    logger.info("Starting Pipeline Execution")
    
    # Ensure output directories exist
    for dir_path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, OUTPUTS_DIR, REPORTS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    results = {
        "status": "success",
        "stages": {},
        "errors": []
    }
    
    # --- Stage 1: Data Ingestion (T016-T022) ---
    logger.info("Stage 1: Data Ingestion")
    try:
        # We call the main function from ingestion.py which handles download, load, preprocess, and save
        # We pass the config to override defaults if necessary
        # Note: ingestion_main() currently expects no args, but we can adapt or call internal functions
        # For now, we rely on ingestion_main() to use defaults or read its own config if implemented.
        # To be robust, we might need to refactor ingestion.py to accept args, but per constraints we extend.
        # We will assume ingestion_main() handles the full flow for T016-T021.
        # We need to ensure T022 (schema validation) is called.
        
        # Let's call the specific functions to ensure T022 is triggered if ingestion_main doesn't cover it fully
        # Or we assume ingestion_main covers the whole flow.
        # Given the task T010 is a skeleton, we assume ingestion_main() is the entry point for Stage 1.
        # We will call ingestion_main() and assume it writes to data/processed/accommodation_metrics.csv
        
        # Since ingestion_main() might not take args, we rely on it using defaults or reading a config.
        # To be safe, we'll just call it. If it fails, we catch it.
        ingestion_main() 
        
        # Validate output against schema (T022)
        if SCHEMA_INGESTION.exists():
            schema = load_schema(SCHEMA_INGESTION)
            input_path = DATA_PROCESSED_DIR / "accommodation_metrics.csv"
            if input_path.exists():
                import pandas as pd
                df = pd.read_csv(input_path)
                is_valid, errors = validate_dataframe(df, schema)
                if not is_valid:
                    logger.error(f"Ingestion output validation failed: {errors}")
                    results["errors"].extend(errors)
                    results["stages"]["ingestion"] = {"status": "failed", "errors": errors}
                else:
                    results["stages"]["ingestion"] = {"status": "success", "rows": len(df)}
            else:
                raise FileNotFoundError(f"Ingestion output not found at {input_path}")
        else:
            logger.warning(f"Schema file not found at {SCHEMA_INGESTION}. Skipping validation.")
            
    except Exception as e:
        logger.error(f"Stage 1 (Ingestion) failed: {e}")
        results["stages"]["ingestion"] = {"status": "failed", "error": str(e)}
        results["status"] = "failed"
        # In a real pipeline, we might stop here. For now, we log and continue if possible.
        return results # Stop on critical failure in Phase 3 prerequisite

    # --- Stage 2: Emotion Mapping (T026-T032) ---
    logger.info("Stage 2: Emotion Mapping")
    try:
        # Placeholder for future implementation of emotion_mapping.py
        # This stage depends on T021 output
        input_path = DATA_PROCESSED_DIR / "accommodation_metrics.csv"
        if not input_path.exists():
            raise FileNotFoundError("Accommodation metrics not found. Run Stage 1 first.")
        
        # TODO: Import and run emotion mapping logic when T026-T032 are implemented
        # from analysis.emotion_mapping import run_emotion_mapping
        # final_df = run_emotion_mapping(input_path)
        
        logger.info("Stage 2 (Emotion Mapping) is a placeholder. Implementation pending T026-T032.")
        results["stages"]["emotion_mapping"] = {"status": "skipped", "reason": "Implementation pending"}
        
    except Exception as e:
        logger.error(f"Stage 2 (Emotion Mapping) failed: {e}")
        results["stages"]["emotion_mapping"] = {"status": "failed", "error": str(e)}
        results["status"] = "failed"

    # --- Stage 3: Statistical Analysis (T036-T047) ---
    logger.info("Stage 3: Statistical Analysis")
    try:
        # Placeholder for future implementation of stats.py and viz.py
        final_dataset_path = DATA_PROCESSED_DIR / "final_dataset.csv"
        if not final_dataset_path.exists():
            # If Stage 2 was skipped, try to use Stage 1 output if it has enough fields
            # But per spec, Stage 3 depends on Stage 2 output (final_dataset.csv)
            logger.warning("Final dataset not found. Stage 3 requires T031 completion.")
            results["stages"]["statistical_analysis"] = {"status": "skipped", "reason": "Final dataset missing"}
        else:
            # TODO: Import and run stats logic when T036-T047 are implemented
            # from analysis.stats import run_full_analysis
            # report = run_full_analysis(final_dataset_path)
            logger.info("Stage 3 (Statistical Analysis) is a placeholder. Implementation pending T036-T047.")
            results["stages"]["statistical_analysis"] = {"status": "skipped", "reason": "Implementation pending"}

    except Exception as e:
        logger.error(f"Stage 3 (Statistical Analysis) failed: {e}")
        results["stages"]["statistical_analysis"] = {"status": "failed", "error": str(e)}
        results["status"] = "failed"

    logger.info("Pipeline Execution Finished")
    return results


def main():
    """
    CLI entry point.
    Usage: python main.py [--config <path>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Linguistic Accommodation Pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration JSON file"
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config) if args.config else None
    
    try:
        results = run_pipeline(config_path)
        
        # Print summary
        print("\n--- Pipeline Execution Summary ---")
        for stage, res in results.get("stages", {}).items():
            status = res.get("status", "unknown")
            print(f"{stage}: {status}")
            if status == "failed":
                print(f"  Error: {res.get('error', res.get('errors', 'Unknown'))}")
        
        if results["status"] == "failed":
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.critical(f"Pipeline crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()