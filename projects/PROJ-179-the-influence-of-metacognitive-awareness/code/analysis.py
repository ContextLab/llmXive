import os
import sys
import json
import logging
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import config safely; handle potential missing file gracefully
try:
    from config.env_config import load_config, setup_logging
except ImportError:
    # Fallback if config module is missing or broken
    def load_config():
        return {}
    def setup_logging(level=None):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)

def main():
    """
    Main entry point for the analysis pipeline.
    Executes the sequence: Download -> Validate -> Preprocess -> Correlation -> Bootstrap -> Regression -> Filter -> Robustness -> Report
    """
    # Initialize logging immediately to ensure we have a logger for the pipeline
    try:
        config = load_config()
        logger = setup_logging(config)
    except Exception as e:
        # Fallback to basic config if setup fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logger = logging.getLogger(__name__)
        logger.warning(f"Config setup failed ({e}), using default logging.")
    
    logger.info("Starting full analysis pipeline...")
    
    # 0. Validate Data Availability (T004)
    try:
        from data.validate_data_availability import main as validate_avail_main
        validate_avail_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Data availability check failed. Aborting pipeline.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Data availability check failed: {e}")
        sys.exit(1)

    # 1. Download Data (T005)
    try:
        from data.download import main as download_main
        download_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Data download failed. Aborting pipeline.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Data download failed: {e}")
        sys.exit(1)
    
    # 2. Validate Data (T006)
    try:
        from data.validate_data import main as validate_data_main
        validate_data_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Data validation failed. Aborting pipeline.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        sys.exit(1)

    # 3. Preprocess (T012) - Ensure this runs first to generate trial_data.csv
    try:
        from data.preprocess import main as preprocess_main
        preprocess_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Preprocessing failed. Aborting pipeline.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)
    
    # 4. Correlation Analysis (T014)
    try:
        from src.analysis.correlation import main as correlation_main
        correlation_main()
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        sys.exit(1)
    
    # 5. Bootstrap (T015)
    try:
        from src.analysis.bootstrap import main as bootstrap_main
        bootstrap_main()
    except Exception as e:
        logger.error(f"Bootstrap analysis failed: {e}")
        sys.exit(1)
    
    # 6. Regression (T020)
    try:
        from src.analysis.regression import main as regression_main
        regression_main()
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        sys.exit(1)
    
    # 7. Filter for Modality (T026)
    try:
        from src.analysis.filter import main as filter_main
        filter_main()
    except Exception as e:
        logger.error(f"Filter analysis failed: {e}")
        sys.exit(1)
    
    # 8. Robustness (T027)
    try:
        from src.analysis.robustness import main as robustness_main
        robustness_main()
    except Exception as e:
        logger.error(f"Robustness analysis failed: {e}")
        sys.exit(1)
    
    # 9. Generate Reports (T016, T022, T028)
    try:
        from src.report.generate import main as report_main
        report_main()
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)
    
    logger.info("Analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()