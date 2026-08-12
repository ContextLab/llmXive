import json
import os
import re
import logging
import hashlib
import csv
from typing import Any, Dict, List, Optional, Tuple
from scipy import stats
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- File I/O Helpers ---

def load_json_file(filepath: str) -> Any:
    """Load and return JSON data from a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Any) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def calculate_checksum(filepath: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(filepath: str, checksum_file: str = "data/checksums.txt") -> None:
    """Update the checksums file with the checksum of the given file."""
    checksum = calculate_checksum(filepath)
    filename = os.path.basename(filepath)
    
    checksums = {}
    if os.path.exists(checksum_file):
        with open(checksum_file, 'r') as f:
            for line in f:
                if ':' in line:
                    k, v = line.strip().split(':', 1)
                    checksums[k] = v

    checksums[filename] = checksum
    
    os.makedirs(os.path.dirname(checksum_file), exist_ok=True)
    with open(checksum_file, 'w') as f:
        for k, v in checksums.items():
            f.write(f"{k}:{v}\n")

# --- PII Removal Helpers ---

def remove_pii_from_string(text: str) -> str:
    """Remove common PII patterns from a string."""
    patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
        r'\b\d{5}([-]?\d{4})?\b',  # Zip code (simplified)
    ]
    for pattern in patterns:
        text = re.sub(pattern, '[REDACTED]', text)
    return text

def remove_pii_from_list(data: List[Any]) -> List[Any]:
    return [remove_pii_from_string(str(item)) if isinstance(item, str) else item for item in data]

def remove_pii_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: remove_pii_from_string(str(v)) if isinstance(v, str) else v for k, v in data.items()}

def remove_pii(data: Any) -> Any:
    if isinstance(data, dict):
        return remove_pii_from_dict(data)
    elif isinstance(data, list):
        return remove_pii_from_list(data)
    elif isinstance(data, str):
        return remove_pii_from_string(data)
    return data

# --- Data Cleaning & Validation Helpers ---

def validate_input_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Basic validation of input data structure."""
    required_keys = ['participant_id', 'condition', 'time_on_task', 'help_requests']
    for key in required_keys:
        if key not in data:
            return False, f"Missing required key: {key}"
    if not isinstance(data['time_on_task'], (int, float)):
        return False, "time_on_task must be numeric"
    if not isinstance(data['help_requests'], list):
        return False, "help_requests must be a list"
    return True, "OK"

