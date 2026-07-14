import logging
from pathlib import Path
from code.analysis.correlations import main as _correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    logger.log("correlation_main_runner_start")
    try:
        full_metrics, corr_results = _correlations_main()
        logger.log("correlation_main_runner_success", 
                   full_metrics_rows=len(full_metrics), 
                   corr_results_rows=len(corr_results))
    except Exception as e:
        logger.log("correlation_main_runner_error", message=str(e))
        raise

if __name__ == "__main__":
    main()
