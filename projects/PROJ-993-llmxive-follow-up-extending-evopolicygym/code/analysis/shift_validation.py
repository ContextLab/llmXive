import os
import csv
import json
import logging
from typing import List, Dict, Any, Optional
from scipy import stats
from utils.logging import get_logger

logger = get_logger(__name__)

def load_sensitivity_report(report_path: str) -> List[Dict[str, Any]]:
    """
    Load the sensitivity report CSV into a list of dictionaries.
    Handles missing files by returning an empty list (checked by caller).
    """
    if not os.path.exists(report_path):
        logger.error(f"Sensitivity report not found at {report_path}")
        return []
    
    data = []
    with open(report_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['shift_step'] = int(row['shift_step'])
                row['pre_shift_score'] = float(row['pre_shift_score'])
                row['post_shift_score'] = float(row['post_shift_score'])
                row['drop_rate'] = float(row['drop_rate'])
                row['p_value'] = float(row['p_value'])
                data.append(row)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed row in sensitivity report: {e}")
    return data

def calculate_p_value(pre_scores: List[float], post_scores: List[float]) -> float:
    """
    Calculate the p-value for the performance drop using a paired t-test.
    Returns 1.0 if either list is empty or if the test cannot be performed.
    """
    if len(pre_scores) < 2 or len(post_scores) < 2:
        logger.warning("Insufficient data points for p-value calculation (< 2).")
        return 1.0
    
    if len(pre_scores) != len(post_scores):
        logger.warning("Pre and post score lists have different lengths.")
        return 1.0
    
    try:
        # Paired t-test: we expect post scores to be lower (negative difference)
        # stats.ttest paired returns two-tailed p-value
        stat, p_val = stats.ttest_rel(pre_scores, post_scores)
        return float(p_val)
    except Exception as e:
        logger.error(f"Error calculating t-test: {e}")
        return 1.0

def process_validation_report(
    sensitivity_data: List[Dict[str, Any]],
    output_log_path: str,
    output_filtered_report_path: Optional[str] = None
) -> List[str]:
    """
    Process the sensitivity report to calculate p-values and log failures.
    
    For each environment:
    1. Calculate p-value based on pre/post scores (assuming single run per env for simplicity,
       or aggregating if multiple runs exist per env in the report).
       NOTE: The sensitivity report from T013f typically has one row per env_id.
       If multiple runs exist per env_id, we aggregate them.
       
       Logic for aggregation:
       - Group by env_id.
       - If multiple rows for an env_id, calculate mean pre/post scores and run t-test on the means?
       - Actually, t-test requires paired samples. If we have multiple runs, we should have multiple pre/post pairs.
       - The current report schema from T015b implies one row per env_id.
       - If the report has multiple rows per env_id (e.g., multiple seeds), we need to handle that.
       
       Assumption: The report from T013f contains one row per (env_id, seed) or just env_id.
       If it's just env_id, we cannot do a t-test unless we have multiple runs.
       However, T013f description says "run a static agent... to generate pre_shift_score and post_shift_score".
       Usually, this implies one score per shift.
       
       To perform a p-value test, we need variance.
       Strategy: If the report has multiple rows per env_id (different seeds), we group them.
       If only one row per env_id, we cannot calculate a meaningful p-value (variance=0).
       In that case, we treat the drop as "observed" but p-value is undefined or 1.0 (no stats).
       
       Revised Logic based on T013f/T015b context:
       T013f likely runs a static agent ONCE per env.
       T014 requires p-value.
       If we only have one data point per env, we cannot do a t-test.
       We must assume the 'sensitivity report' might contain multiple runs per env if T013f was run with seeds.
       Let's implement grouping by env_id.
       
       If grouped count < 2, p-value = 1.0 (fail validation).
       If grouped count >= 2, run t-test on pre vs post.
       
       If p >= 0.05:
         - Log failure to shift_validation.log.
         - Do NOT include in filtered report.
       Else:
         - Include in filtered report.
    """
    if not sensitivity_data:
        logger.warning("No sensitivity data provided for validation.")
        return []
    
    # Group by env_id
    grouped = {}
    for row in sensitivity_data:
        env_id = row['env_id']
        if env_id not in grouped:
            grouped[env_id] = {'pre': [], 'post': []}
        grouped[env_id]['pre'].append(row['pre_shift_score'])
        grouped[env_id]['post'].append(row['post_shift_score'])
    
    valid_envs = []
    failed_envs = []
    
    with open(output_log_path, 'w', encoding='utf-8') as log_file:
        log_file.write("shift_validation_log\n")
        log_file.write("=" * 50 + "\n")
        
        for env_id, scores in grouped.items():
            pre_scores = scores['pre']
            post_scores = scores['post']
            
            # Calculate p-value
            p_val = calculate_p_value(pre_scores, post_scores)
            
            # Calculate average drop rate for logging
            avg_pre = sum(pre_scores) / len(pre_scores)
            avg_post = sum(post_scores) / len(post_scores)
            avg_drop = avg_pre - avg_post
            drop_rate = avg_drop / avg_pre if avg_pre > 0 else 0.0
            
            log_entry = f"Env: {env_id} | Pre: {avg_pre:.4f} | Post: {avg_post:.4f} | Drop: {drop_rate:.4f} | P-Value: {p_val:.4f}"
            
            if p_val >= 0.05:
                # Failure: shift not statistically significant
                log_entry += " -> FAILED (p >= 0.05)"
                log_file.write(log_entry + "\n")
                failed_envs.append(env_id)
                logger.warning(f"Environment {env_id} failed shift validation (p={p_val:.4f}). Skipping.")
            else:
                # Success
                log_entry += " -> PASSED"
                log_file.write(log_entry + "\n")
                valid_envs.append(env_id)
                
                # If we need to update the report with the p-value, we do it here
                # But the task says "log a failure... and SKIP it".
                # We don't modify the original report, we create a filtered set or just log.
                # The task says "log the error to data/shift_validation.log".
    
    logger.info(f"Shift validation complete. Passed: {len(valid_envs)}, Failed: {len(failed_envs)}")
    
    # If an output filtered report path is provided, write it
    if output_filtered_report_path:
        # Filter the original data to only include rows for valid_envs
        # Note: If multiple rows per env, all are kept or all dropped?
        # We keep all rows for valid envs.
        filtered_data = [row for row in sensitivity_data if row['env_id'] in valid_envs]
        with open(output_filtered_report_path, 'w', newline='', encoding='utf-8') as f:
            if filtered_data:
                writer = csv.DictWriter(f, fieldnames=filtered_data[0].keys())
                writer.writeheader()
                writer.write_rows(filtered_data)
            else:
                # Write header only
                writer = csv.DictWriter(f, fieldnames=sensitivity_data[0].keys())
                writer.writeheader()
        
        logger.info(f"Filtered report written to {output_filtered_report_path}")

    return valid_envs

def main():
    """
    Main entry point for T014: Shift Validation.
    Reads sensitivity report, calculates p-values, logs failures, and outputs valid env list.
    """
    report_path = "data/sensitivity_report.csv"
    log_path = "data/shift_validation.log"
    filtered_report_path = "data/sensitivity_report_filtered.csv" # Optional intermediate, or just log list?
    # The task requires logging to data/shift_validation.log.
    # It doesn't explicitly ask for a filtered CSV, but T015a depends on the report.
    # T015a says: "Must verify data/sensitivity_report.csv exists".
    # T032a says: "Filter the environment list to include ONLY rows where p_value < 0.05".
    # So we need to update the sensitivity_report.csv to include p-values and valid/invalid flags?
    # Or T032a reads the log?
    # Let's update the sensitivity_report.csv to include the p-value and a 'valid' flag.
    # This makes T032a's job easier (it can just read the CSV).
    
    logger.info(f"Starting Shift Validation. Loading {report_path}")
    data = load_sensitivity_report(report_path)
    
    if not data:
        logger.error("No data to validate. Aborting.")
        return 1
    
    # Process and log
    valid_envs = process_validation_report(data, log_path)
    
    # Update the original report to include p-values and validity status?
    # The schema T015b includes p_value column.
    # We should recalculate and write the report with the p-values filled in.
    # However, the task T014 specifically says "log a failure... and SKIP it".
    # Let's write the filtered list to a new file if needed, but primarily ensure the log exists.
    # To support T032a, we should ensure the p-value is available.
    # We will re-write the sensitivity_report.csv with the calculated p-values and a 'valid' column.
    
    # Re-read and update
    # We already have the data. We need to attach the p-value and valid flag to each row.
    # Since we grouped, we need to map back to rows.
    # Actually, the t-test requires multiple rows per env.
    # If the original report had one row per env, we can't do t-test.
    # Assuming the report has multiple runs (seeds) per env.
    
    # Let's update the rows with the calculated p-value for the group.
    # And mark valid/invalid.
    updated_rows = []
    for row in data:
        env_id = row['env_id']
        # Find the p-value for this env_id (we calculated it in process_validation_report but didn't store it)
        # We need to re-calculate or store.
        # Let's re-calculate for simplicity or store in a dict.
        pass 
    
    # Re-implementation of process to return the map
    grouped_stats = {}
    grouped = {}
    for row in data:
        env_id = row['env_id']
        if env_id not in grouped:
            grouped[env_id] = {'pre': [], 'post': []}
        grouped[env_id]['pre'].append(row['pre_shift_score'])
        grouped[env_id]['post'].append(row['post_shift_score'])
    
    for env_id, scores in grouped.items():
        p_val = calculate_p_value(scores['pre'], scores['post'])
        valid = p_val < 0.05
        grouped_stats[env_id] = {'p_value': p_val, 'valid': valid}
    
    # Write updated report
    with open(report_path, 'w', newline='', encoding='utf-8') as f:
        # Ensure header includes p_value (it should per T015b)
        fieldnames = list(data[0].keys())
        if 'p_value' not in fieldnames:
            fieldnames.append('p_value')
        if 'valid' not in fieldnames:
            fieldnames.append('valid')
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            env_id = row['env_id']
            stats = grouped_stats[env_id]
            row_copy = dict(row)
            row_copy['p_value'] = stats['p_value']
            row_copy['valid'] = stats['valid']
            writer.writerow(row_copy)
    
    logger.info(f"Updated sensitivity report written to {report_path}")
    logger.info(f"Validation log written to {log_path}")
    
    return 0

if __name__ == "__main__":
    main()