def handle_incomplete_records(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Separate complete and incomplete records."""
    complete = []
    incomplete = []
    for record in records:
        if record.get('status') == 'complete' or (record.get('time_on_task') is not None and record.get('condition') is not None):
            complete.append(record)
        else:
            incomplete.append(record)
    return complete, incomplete

def save_dropouts(dropouts: List[Dict[str, Any]], filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(dropouts, f, indent=2)

def save_cleaned_dataset_csv(records: List[Dict[str, Any]], filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if not records:
        logger.warning("No records to write to CSV.")
        with open(filepath, 'w') as f:
            f.write("")
        return

    fieldnames = sorted(set(key for record in records for key in record.keys()))
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for record in records:
            writer.writerow(record)

# --- Statistical Analysis Functions ---

def perform_welchs_anova(groups: Dict[str, List[float]]) -> Dict[str, Any]:
    """
    Perform Welch's ANOVA.
    Args:
        groups: Dict mapping condition name to list of values.
    Returns:
        Dictionary with F-statistic, p-value, and group means.
    """
    if len(groups) < 2:
        return {"error": "Need at least 2 groups for ANOVA"}
    
    group_values = [np.array(v) for v in groups.values()]
    group_names = list(groups.keys())
    
    # Welch's ANOVA calculation
    # F = ( (N - k) / (k - 1) ) * ( sum(w_i * (mean_i - mean_g)^2) / (1 + (2*(k-2)/(N-k)) * sum( (1 - w_i/W)^2 / (n_i - 1) ) ) )
    # where w_i = n_i / s_i^2, W = sum(w_i), mean_g = sum(w_i * mean_i) / W
    
    k = len(group_values)
    N = sum(len(v) for v in group_values)
    
    means = [np.mean(v) for v in group_values]
    vars_ = [np.var(v, ddof=1) if len(v) > 1 else 0.0001 for v in group_values] # Avoid div by zero
    ns = [len(v) for v in group_values]
    
    w = [n / v if v > 0 else n / 0.0001 for n, v in zip(ns, vars_)]
    W = sum(w)
    grand_mean = sum(wi * mi for wi, mi in zip(w, means)) / W
    
    numerator = sum(wi * (mi - grand_mean)**2 for wi, mi in zip(w, means))
    
    term2_sum = sum( ((1 - wi/W)**2) / (ni - 1) if ni > 1 else 0 for wi, ni in zip(w, ns))
    denominator = 1 + (2 * (k - 2) / (N - k)) * term2_sum if N > k else 1.0
    
    if denominator == 0:
        f_stat = 0.0
    else:
        f_stat = ((N - k) / (k - 1)) * (numerator / denominator)
    
    # Degrees of freedom
    df1 = k - 1
    df2 = (N - k) / (3 * (k - 2) * term2_sum) if term2_sum > 0 else 1.0 # Approximation
    
    p_value = 1 - stats.f.cdf(f_stat, df1, df2)
    
    return {
        "f_statistic": float(f_stat),
        "df1": float(df1),
        "df2": float(df2),
        "p_value": float(p_value),
        "group_means": {name: float(np.mean(vals)) for name, vals in groups.items()},
        "group_sizes": {name: len(vals) for name, vals in groups.items()}
    }

def perform_games_howell_posthoc(groups: Dict[str, List[float]]) -> List[Dict[str, Any]]:
    """
    Perform Games-Howell post-hoc tests.
    Returns list of pairwise comparisons with t-stat, p-value, CI.
    """
    comparisons = []
    group_names = list(groups.keys())
    values = {k: np.array(v) for k, v in groups.items()}
    
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            g1, g2 = group_names[i], group_names[j]
            v1, v2 = values[g1], values[g2]
            
            n1, n2 = len(v1), len(v2)
            mean1, mean2 = np.mean(v1), np.mean(v2)
            var1, var2 = np.var(v1, ddof=1), np.var(v2, ddof=1)
            
            if n1 < 2 or n2 < 2:
                continue
                
            se = np.sqrt(var1/n1 + var2/n2)
            t_stat = (mean1 - mean2) / se if se > 0 else 0.0
            
            # Welch-Satterthwaite degrees of freedom
            df = (var1/n1 + var2/n2)**2 / ( (var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1) )
            
            p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df))
            
            # Confidence interval (95%)
            t_crit = stats.t.ppf(0.975, df)
            ci_lower = (mean1 - mean2) - t_crit * se
            ci_upper = (mean1 - mean2) + t_crit * se
            
            comparisons.append({
                "group1": g1,
                "group2": g2,
                "mean_diff": float(mean1 - mean2),
                "t_statistic": float(t_stat),
                "df": float(df),
                "p_value": float(p_val),
                "ci_95_lower": float(ci_lower),
                "ci_95_upper": float(ci_upper)
            })
    
    return comparisons

def run_sensitivity_analysis(input_data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Perform sensitivity analysis for alpha thresholds.
    Loads cleaned data, groups by condition, runs Welch's ANOVA,
    and reports p-values against standard alpha levels (0.01, 0.05, 0.10).
    Explicitly reports power limitations for N=15-20.
    """
    logger.info(f"Loading data from {input_data_path}")
    data = load_json_file(input_data_path)
    
    if not isinstance(data, list):
        data = [data]
        
    # Group data by condition
    groups: Dict[str, List[float]] = {}
    for record in data:
        cond = record.get('condition')
        time_val = record.get('time_on_task')
        if cond and time_val is not None:
            if cond not in groups:
                groups[cond] = []
            groups[cond].append(float(time_val))
    
    if len(groups) < 2:
        logger.error("Not enough groups to perform sensitivity analysis.")
        return {"error": "Insufficient groups"}

    logger.info(f"Groups found: {list(groups.keys())}")
    logger.info(f"Sample sizes: {[len(v) for v in groups.values()]}")

    # Perform Welch's ANOVA
    anova_results = perform_welchs_anova(groups)
    
    if "error" in anova_results:
        return anova_results

    p_value = anova_results['p_value']
    
    # Standard alpha levels
    alpha_levels = [0.01, 0.05, 0.10]
    significance_results = {}
    
    for alpha in alpha_levels:
        is_significant = p_value < alpha
        significance_results[str(alpha)] = {
            "alpha": alpha,
            "p_value": p_value,
            "is_significant": is_significant,
            "conclusion": "Reject Null" if is_significant else "Fail to Reject Null"
        }

    # Power limitation note
    # Check total N
    total_n = sum(len(v) for v in groups.values())
    min_group_n = min(len(v) for v in groups.values())
    
    power_note = (
        f"Sensitivity Analysis Note: Total N={total_n}, Min Group N={min_group_n}. "
        f"Given the small sample size (N=15-20 range), the study is likely UNDERPOWERED "
        f"to detect medium effect sizes (Cohen's d ~ 0.5). "
        f"A non-significant result should be interpreted with caution as it may reflect "
        f"low statistical power rather than a true absence of effect."
    )

    result = {
        "description": "Sensitivity Analysis for Alpha Thresholds",
        "anova_summary": {
            "f_statistic": anova_results['f_statistic'],
            "p_value": p_value,
            "df1": anova_results['df1'],
            "df2": anova_results['df2']
        },
        "alpha_thresholds": significance_results,
        "power_limitation_warning": power_note,
        "sample_sizes": {k: len(v) for k, v in groups.items()}
    }

    logger.info(f"Saving sensitivity analysis to {output_path}")
    save_json_file(output_path, result)
    
    # Update checksums
    update_checksums(output_path)
    
    return result

def main():
    """Main entry point for analysis script."""
    # Paths relative to project root
    input_path = "data/processed/cleaned_dataset.json" # Assuming cleaned data is JSON or CSV converted
    output_path = "data/reports/sensitivity_analysis.json"
    
    # If input is CSV, we need to load it differently, but task T032 produced CSV.
    # We'll assume a helper to load CSV to dict if needed, or adjust input path.
    # For this task, let's assume the cleaned data is available as JSON for analysis 
    # or we load the CSV and convert.
    
    # Check if CSV exists (from T032)
    csv_path = "data/processed/cleaned_dataset.csv"
    if os.path.exists(csv_path):
        # Load CSV manually
        records = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings to floats
                if 'time_on_task' in row and row['time_on_task']:
                    try:
                        row['time_on_task'] = float(row['time_on_task'])
                    except ValueError:
                        row['time_on_task'] = None
                records.append(row)
        # Save temporarily as JSON for the analysis function
        save_json_file(input_path, records)
    else:
        logger.error(f"Cleaned dataset not found at {csv_path}. Cannot run analysis.")
        return

    run_sensitivity_analysis(input_path, output_path)
    logger.info("Sensitivity analysis complete.")

if __name__ == "__main__":
    main()