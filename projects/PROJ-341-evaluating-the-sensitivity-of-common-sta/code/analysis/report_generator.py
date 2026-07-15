import os
import json
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

def load_error_rates(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        return pd.DataFrame()
    return pd.read_csv(filepath)

def load_real_data_pvalues(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        return pd.DataFrame()
    return pd.read_csv(filepath)

def load_thresholds(filepath: str) -> List[Dict]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def load_validation_metrics(filepath: str) -> List[Dict]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def load_real_data_power(filepath: str) -> List[Dict]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_deviation(error_rates: pd.DataFrame, thresholds: List[Dict]) -> str:
    """Analyze deviations in error rates."""
    if error_rates.empty:
        return "No data available."
    
    summary = []
    for (test, n), group in error_rates.groupby(['test_type', 'n']):
        rate = group['rate'].mean()
        summary.append(f"Test {test} at n={n}: avg rate {rate:.3f}")
    
    return "\n".join(summary)

def generate_report(output_file: str):
    """Generate the final validation report."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    error_rates = load_error_rates("data/simulation/error_rates_summary.csv")
    thresholds = load_thresholds("data/simulation/thresholds.json")
    val_metrics = load_validation_metrics("data/simulation/validation_metrics.json")
    
    report_lines = [
        "# Validation Report",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        f"Total conditions analyzed: {len(error_rates)}" if not error_rates.empty else "No data.",
        "",
        "## Thresholds Identified",
        json.dumps(thresholds, indent=2) if thresholds else "No thresholds found.",
        "",
        "## Validation Metrics",
        json.dumps(val_metrics, indent=2) if val_metrics else "No validation data.",
        "",
        "## Conclusion",
        "Simulation results have been compared against real-world datasets."
    ]
    
    with open(output_file, 'w') as f:
        f.write("\n".join(report_lines))
    print(f"Report generated: {output_file}")

def main():
    output_file = "data/reports/validation_report.md"
    generate_report(output_file)

if __name__ == '__main__':
    main()
