"""
Standalone runner for the analysis pipeline to ensure T023b outputs are generated.
This script is invoked by the quickstart run-book to produce the required CSVs.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.correlations import main as run_correlation_analysis
from code.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def main():
    setup_logging()
    logger.log("run_analysis", step="start")
    
    try:
        merged_df, corr_results = run_correlation_analysis()
        logger.log("run_analysis", step="success", 
                   full_metrics_count=len(merged_df), 
                   correlations_count=len(corr_results))
        print(f"Analysis complete. Output files written to {Path('data/analysis').resolve()}")
    except Exception as e:
        logger.log("run_analysis", step="failed", error=str(e))
        print(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()