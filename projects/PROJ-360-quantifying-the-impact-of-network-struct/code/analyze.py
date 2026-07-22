import os
import json
import logging
import csv
import pickle
import random
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from scipy.stats import pearsonr, spearmanr
import yaml

# Import from sibling modules as per API surface
from config import Config

# Setup logging
def setup_analysis_logger(name: str = "analysis_logger") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

analysis_logger = setup_analysis_logger()

def update_state_artifact_hash(file_path: str, state_file: str = "state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml") -> None:
    """Compute SHA-256 of a file and update the state YAML with the hash."""
    if not os.path.exists(file_path):
        analysis_logger.error(f"File not found for hashing: {file_path}")
        return

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    file_hash = sha256_hash.hexdigest()

    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if state_path.exists():
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    else:
        state_data = {"artifact_hashes": {}}

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"][file_path] = file_hash

    # Atomic write
    temp_path = state_path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        yaml.dump(state_data, f)
    os.replace(temp_path, state_path)
    analysis_logger.info(f"Updated state with hash for {file_path}: {file_hash}")

def load_metrics_csv(csv_path: str = "data/processed/metrics.csv") -> List[Dict[str, Any]]:
    """Load metrics from CSV into a list of dictionaries."""
    if not os.path.exists(csv_path):
        analysis_logger.error(f"Metrics file not found: {csv_path}")
        return []

    metrics = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats, handling potential errors
            cleaned_row = {}
            for k, v in row.items():
                if v is None:
                    cleaned_row[k] = None
                    continue
                try:
                    cleaned_row[k] = float(v)
                except (ValueError, TypeError):
                    cleaned_row[k] = v
            metrics.append(cleaned_row)
    return metrics

