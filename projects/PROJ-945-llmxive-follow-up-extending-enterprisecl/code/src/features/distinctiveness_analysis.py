"""
Perform Mann-Whitney U test on feature distributions (failed vs success)
and apply FDR correction (Benjamini-Hochberg if features > 10, else Bonferroni).
Log results to data/results/distinctiveness_stats.csv.
"""
import os
import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
from scipy.stats import mannwhitneyu

# Add project root to path for imports if running as script
if "code" not in sys.path:
    code_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(code_root))

from src.utils.resource_monitor import ResourceMonitor


def load_features_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load features from JSONL file."""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def separate_by_status(records: List[Dict[str, Any]]) -> Tuple[Dict[str, List[float]], Dict[str, List[float]]]:
    """
    Separate feature values by status (success/failure).
    Returns dicts mapping feature_name -> list of values.
    """
    failed_features: Dict[str, List[float]] = {}
    success_features: Dict[str, List[float]] = {}

    for record in records:
        status = record.get("status", "").lower()
        features = record.get("features", {})

        # Determine which dict to populate
        target_dict = failed_features if status == "failed" else success_features

        for feat_name, feat_val in features.items():
            if feat_name not in target_dict:
                target_dict[feat_name] = []
            # Ensure we only collect numeric values
            if isinstance(feat_val, (int, float)):
                target_dict[feat_name].append(float(feat_val))

    return failed_features, success_features


def perform_mann_whitney_u(failed_vals: List[float], success_vals: List[float]) -> float:
    """
    Perform Mann-Whitney U test and return the p-value.
    Handles edge cases where one group has < 2 samples or all values are identical.
    """
    if len(failed_vals) < 2 or len(success_vals) < 2:
        # Not enough data for statistical test
        return 1.0

    try:
        # Use two-sided test
        stat, p_value = mannwhitneyu(failed_vals, success_vals, alternative='two-sided')
        return p_value
    except Exception:
        # Fallback for edge cases (e.g., constant values)
        return 1.0


def apply_fdr_correction(p_values: List[float], method: str = "auto") -> List[float]:
    """
    Apply FDR correction to a list of p-values.
    - Benjamini-Hochberg if len(p_values) > 10
    - Bonferroni otherwise
    """
    n = len(p_values)
    if n == 0:
        return []

    if method == "auto":
        use_bh = n > 10
    else:
        use_bh = (method == "bh")

    corrected = []
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])

    if use_bh:
        # Benjamini-Hochberg procedure
        # Sort p-values, calculate critical values, then adjust
        # We need to return corrected p-values in the original order
        # BH adjusted p-value for rank i (1-indexed) is p_i * n / i
        # But we must ensure monotonicity (adjusted p_i <= adjusted p_{i+1})

        sorted_p_vals = [p_values[i] for i in sorted_indices]
        adjusted_sorted = []
        min_val = 1.0
        for rank in range(n, 0, -1):
            # rank is 1-based index from the end
            i = n - rank  # 0-based index in sorted list
            p = sorted_p_vals[i]
            adj = p * n / rank
            if adj < min_val:
                min_val = adj
            else:
                adj = min_val
            adjusted_sorted.append(adj)

        # Reverse to match sorted order
        adjusted_sorted.reverse()

        # Map back to original order
        result = [0.0] * n
        for idx, adj_val in zip(sorted_indices, adjusted_sorted):
            result[idx] = min(1.0, adj_val) # Cap at 1.0
        return result

    else:
        # Bonferroni correction
        return [min(1.0, p * n) for p in p_values]


def run_analysis(
    input_path: str,
    output_path: str,
    threshold: float = 0.05
) -> None:
    """
    Main analysis function.
    1. Loads features.
    2. Separates by status.
    3. Runs Mann-Whitney U for each feature.
    4. Applies FDR correction.
    5. Writes CSV.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    records = load_features_jsonl(input_path)
    if not records:
        raise ValueError("No records found in input file.")

    failed_features, success_features = separate_by_status(records)

    # Get all feature names (union of keys)
    all_features = set(failed_features.keys()) | set(success_features.keys())

    if not all_features:
        raise ValueError("No numeric features found in records.")

    # Collect p-values
    feature_names = sorted(list(all_features))
    raw_p_values = []
    stats_data = []

    for feat_name in feature_names:
        f_vals = failed_features.get(feat_name, [])
        s_vals = success_features.get(feat_name, [])

        if not f_vals or not s_vals:
            # Skip features missing in one group
            p_val = 1.0
        else:
            p_val = perform_mann_whitney_u(f_vals, s_vals)

        raw_p_values.append(p_val)
        stats_data.append({
            "feature": feat_name,
            "n_failed": len(failed_features.get(feat_name, [])),
            "n_success": len(success_features.get(feat_name, [])),
            "p_value": p_val
        })

    # Apply FDR correction
    n_features = len(feature_names)
    corrected_p_values = apply_fdr_correction(raw_p_values, method="auto")

    # Update stats data with corrected values and significance
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['feature', 'p_value', 'corrected_p_value', 'significant'])

        for i, feat_name in enumerate(feature_names):
            p_val = raw_p_values[i]
            corr_p_val = corrected_p_values[i]
            is_sig = corr_p_val < threshold
            writer.writerow([feat_name, f"{p_val:.6f}", f"{corr_p_val:.6f}", is_sig])

    print(f"Analysis complete. Results written to {output_path}")
    print(f"Total features tested: {n_features}")
    significant_count = sum(1 for cp in corrected_p_values if cp < threshold)
    print(f"Significant features (p < {threshold}): {significant_count}")


def main():
    # Default paths based on project structure
    code_root = Path(__file__).resolve().parent.parent.parent
    input_file = code_root / "data" / "processed" / "features.jsonl"
    output_file = code_root / "data" / "results" / "distinctiveness_stats.csv"

    # Allow override via command line args
    if len(sys.argv) >= 3:
        input_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2])

    # Run with monitoring
    monitor = ResourceMonitor()
    monitor.start()

    try:
        run_analysis(str(input_file), str(output_file))
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        monitor.stop()
        memory_log = monitor.get_log()
        print(f"Peak RSS: {memory_log.get('peak_rss_mb', 'N/A')} MB")


if __name__ == "__main__":
    main()