import argparse
import logging
import sys
from pathlib import Path
from utils.logging import setup_logging, get_logger
from config import get_project_root, ensure_directories
from stimuli.process import process_stimuli_batch
from data.load import load_response_logs, generate_synthetic_response_logs
from data.process import aggregate_d_scores, save_aggregated_scores
from analysis.permutation import run_permutation_test, run_post_hoc_power_analysis, run_sensitivity_analysis
from analysis.results import save_json_results
from viz.plot import plot_boxplot
import pandas as pd

logger = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the full research pipeline.")
    parser.add_argument("--null-effect", action="store_true", help="Generate synthetic data for CI.")
    parser.add_argument("--stages", nargs="+", default=["all"], help="Stages to run: stimuli, data, analysis, viz, all.")
    return parser.parse_args()

def main() -> int:
    """Main entry point for the pipeline."""
    args = parse_args()
    setup_logging(level=logging.INFO)
    logger.info("Starting llmXive research pipeline...")
    
    ensure_directories()
    
    try:
        # Stage 1: Stimuli Processing
        if "all" in args.stages or "stimuli" in args.stages:
            logger.info("Stage 1: Processing stimuli...")
            process_stimuli_batch()
        
        # Stage 2: Data Loading and Aggregation
        if "all" in args.stages or "data" in args.stages:
            logger.info("Stage 2: Loading and aggregating data...")
            if args.null_effect:
                generate_synthetic_response_logs(Path(get_project_root()) / "data" / "raw" / "responses" / "synthetic.csv")
            
            raw_df = load_response_logs()
            aggregated_df = aggregate_d_scores(raw_df, min_valid_trials=10)
            save_aggregated_scores(aggregated_df)
            
            # Join with complexity scores if available
            complexity_path = get_project_root() / "data" / "processed" / "complexity_scores.csv"
            if complexity_path.exists():
                complexity_df = pd.read_csv(complexity_path)
                # Simple join logic (assumes mapping exists)
                # In reality, this would require a mapping file between images and participants
                logger.info("Complexity scores found. Note: Mapping logic requires implementation.")
        
        # Stage 3: Analysis
        if "all" in args.stages or "analysis" in args.stages:
            logger.info("Stage 3: Running analysis...")
            data_path = get_project_root() / "data" / "processed" / "aggregated_d_scores.csv"
            if data_path.exists():
                df = pd.read_csv(data_path)
                valid_df = df[df["status"] == "valid"]
                
                # Group by complexity (requires joined data, simplified here)
                # This assumes the data has been enriched with complexity categories
                if "complexity_category" in valid_df.columns:
                    low = valid_df[valid_df["complexity_category"] == "Low"]["d_score"].dropna().tolist()
                    high = valid_df[valid_df["complexity_category"] == "High"]["d_score"].dropna().tolist()
                    
                    if low and high:
                        d_scores = {"Low": low, "High": high}
                        perm_results = run_permutation_test(d_scores)
                        power_results = run_post_hoc_power_analysis(d_scores)
                        sensitivity_results = run_sensitivity_analysis(d_scores)
                        
                        save_json_results(perm_results, "permutation_results.json")
                        save_json_results(power_results, "power_analysis.json")
                        save_json_results(sensitivity_results, "sensitivity_results.json")
                    else:
                        logger.warning("Insufficient data for analysis.")
                else:
                    logger.warning("Complexity category column missing. Skipping analysis.")
            else:
                logger.warning("Aggregated data not found. Skipping analysis.")
        
        # Stage 4: Visualization
        if "all" in args.stages or "viz" in args.stages:
            logger.info("Stage 4: Generating plots...")
            data_path = get_project_root() / "data" / "processed" / "aggregated_d_scores.csv"
            if data_path.exists():
                df = pd.read_csv(data_path)
                if "complexity_category" in df.columns:
                    plot_boxplot(df, "complexity_category", "d_score")
                else:
                    logger.warning("Cannot plot: complexity_category missing.")
            else:
                logger.warning("Cannot plot: data not found.")
        
        logger.info("Pipeline completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