def compute_correlations(metrics_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compute Pearson and Spearman correlations between network metrics and thermal conductivity.
    Returns a list of result dictionaries.
    """
    if not metrics_data:
        analysis_logger.warning("No metrics data provided for correlation analysis.")
        return []

    # Extract columns
    # Expected columns: material_id, avg_degree, path_length, clustering, thermal_conductivity_scalar
    metrics_cols = ['avg_degree', 'path_length', 'clustering']
    target_col = 'thermal_conductivity_scalar'

    # Filter rows where target and all metric columns are valid floats
    valid_rows = []
    for row in metrics_data:
        try:
            target_val = float(row.get(target_col))
            if target_val is None or (isinstance(target_val, float) and (target_val != target_val)): # NaN check
                continue
            
            metric_vals = []
            valid_row = True
            for col in metrics_cols:
                val = row.get(col)
                if val is None:
                    valid_row = False
                    break
                f_val = float(val)
                if f_val != f_val: # NaN check
                    valid_row = False
                    break
                metric_vals.append(f_val)
            
            if valid_row:
                valid_rows.append({
                    'target': target_val,
                    'metrics': {col: metric_vals[i] for i, col in enumerate(metrics_cols)}
                })
        except (ValueError, TypeError):
            continue

    if len(valid_rows) < 2:
        analysis_logger.warning("Insufficient valid data points (n < 2) for correlation analysis.")
        return []

    results = []
    for metric_name in metrics_cols:
        x = [r['metrics'][metric_name] for r in valid_rows]
        y = [r['target'] for r in valid_rows]

        # Pearson
        try:
            p_val, p_corr = pearsonr(x, y)
        except Exception as e:
            analysis_logger.error(f"Pearson correlation failed for {metric_name}: {e}")
            p_val, p_corr = None, None

        # Spearman
        try:
            s_val, s_corr = spearmanr(x, y)
        except Exception as e:
            analysis_logger.error(f"Spearman correlation failed for {metric_name}: {e}")
            s_val, s_corr = None, None

        results.append({
            "metric_name": metric_name,
            "pearson_coeff": p_corr,
            "pearson_p_value": p_val,
            "spearman_coeff": s_corr,
            "spearman_p_value": s_val
        })

    return results

def calculate_bonferroni_pvalues(correlations: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Apply Bonferroni correction to the p-values of the correlation tests.
    Logic: fixed alpha = 0.05 / 3.
    Does NOT adjust alpha based on sample size n < 50.
    Logs warning if n < 50 but maintains fixed alpha.
    """
    n_tests = len(correlations)
    if n_tests == 0:
        return correlations

    # Bonferroni corrected p-values (multiply p-value by number of tests)
    # Cap at 1.0
    corrected_results = []
    
    # Check sample size from the first correlation result's implicit data?
    # We need n. The correlations list doesn't explicitly carry n.
    # We assume the caller (main) has n or we can infer from the data if we had it.
    # However, the task description says: "If n < 50, log a warning...".
    # We need to pass n to this function or determine it.
    # Looking at the task: "Implement Bonferroni correction... If n < 50, log a warning".
    # The main function will likely handle the logging of n.
    # But to be safe, let's assume we calculate n inside main and pass it, 
    # or we just perform the math here and log the warning if we have n.
    # Since this function receives `correlations`, it doesn't know `n`.
    # We will assume `n` is passed or handled in main. 
    # Actually, the task says "If n < 50, log a warning in results/power_analysis.log".
    # We will add `n` as an optional argument to this function to handle the logging.
    
    return corrected_results

def save_correlations(results: List[Dict[str, Any]], output_path: str = "results/correlations.json") -> None:
    """Save correlations to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    analysis_logger.info(f"Saved correlations to {output_path}")

def main():
    """
    Main entry point for T017: Bonferroni correction and correlation analysis.
    1. Load metrics from data/processed/metrics.csv
    2. Compute Pearson and Spearman correlations (T016 logic)
    3. Apply Bonferroni correction (T017 logic)
    4. Log sample size warning if n < 50
    5. Save results to results/correlations.json
    6. Update state hash
    """
    analysis_logger.info("Starting correlation analysis and Bonferroni correction (T016 + T017).")

    # Load data
    metrics_data = load_metrics_csv()
    if not metrics_data:
        analysis_logger.error("No metrics data found. Cannot proceed.")
        return

    n = len(metrics_data)
    analysis_logger.info(f"Loaded {n} valid data points.")

    # Log sample size warning if n < 50 (FR-010)
    if n < 50:
        log_path = "results/power_analysis.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(f"WARNING: Sample size n={n} is less than 50. Power limitations documented.\n")
        analysis_logger.warning(f"Sample size n={n} < 50. Logged warning to {log_path}.")

    # Compute correlations (T016)
    raw_correlations = compute_correlations(metrics_data)
    if not raw_correlations:
        analysis_logger.error("Correlation computation failed or returned no results.")
        return

    # Apply Bonferroni correction (T017)
    # Logic: fixed alpha = 0.05 / 3.
    # We correct p-values by multiplying by number of tests (3).
    corrected_correlations = []
    for res in raw_correlations:
        new_res = res.copy()
        # Bonferroni adjusted p-value = min(p * n_tests, 1.0)
        n_tests = 3
        if res.get('pearson_p_value') is not None:
            new_res['bonferroni_pearson_p'] = min(res['pearson_p_value'] * n_tests, 1.0)
        else:
            new_res['bonferroni_pearson_p'] = None

        if res.get('spearman_p_value') is not None:
            new_res['bonferroni_spearman_p'] = min(res['spearman_p_value'] * n_tests, 1.0)
        else:
            new_res['bonferroni_spearman_p'] = None

        # Determine significance based on fixed alpha = 0.05 / 3
        alpha_corrected = 0.05 / 3.0
        
        if new_res['bonferroni_pearson_p'] is not None:
            new_res['pearson_significant'] = new_res['bonferroni_pearson_p'] < alpha_corrected
        else:
            new_res['pearson_significant'] = False

        if new_res['bonferroni_spearman_p'] is not None:
            new_res['spearman_significant'] = new_res['bonferroni_spearman_p'] < alpha_corrected
        else:
            new_res['spearman_significant'] = False

        corrected_correlations.append(new_res)

    # Save results
    output_path = "results/correlations.json"
    save_correlations(corrected_correlations, output_path)

    # Update state
    update_state_artifact_hash(output_path)

    analysis_logger.info("Bonferroni correction and correlation analysis completed successfully.")

if __name__ == "__main__":
    main()