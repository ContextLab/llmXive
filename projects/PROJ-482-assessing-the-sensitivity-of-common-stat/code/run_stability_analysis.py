import os
import sys
import logging
import argparse
from analyzer import analyze_stability_trend

def main():
    parser = argparse.ArgumentParser(description="Run Stability Trend Analysis (T026b)")
    parser.add_argument("--input", type=str, default="data/processed/error_counts.csv",
                        help="Path to input error counts CSV")
    parser.add_argument("--output", type=str, default="data/processed/stability_trend.csv",
                        help="Path to output trend CSV")
    parser.add_argument("--plot", type=str, default="data/processed/plots/stability_trend.png",
                        help="Path to output plot PNG")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        result_df = analyze_stability_trend(
            input_filepath=args.input,
            output_filepath=args.output,
            plot_filepath=args.plot
        )
        print(f"Analysis complete. Results saved to {args.output}")
        print(f"Plot saved to {args.plot}")
        print(f"Stability verified: {result_df['stability_verified'].all()}")
    except Exception as e:
        logging.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
