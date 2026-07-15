"""
Script to run the stability trend analysis (T026b).
Loads raw p-values, calculates Type I error rates per sample size,
performs regression analysis, and generates plots.
"""
import os
import sys
import logging
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer import analyze_stability_trend

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run stability trend analysis (T026b)')
    parser.add_argument('--input', type=str, default='data/processed/raw_pvalues.csv',
                        help='Path to raw p-values CSV')
    parser.add_argument('--csv-output', type=str, default='data/processed/stability_trend.csv',
                        help='Path to save stability trend CSV')
    parser.add_argument('--plot-output', type=str, default='data/processed/plots/stability_trend.png',
                        help='Path to save the trend plot')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        logger.error("Please run the simulation pipeline first to generate raw_pvalues.csv")
        sys.exit(1)
    
    logger.info(f"Starting stability analysis with input: {args.input}")
    
    try:
        result_df = analyze_stability_trend(
            raw_input_path=args.input,
            csv_output_path=args.csv_output,
            plot_output_path=args.plot_output
        )
        
        if result_df.empty:
            logger.warning("Analysis returned empty results.")
        else:
            logger.info(f"Analysis complete. Results saved to {args.csv_output}")
            logger.info(f"Plots saved to {args.plot_output} (and variants)")
            logger.info(f"Summary:\n{result_df[['distribution', 'test_type', 'slope', 'r_squared', 'p_value_trend']]}")
            
    except Exception as e:
        logger.exception(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
