"""
Ablation Analysis Script for PROJ-108

This script verifies the independence of style consistency scores from code complexity.

Justification for Control Variable:
While `cyclomatic_complexity` is extracted (T013), we use `file_size` as the primary 
control variable in this ablation analysis. This decision avoids potential multicollinearity 
between style metrics (which often correlate with line count) and cyclomatic complexity, 
providing a cleaner isolation of the style effect. `cyclomatic_complexity` is included 
in the analysis as a secondary check but is not the primary control variable.
"""
import argparse
import json
import os
import sys
import statistics
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Attempt to import scipy for statistical tests; if unavailable, use simple approximations
try:
    import scipy.stats as stats
    import scipy.optimize as optimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("WARNING: scipy not found. Some advanced statistical tests will be skipped or approximated.")

# Attempt to import statsmodels for ANCOVA if available
try:
    import statsmodels.api as sm
    from statsmodels.formula.api import ols
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("WARNING: statsmodels not found. ANCOVA will be skipped or approximated.")

def load_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load the stratified data CSV containing style scores and metadata."""
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats
            try:
                row['composite_score'] = float(row['composite_score'])
                row['file_size'] = float(row['file_size'])
                row['cyclomatic_complexity'] = float(row['cyclomatic_complexity'])
                # Handle potential float values for file_age if present
                if 'file_age' in row and row['file_age']:
                    row['file_age'] = float(row['file_age'])
            except (ValueError, TypeError) as e:
                # Skip rows with invalid numeric data
                print(f"Skipping row due to invalid numeric data: {e}")
                continue
            data.append(row)
    return data

def load_evaluation_results(file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load evaluation results (BLEU/F1 scores) keyed by group or file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Evaluation results not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Assuming JSONL format where each line is a result dict
        # or a JSON list of dicts. We'll handle both.
        content = f.read().strip()
        if not content:
            return {}
        
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return {"results": data}
            elif isinstance(data, dict):
                return data
            else:
                return {}
        except json.JSONDecodeError:
            # Try line-by-line JSONL
            results = []
            for line in content.split('\n'):
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return {"results": results}

def merge_data(stratified_data: List[Dict], eval_results: Dict[str, List[Dict]]) -> List[Dict]:
    """Merge stratified data with evaluation results on file_path."""
    # Create a lookup map for evaluation results by file_path
    # Assuming the eval results have a 'file_path' key
    eval_map = {}
    if "results" in eval_results:
        for item in eval_results["results"]:
            if "file_path" in item:
                eval_map[item["file_path"]] = item
    else:
        # Try to find the list of results in the dict
        for key, value in eval_results.items():
            if isinstance(value, list):
                for item in value:
                    if "file_path" in item:
                        eval_map[item["file_path"]] = item
                break

    merged = []
    for row in stratified_data:
        file_path = row.get("file_path")
        if file_path in eval_map:
            eval_item = eval_map[file_path]
            # Merge keys, preferring eval_item keys if they exist (e.g., BLEU scores)
            merged_row = {**row, **eval_item}
            merged.append(merged_row)
        else:
            # Include row even if no eval result (might be needed for ablation)
            merged.append(row)
    return merged

def calculate_partial_correlation(x: List[float], y: List[float], z: List[float]) -> Optional[float]:
    """
    Calculate partial correlation between x and y, controlling for z.
    Formula: r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1 - r_xz^2) * (1 - r_yz^2))
    """
    if len(x) != len(y) or len(y) != len(z) or len(x) < 3:
        return None

    if not SCIPY_AVAILABLE:
        # Fallback to manual calculation
        def pearson(r, s):
            n = len(r)
            mean_r = sum(r) / n
            mean_s = sum(s) / n
            num = sum((ri - mean_r) * (si - mean_s) for ri, si in zip(r, s))
            den_r = sum((ri - mean_r)**2 for ri in r)**0.5
            den_s = sum((si - mean_s)**2 for si in s)**0.5
            if den_r == 0 or den_s == 0:
                return 0.0
            return num / (den_r * den_s)

        r_xy = pearson(x, y)
        r_xz = pearson(x, z)
        r_yz = pearson(y, z)

        denom = ((1 - r_xz**2) * (1 - r_yz**2))**0.5
        if denom == 0:
            return 0.0
        
        return (r_xy - r_xz * r_yz) / denom
    else:
        return stats.partialcorr(x, y, z)

def run_ablation_analysis(data: List[Dict[str, Any]], target_metric: str = "bleu_score") -> Dict[str, Any]:
    """
    Perform ablation analysis to verify style score independence from code complexity.
    
    Returns a report containing:
    - Correlation between style score and target metric (raw)
    - Partial correlation controlling for file_size
    - Partial correlation controlling for cyclomatic_complexity
    - Justification and interpretation
    """
    if not data:
        return {"error": "No data provided for ablation analysis"}

    # Extract vectors
    style_scores = []
    file_sizes = []
    cyclomatic_complexities = []
    target_values = []
    
    for row in data:
        if target_metric in row and isinstance(row[target_metric], (int, float)):
            style_scores.append(row.get("composite_score", 0.0))
            file_sizes.append(row.get("file_size", 0.0))
            cyclomatic_complexities.append(row.get("cyclomatic_complexity", 0.0))
            target_values.append(row[target_metric])
        elif "f1_score" in row and isinstance(row["f1_score"], (int, float)):
            # Fallback to F1 if BLEU is not present
            style_scores.append(row.get("composite_score", 0.0))
            file_sizes.append(row.get("file_size", 0.0))
            cyclomatic_complexities.append(row.get("cyclomatic_complexity", 0.0))
            target_values.append(row["f1_score"])

    if len(style_scores) < 3:
        return {"error": "Insufficient data points for correlation analysis"}

    report = {
        "analysis_type": "ablation_analysis",
        "control_variable_justification": (
            "Using 'file_size' as the primary control variable to avoid multicollinearity "
            "between style metrics (which often correlate with line count) and cyclomatic complexity. "
            "Cyclomatic complexity is included as a secondary check."
        ),
        "primary_control": "file_size",
        "secondary_control": "cyclomatic_complexity",
        "target_metric": target_metric,
        "sample_size": len(style_scores),
        "raw_correlation": None,
        "partial_correlation_file_size": None,
        "partial_correlation_complexity": None,
        "interpretation": []
    }

    # Calculate raw correlation
    if SCIPY_AVAILABLE:
        raw_corr, raw_p = stats.pearsonr(style_scores, target_values)
        report["raw_correlation"] = {
            "r": raw_corr,
            "p_value": raw_p,
            "significant": raw_p < 0.05
        }
    else:
        # Manual Pearson
        n = len(style_scores)
        mean_x = sum(style_scores) / n
        mean_y = sum(target_values) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(style_scores, target_values))
        den_x = sum((x - mean_x)**2 for x in style_scores)**0.5
        den_y = sum((y - mean_y)**2 for y in target_values)**0.5
        if den_x == 0 or den_y == 0:
            raw_corr = 0.0
        else:
            raw_corr = num / (den_x * den_y)
        report["raw_correlation"] = {
            "r": raw_corr,
            "p_value": "manual_calculation_unavailable",
            "significant": "unknown"
        }

    # Partial correlation controlling for file_size
    partial_corr_size = calculate_partial_correlation(style_scores, target_values, file_sizes)
    report["partial_correlation_file_size"] = partial_corr_size

    # Partial correlation controlling for cyclomatic_complexity
    partial_corr_complexity = calculate_partial_correlation(style_scores, target_values, cyclomatic_complexities)
    report["partial_correlation_complexity"] = partial_corr_complexity

    # Interpretation
    if partial_corr_size is not None and abs(partial_corr_size) < 0.1:
        report["interpretation"].append(
            "The style score shows negligible correlation with the target metric after controlling for file_size. "
            "This supports the hypothesis that style consistency effects are independent of code size."
        )
    elif partial_corr_size is not None:
        report["interpretation"].append(
            f"The style score shows a partial correlation of {partial_corr_size:.3f} with the target metric "
            "after controlling for file_size. This suggests some dependency or shared variance."
        )

    if partial_corr_complexity is not None and abs(partial_corr_complexity) < 0.1:
        report["interpretation"].append(
            "Similarly, controlling for cyclomatic complexity yields a negligible correlation, "
            "further supporting the independence hypothesis."
        )
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Ablation Analysis for Style Consistency Study")
    parser.add_argument(
        "--input-stratified",
        type=str,
        default="data/processed/style_scores.csv",
        help="Path to stratified style scores CSV (from T016)"
    )
    parser.add_argument(
        "--input-eval",
        type=str,
        default="data/processed/evaluation_report.json",
        help="Path to evaluation results JSON/JSONL (from T021)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/ablation_report.json",
        help="Path to output ablation report JSON"
    )
    parser.add_argument(
        "--metric",
        type=str,
        default="bleu_score",
        choices=["bleu_score", "f1_score"],
        help="Target metric to analyze (default: bleu_score)"
    )
    args = parser.parse_args()

    input_path = Path(args.input_stratified)
    eval_path = Path(args.input_eval)
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading stratified data from: {input_path}")
    try:
        stratified_data = load_data(input_path)
        print(f"Loaded {len(stratified_data)} records.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Loading evaluation results from: {eval_path}")
    try:
        eval_results = load_evaluation_results(eval_path)
        print(f"Loaded evaluation results.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Merging data...")
    merged_data = merge_data(stratified_data, eval_results)
    print(f"Merged {len(merged_data)} records.")

    print(f"Running ablation analysis for {args.metric}...")
    report = run_ablation_analysis(merged_data, args.metric)

    print(f"Saving report to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print("Ablation analysis complete.")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()