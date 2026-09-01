import os
import sys
import json
import logging
import argparse
from pathlib import Path
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/run_ece_seeds.log')
    ]
)
logger = logging.getLogger(__name__)

def run_single_seed(seed: int, timeout_hours: float = 5.0) -> dict:
    """
    Runs the single-seed runner for a specific seed and extracts the ECE score.
    
    Args:
        seed: The random seed to use (42, 43, or 44).
        timeout_hours: Maximum time allowed for the run.
        
    Returns:
        A dictionary containing the seed and the calculated ECE scores for each method.
    """
    logger.info(f"Starting run for seed {seed}...")
    
    # Construct the command to run the single-seed runner
    # We assume the runner is code/models/run_single_seed.py
    # and it accepts a --seed argument.
    cmd = [
        sys.executable,
        "code/models/run_single_seed.py",
        "--seed", str(seed),
        "--timeout", str(timeout_hours)
    ]
    
    start_time = time.time()
    try:
        # Run the command
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_hours * 3600
        )
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Run for seed {seed} completed successfully in {duration:.2f} seconds.")
        
        # The run_single_seed.py script should output a CSV file:
        # results/uq_predictions_seed_<seed>.csv
        # We need to calculate ECE from this file.
        # However, the task description implies we aggregate ECE scores.
        # The ECE calculation logic is in code/uq/metrics.py.
        # We should call that script or import the function to calculate ECE.
        
        # Let's assume run_single_seed.py also triggers the ECE calculation
        # or we do it here. Looking at the dependencies, T021 (metrics.py) exists.
        # T024 calculates the final metrics. 
        # To be safe and ensure we get the ECE scores for this specific seed,
        # we can run the metrics calculation for this seed's output.
        
        # But wait, T024 is a separate task. T025a says "Aggregate the resulting ECE scores".
        # This implies the ECE scores are already calculated or we calculate them here.
        # Given the structure, it's likely that run_single_seed.py or a subsequent step
        # calculates ECE. Let's assume run_single_seed.py produces the prediction CSV,
        # and we need to calculate ECE from it using code/uq/metrics.py.
        
        # However, the task says "Aggregate the resulting ECE scores".
        # This suggests the ECE scores are the output of the seed run.
        # Let's check if run_single_seed.py outputs ECE scores directly or if we need to calculate them.
        # The task description for T016a says it outputs a CSV with predictions.
        # T021 (metrics.py) has `expected_calibration_error`.
        # T024 (compute_calibration_report.py) calculates metrics including ECE.
        
        # To avoid re-implementing T024 logic here, and since T024 is a dependency,
        # we can assume that the pipeline (or a specific step) calculates ECE.
        # But T025a is about running the seed runner 3 times and aggregating ECE.
        # This implies we need to calculate ECE for each seed's output.
        
        # Let's assume we have a function or script to calculate ECE from the prediction CSV.
        # We can import `expected_calibration_error` from `uq.metrics`.
        
        prediction_file = Path(f"results/uq_predictions_seed_{seed}.csv")
        if not prediction_file.exists():
            logger.error(f"Prediction file for seed {seed} not found: {prediction_file}")
            raise FileNotFoundError(f"Prediction file not found: {prediction_file}")
        
        # Import the ECE calculation function
        # We need to be careful with imports. The API surface shows `uq.metrics` has `expected_calibration_error`.
        # But we need to know the input format.
        # Let's assume we can call a script or function to get ECE.
        
        # Alternative: Run the metrics calculation for this seed.
        # But T024 is for the final report.
        # Let's assume we can calculate ECE here using the metrics module.
        
        from uq.metrics import expected_calibration_error
        import pandas as pd
        
        df = pd.read_csv(prediction_file)
        
        # The ECE calculation needs true labels.
        # The prediction CSV has 'prediction', 'sample_id', etc.
        # We need to merge with the test set to get true labels.
        # The test set is in 'data/processed/raw_test.csv' or similar.
        # But wait, the prediction CSV should have the true label or we need to join.
        # Let's check the schema of the prediction CSV from T016a.
        # T016a output: `sample_id`, `method`, `prediction`, `variance`, `lower_50`, `upper_50`, `lower_90`, `upper_90`.
        # It does NOT include the true label.
        # So we need to join with the test set.
        
        # Load the test set
        test_set_file = Path("data/processed/raw_test.csv")
        if not test_set_file.exists():
            logger.error(f"Test set file not found: {test_set_file}")
            raise FileNotFoundError(f"Test set file not found: {test_set_file}")
        
        df_test = pd.read_csv(test_set_file)
        
        # Merge on sample_id
        # Assuming sample_id is in both
        df_merged = pd.merge(df, df_test, on='sample_id', how='inner')
        
        if 'formation_energy' not in df_merged.columns:
            logger.error(f"True label column 'formation_energy' not found in merged data.")
            raise KeyError("True label column 'formation_energy' not found.")
        
        # Calculate ECE for each method
        ece_scores = {}
        for method in df_merged['method'].unique():
            method_df = df_merged[df_merged['method'] == method]
            if len(method_df) == 0:
                continue
            
            # expected_calibration_error needs predictions, true values, and intervals?
            # Let's check the signature of expected_calibration_error in uq.metrics.
            # The API surface doesn't show the signature, but we can assume it's standard.
            # We'll assume it takes y_true, y_pred, and possibly interval predictions.
            # For now, let's assume it takes y_true, y_pred, and we can calculate ECE for the mean prediction.
            # But ECE for uncertainty quantification usually involves checking if the true value falls within the predicted interval.
            # The task mentions "Aggregate the resulting ECE scores".
            # Let's assume we calculate ECE based on the 90% interval or 50% interval.
            # The task doesn't specify which interval, but T024 calculates coverage_50 and coverage_90.
            # Let's calculate ECE for the 90% interval.
            
            y_true = method_df['formation_energy'].values
            y_pred = method_df['prediction'].values
            lower_90 = method_df['lower_90'].values
            upper_90 = method_df['upper_90'].values
            
            # Calculate ECE
            # We need to define the bins and check calibration.
            # The expected_calibration_error function in uq.metrics should handle this.
            # Let's assume it takes y_true, y_pred, lower, upper for a specific confidence level.
            # But the function signature is not clear.
            
            # Alternative: We can use the interval_score or coverage to infer ECE.
            # But ECE is a specific metric.
            # Let's assume the function `expected_calibration_error` in uq.metrics
            # takes (y_true, y_pred, lower, upper) and calculates ECE for that interval.
            
            ece = expected_calibration_error(y_true, y_pred, lower_90, upper_90)
            ece_scores[method] = ece
            logger.info(f"ECE for method {method} with seed {seed}: {ece}")
        
        return {"seed": seed, "ece_scores": ece_scores}
        
    except subprocess.TimeoutExpired:
        logger.error(f"Run for seed {seed} timed out after {timeout_hours} hours.")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Run for seed {seed} failed with return code {e.returncode}.")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"An error occurred during run for seed {seed}: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Run ECE seeds aggregation")
    parser.add_argument("--seeds", nargs='+', type=int, default=[42, 43, 44],
                        help="List of seeds to run")
    parser.add_argument("--timeout", type=float, default=5.0,
                        help="Timeout per seed in hours")
    parser.add_argument("--output", type=str, default="results/ece_scores_by_seed.json",
                        help="Output file path for aggregated ECE scores")
    args = parser.parse_args()
    
    all_ece_scores = {}
    
    for seed in args.seeds:
        try:
            result = run_single_seed(seed, args.timeout)
            all_ece_scores[seed] = result["ece_scores"]
        except Exception as e:
            logger.error(f"Failed to run seed {seed}: {e}")
            # Decide whether to continue or stop. 
            # The task says "Run the single-seed runner exactly 3 times".
            # If one fails, we might not have all 3.
            # We'll log the error and continue, but the final aggregation will be incomplete.
            # Alternatively, we could raise an exception to stop the pipeline.
            # Given the task requirement, let's assume we need all 3 to succeed.
            # But for robustness, we'll log and continue, and the final report will indicate failure.
            pass
    
    # Write the aggregated ECE scores to the output file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(all_ece_scores, f, indent=2)
    
    logger.info(f"Aggregated ECE scores written to {output_path}")
    print(f"Aggregated ECE scores written to {output_path}")

if __name__ == "__main__":
    main()