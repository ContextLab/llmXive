import os
import sys
import logging
import argparse
from analyzer import analyze_stability_trend, load_simulation_results, aggregate_results

def main():
    parser = argparse.ArgumentParser(description="Run stability analysis for statistical tests.")
    parser.add_argument('--input', type=str, default=None, help="Path to raw p-values CSV. Defaults to data/processed/raw_pvalues.csv")
    parser.add_argument('--output-csv', type=str, default="data/processed/stability_trend.csv", help="Output CSV path")
    parser.add_argument('--output-plot', type=str, default="data/processed/plots/stability_trend.png", help="Output plot path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        # Load and aggregate
        logger.info("Loading simulation results...")
        df = load_simulation_results(args.input)
        agg_df = aggregate_results(df)

        # Analyze
        logger.info("Performing stability trend analysis...")
        trend_df, stability_metric, is_robust = analyze_stability_trend(agg_df)

        # Export
        from analyzer import export_stability_results, plot_stability_trend
        export_stability_results(trend_df, stability_metric, is_robust, args.output_csv)
        plot_stability_trend(agg_df, trend_df, args.output_plot)

        logger.info(f"Analysis complete. Stability metric: {stability_metric:.6f}, Robust: {is_robust}")
        return 0

    except Exception as e:
        logger.error(f"Stability analysis failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
