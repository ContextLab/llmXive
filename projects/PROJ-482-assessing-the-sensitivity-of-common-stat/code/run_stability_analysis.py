import os
import sys
import logging
import argparse
from analyzer import analyze_stability_trend, load_simulation_results, aggregate_results, plot_stability_trend, export_stability_results

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run stability analysis on simulation results")
    parser.add_argument('--input', type=str, default='data/processed/raw_pvalues.csv',
                        help='Path to raw p-values CSV')
    parser.add_argument('--output-csv', type=str, default='data/processed/stability_trend.csv',
                        help='Path for output CSV')
    parser.add_argument('--output-plot', type=str, default='data/processed/plots/stability_trend.png',
                        help='Path for output plot')
    parser.add_argument('--test', type=str, default='ttest',
                        help='Test type to analyze (ttest, anova, chisq)')
    parser.add_argument('--dist', type=str, default='normal',
                        help='Distribution type to analyze (normal, uniform, lognormal)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    logger.info(f"Loading data from {args.input}")
    df = load_simulation_results(args.input)
    
    logger.info("Aggregating results...")
    agg_df = aggregate_results(df)
    
    logger.info(f"Analyzing stability for {args.test} ({args.dist})...")
    result = analyze_stability_trend(agg_df, args.test, args.dist)
    
    logger.info(f"Result - Slope: {result.slope:.6f}, Robust: {result.robust}")
    
    logger.info(f"Saving plot to {args.output_plot}")
    plot_stability_trend(result, args.output_plot)
    
    logger.info(f"Saving CSV to {args.output_csv}")
    export_stability_results(result, args.output_csv)
    
    logger.info("Stability analysis complete.")

if __name__ == "__main__":
    main()
