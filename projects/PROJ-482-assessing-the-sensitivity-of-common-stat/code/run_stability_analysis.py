import os
import sys
import logging
import argparse
from analyzer import analyze_stability_trend, load_simulation_results, aggregate_results

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run stability trend analysis on simulation results.")
    parser.add_argument("--input", type=str, default="data/processed/raw_pvalues.csv", help="Path to raw p-values CSV")
    parser.add_argument("--output-csv", type=str, default="data/processed/stability_trend.csv", help="Path to output trend CSV")
    parser.add_argument("--output-plot", type=str, default="data/processed/stability_trend.png", help="Path to output plot")
    args = parser.parse_args()

    logger.info(f"Starting stability analysis with input: {args.input}")
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    try:
        # Load and Aggregate
        df = load_simulation_results(args.input)
        agg_df = aggregate_results(df)
        
        # Analyze Trend
        analyze_stability_trend(
            aggregated_df=agg_df,
            output_csv=args.output_csv,
            plot_path=args.output_plot
        )
        
        logger.info("Stability analysis completed successfully.")
    except Exception as e:
        logger.error(f"Stability analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
