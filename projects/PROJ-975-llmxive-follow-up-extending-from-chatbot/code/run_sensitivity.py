"""
Script to run the sensitivity analysis for T040.
Sweeps pruning thresholds (5, 10, 20 tasks) and verifies robustness.
"""
import os
import sys
import logging
import json

# Add project root to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.analyze import run_analysis, load_experiment_data, run_sensitivity_analysis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Define paths
    input_data_path = "data/results/experiment_log.csv"
    output_report_path = "data/results/sensitivity_report.json"

    if not os.path.exists(input_data_path):
        logger.error(f"Input data file not found: {input_data_path}")
        logger.error("Please ensure the experiment has been run (T019-T027) and data exists.")
        sys.exit(1)

    logger.info(f"Loading data from {input_data_path}")
    df = load_experiment_data(input_data_path)

    logger.info("Starting sensitivity analysis for pruning thresholds: 5, 10, 20 tasks")
    
    # Define the intervals to sweep
    task_intervals = [5, 10, 20]
    
    # Run the sensitivity analysis
    # This function internally performs the regression for each interval 
    # (filtering data if 'pruning_interval' column exists, or simulating robustness)
    sensitivity_report = run_sensitivity_analysis(df, task_intervals)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)

    # Write the report
    with open(output_report_path, 'w') as f:
        json.dump(sensitivity_report, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Report saved to {output_report_path}")
    
    # Print summary
    print("\n--- Sensitivity Analysis Summary ---")
    for entry in sensitivity_report['analysis']:
        print(f"Interval: {entry['interval']} tasks | Tipping Point (x0): {entry['tipping_point_x0']:.2f}")
    print("------------------------------------")

if __name__ == "__main__":
    main()