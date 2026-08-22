import os
import sys
import json
import argparse
import logging
from pathlib import Path
import pandas as pd

def calculate_ui_completeness(ui_element_count: int, max_elements: int = 20) -> float:
    """
    Calculate UI completeness based on element count.
    Normalized to [0, 1].
    """
    if max_elements <= 0:
        return 0.0
    return min(1.0, ui_element_count / max_elements)

def calculate_metrics_for_run(run_data: dict) -> dict:
    """Calculate derived metrics for a single run."""
    ui_count = run_data.get('ui_element_count', 0)
    completeness = calculate_ui_completeness(ui_count)
    
    return {
        'ui_element_count': ui_count,
        'ui_completeness': completeness,
        'density_level': run_data.get('density_level', 0)
    }

def aggregate_metrics_by_density(results: list) -> pd.DataFrame:
    """Aggregate metrics by density level."""
    df = pd.DataFrame(results)
    if df.empty:
        return pd.DataFrame()
    
    agg = df.groupby('density_level').agg({
        'ui_element_count': 'mean',
        'alignment_score': 'mean',
        'total_latency_ms': 'mean'
    }).reset_index()
    return agg

def load_simulation_results(input_path: Path) -> pd.DataFrame:
    """Load simulation results from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Simulation results not found at {input_path}")
    return pd.read_csv(input_path)

def validate_ui_element_logging(df: pd.DataFrame) -> bool:
    """Validate that ui_element_count is present and non-negative."""
    if 'ui_element_count' not in df.columns:
        return False
    return (df['ui_element_count'] >= 0).all()

def save_metrics_report(metrics: dict, output_path: Path):
    """Save metrics report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Calculate and validate simulation metrics")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output JSON path")
    args = parser.parse_args()

    logger = logging.getLogger("metrics")
    df = load_simulation_results(Path(args.input))
    
    if not validate_ui_element_logging(df):
        logger.error("UI element logging validation failed")
        sys.exit(1)
    
    agg = aggregate_metrics_by_density(df)
    report = {
        'summary': agg.to_dict(orient='records'),
        'total_runs': len(df)
    }
    
    save_metrics_report(report, Path(args.output))
    print(f"Metrics report saved to {args.output}")

if __name__ == "__main__":
    main()
