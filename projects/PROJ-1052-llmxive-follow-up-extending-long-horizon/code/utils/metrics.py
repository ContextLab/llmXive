import logging
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def calculate_recovery_metrics(
    baseline_logs_path: str,
    injected_logs_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Calculate recovery success metrics, explicitly excluding unrecoverable errors
    (baseline failures) from the success rate calculation but logging them separately.

    Logic:
    1. Load baseline execution logs to identify which tasks failed at the baseline (clean) level.
       These are "unrecoverable errors" because the agent couldn't solve the task even without
       injected errors.
    2. Load injected execution logs (T015 output).
    3. Filter injected logs:
       - If a task_id is in the baseline failure set, mark it as 'unrecoverable' and exclude
         from the success rate denominator.
       - Otherwise, include it in the success rate calculation.
    4. Calculate:
       - Total injected tasks
       - Unrecoverable tasks (baseline failures)
       - Recoverable tasks (Total - Unrecoverable)
       - Successful recoveries (Injected success AND not unrecoverable)
       - Recovery Success Rate = Successful recoveries / Recoverable tasks
    5. Save a detailed CSV and a summary dictionary to the output path.

    Args:
        baseline_logs_path: Path to data/processed/baseline_execution_logs.csv
        injected_logs_path: Path to data/processed/injected_execution_logs.csv
        output_path: Path to save the metrics report (CSV or JSON)

    Returns:
        Dictionary containing the calculated metrics.
    """
    # Load baseline logs to find baseline failures
    try:
        baseline_df = pd.read_csv(baseline_logs_path)
    except FileNotFoundError:
        logger.error(f"Baseline logs not found at {baseline_logs_path}")
        raise

    # Identify baseline failures (success_status == False or 'failure')
    # Assuming success_status is a boolean or string 'success'/'failure'
    baseline_failures = set()
    for _, row in baseline_df.iterrows():
        task_id = row.get('task_id')
        success = row.get('success_status')
        # Normalize success check
        is_success = success is True or str(success).lower() == 'success'
        if not is_success and task_id:
            baseline_failures.add(task_id)

    logger.info(f"Identified {len(baseline_failures)} unrecoverable tasks (baseline failures).")

    # Load injected logs
    try:
        injected_df = pd.read_csv(injected_logs_path)
    except FileNotFoundError:
        logger.error(f"Injected logs not found at {injected_logs_path}")
        raise

    if injected_df.empty:
        logger.warning("Injected logs are empty. Returning zero metrics.")
        result = {
            'total_injected': 0,
            'unrecoverable_count': 0,
            'recoverable_count': 0,
            'successful_recoveries': 0,
            'recovery_success_rate': 0.0,
            'details': []
        }
        # Save empty result
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        injected_df.to_csv(output_path, index=False)
        return result

    # Process injected logs
    metrics_rows = []
    successful_recoveries = 0
    recoverable_count = 0

    for _, row in injected_df.iterrows():
        task_id = row.get('task_id')
        injected_success = row.get('success_status')
        is_injected_success = injected_success is True or str(injected_success).lower() == 'success'
        
        metric_entry = {
            'task_id': task_id,
            'is_baseline_failure': task_id in baseline_failures,
            'injected_success': is_injected_success,
            'status': 'unknown'
        }

        if task_id in baseline_failures:
            # This is an unrecoverable error
            metric_entry['status'] = 'unrecoverable'
            # Do NOT count in denominator
        else:
            # This is a recoverable task
            recoverable_count += 1
            if is_injected_success:
                successful_recoveries += 1
                metric_entry['status'] = 'recovered'
            else:
                metric_entry['status'] = 'failed_recovery'

        metrics_rows.append(metric_entry)

    total_injected = len(injected_df)
    unrecoverable_count = len(baseline_failures.intersection(set(injected_df['task_id'])))
    
    # Calculate rate only if there are recoverable tasks
    if recoverable_count > 0:
        recovery_success_rate = successful_recoveries / recoverable_count
    else:
        recovery_success_rate = 0.0

    # Prepare summary
    summary = {
        'total_injected': total_injected,
        'unrecoverable_count': unrecoverable_count,
        'recoverable_count': recoverable_count,
        'successful_recoveries': successful_recoveries,
        'recovery_success_rate': recovery_success_rate
    }

    # Create detailed DataFrame for output
    output_df = pd.DataFrame(metrics_rows)
    
    # Save detailed CSV
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Recovery metrics saved to {output_path}")
    logger.info(f"Total Injected: {total_injected}, Unrecoverable: {unrecoverable_count}, "
                f"Recoverable: {recoverable_count}, Success Rate: {recovery_success_rate:.4f}")

    return summary

def main():
    """Entry point for T016 metric calculation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate recovery metrics excluding baseline failures.")
    parser.add_argument("--baseline", type=str, default="data/processed/baseline_execution_logs.csv",
                        help="Path to baseline execution logs")
    parser.add_argument("--injected", type=str, default="data/processed/injected_execution_logs.csv",
                        help="Path to injected execution logs")
    parser.add_argument("--output", type=str, default="data/processed/recovery_metrics.csv",
                        help="Path to save metrics output")
    
    args = parser.parse_args()
    
    calculate_recovery_metrics(args.baseline, args.injected, args.output)
    print(f"Metrics calculation complete. Output: {args.output}")

if __name__ == "__main__":
    main()
