from pathlib import Path
from config.settings import get_settings
from analysis.data_cleaner import DataCleaner
from analysis.stat_utils import generate_metrics_summary
from analysis.visualizer import Visualizer
from analysis.report_generator import ReportGenerator
from utils.logger import get_logger
import sys
import argparse

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run the full analysis pipeline")
    parser.add_argument("--input", type=str, help="Path to raw sessions CSV (optional if using default)")
    parser.add_argument("--output", type=str, help="Path to metrics summary CSV (optional if using default)")
    args = parser.parse_args()
    
    settings = get_settings()
    project_root = Path(__file__).resolve().parent.parent
    
    # Default paths
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    figures_dir = project_root / "figures"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    input_csv = args.input or str(processed_dir / "cleaned_sessions.csv")
    output_csv = args.output or str(processed_dir / "metrics_summary.csv")
    
    logger.info("Starting analysis pipeline")
    
    # 1. Data Cleaning
    # If input is the cleaned file, we assume cleaning is done. 
    # If input points to raw, we might need to run cleaner.
    # For this script, we assume input is the cleaned data ready for stats.
    if not Path(input_csv).exists():
        # Try to run cleaner if raw data exists
        logger.info(f"Input {input_csv} not found. Attempting to clean raw data...")
        cleaner = DataCleaner(raw_dir, processed_dir)
        input_csv = cleaner.run_pipeline()
        
    if not Path(input_csv).exists():
        logger.error(f"Cleaned data not found at {input_csv}. Aborting.")
        sys.exit(1)
    
    # 2. Statistical Analysis
    logger.info(f"Running statistical analysis on {input_csv}")
    generate_metrics_summary(input_csv, output_csv)
    
    # 3. Visualization
    logger.info("Generating visualizations")
    visualizer = Visualizer(processed_dir, figures_dir)
    visualizer.run_all_plots()
    
    # 4. Report Generation
    logger.info("Generating report")
    report_gen = ReportGenerator(processed_dir, figures_dir)
    report_gen.generate_report()
    
    logger.info("Analysis pipeline completed successfully")

if __name__ == "__main__":
    main()
