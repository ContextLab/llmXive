"""
Standalone VIF Analyzer Script.

This script performs Variance Inflation Factor (VIF) analysis on the
trade-off data to detect multicollinearity among covariates.
"""
import json
import sys
from pathlib import Path
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

OUTPUT_DIR = Path("data/results")
PROCESSED_DIR = Path("data/processed")

def load_processed_logs() -> list:
    """Load all execution logs from the processed directory."""
    logs = []
    if not PROCESSED_DIR.exists():
        return logs
    
    for file_path in PROCESSED_DIR.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                log = json.load(f)
                logs.append(log)
        except (json.JSONDecodeError, IOError):
            continue
    return logs

def filter_invalid_workflows(logs: list) -> list:
    """Filter out workflows that are invalid."""
    return [log for log in logs if log.get("is_valid", True) is not False]

def prepare_dataframe(logs: list) -> pd.DataFrame:
    """Prepare DataFrame for VIF analysis."""
    valid_logs = filter_invalid_workflows(logs)
    
    # Filter numeric context_reduction_pct
    numeric_logs = [
        log for log in valid_logs 
        if isinstance(log.get("context_reduction_pct"), (int, float))
    ]
    
    if not numeric_logs:
        return pd.DataFrame()
    
    df = pd.DataFrame(numeric_logs)
    
    # Ensure numeric columns
    df['context_reduction_pct'] = pd.to_numeric(df['context_reduction_pct'], errors='coerce')
    df['depth'] = pd.to_numeric(df.get('compression_depth', df.get('depth', 0)), errors='coerce')
    df['complexity'] = pd.to_numeric(df.get('complexity', 0), errors='coerce')
    
    # Drop NaN
    df = df.dropna(subset=['context_reduction_pct', 'depth', 'complexity'])
    
    return df

def calculate_vif_for_features(df: pd.DataFrame, features: list) -> dict:
    """Calculate VIF for specified features."""
    if not features or df.empty:
        return {}
    
    X = df[features].select_dtypes(include=[float, int])
    if X.empty:
        return {}
    
    # Add constant
    X_with_const = sm.add_constant(X)
    
    vif_results = {}
    for i, col in enumerate(X_with_const.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_with_const.values, i)
            vif_results[col] = float(vif)
        except Exception:
            vif_results[col] = float('inf')
    
    return vif_results

def generate_vif_report(df: pd.DataFrame, threshold: float = 5.0) -> dict:
    """Generate VIF report."""
    features = []
    if 'depth' in df.columns:
        features.append('depth')
    if 'complexity' in df.columns:
        features.append('complexity')
    if 'context_reduction_pct' in df.columns:
        features.append('context_reduction_pct')
    
    report = {
        "metric": "VIF",
        "threshold": threshold,
        "results": {},
        "warning": None
    }
    
    if not features:
        report["warning"] = "No suitable features found for VIF analysis."
        return report
    
    vif_results = calculate_vif_for_features(df, features)
    report["results"] = vif_results
    
    if vif_results:
        max_vif = max(vif_results.values())
        if max_vif > threshold:
            report["warning"] = (
                f"VIF exceeds threshold ({threshold}). "
                f"Max VIF: {max_vif:.2f}. This indicates potential multicollinearity "
                "which may affect coefficient stability."
            )
    
    return report

def main():
    """Main entry point."""
    print("Starting VIF analysis...")
    
    # Load data
    logs = load_processed_logs()
    if not logs:
        print("No logs found.")
        sys.exit(1)
    
    print(f"Loaded {len(logs)} logs.")
    
    # Prepare DataFrame
    df = prepare_dataframe(logs)
    if df.empty:
        print("No valid data for VIF analysis.")
        sys.exit(1)
    
    print(f"Prepared {len(df)} data points.")
    
    # Generate report
    report = generate_vif_report(df)
    
    # Save report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "vif_report.json"
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"VIF report saved to {output_path}")
    
    # Print summary
    print("\nVIF Report Summary:")
    print(f"  Threshold: {report['threshold']}")
    for feature, vif in report['results'].items():
        print(f"  {feature}: {vif:.4f}")
    
    if report['warning']:
        print(f"\nWARNING: {report['warning']}")
    
    return report

if __name__ == "__main__":
    main()