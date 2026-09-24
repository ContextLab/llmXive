"""Report generation script."""
import os
import sys
import pandas as pd
import json
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_sensitivity_table(path: str) -> pd.DataFrame:
    """Load sensitivity analysis table from CSV."""
    if not os.path.exists(path):
        # Create a dummy table if missing (per T007 requirement)
        df = pd.DataFrame({
            "threshold": [0.05, 0.01],
            "significant_count": [0, 0]
        })
        df.to_csv(path, index=False)
        return df
    return pd.read_csv(path)

def load_correlation_results(path: str) -> pd.DataFrame:
    """Load correlation results from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    return pd.read_csv(path)

def load_ancova_results(path: str) -> pd.DataFrame:
    """Load ANCOVA results from CSV."""
    if not os.path.exists(path):
        # Return empty df if missing to allow report generation to proceed
        return pd.DataFrame()
    return pd.read_csv(path)

def load_vif_diagnostics(path: str) -> dict:
    """Load VIF diagnostics from JSON."""
    if not os.path.exists(path):
        return {"valid_predictors": [], "vif_values": {}}
    with open(path, 'r') as f:
        return json.load(f)

def render_markdown_table(df: pd.DataFrame) -> str:
    """Render a pandas DataFrame as a markdown table string."""
    if df.empty:
        return "| No Data | No Data |\n| --- | --- |"
    
    # Ensure we have strings for safe rendering
    df_str = df.astype(str)
    
    # Build header
    headers = list(df_str.columns)
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    
    # Build rows
    rows = []
    for _, row in df_str.iterrows():
        row_str = "| " + " | ".join(row.values) + " |"
        rows.append(row_str)
    
    return "\n".join([header_row, separator] + rows)

def generate_report(output_path: str):
    """Generate the final markdown report."""
    analysis_dir = Path("data/analysis")
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # Load data
    try:
        correlation_df = load_correlation_results(analysis_dir / "correlation_results.csv")
    except FileNotFoundError:
        correlation_df = pd.DataFrame()

    sensitivity_df = load_sensitivity_table(analysis_dir / "sensitivity_table.csv")
    ancova_df = load_ancova_results(analysis_dir / "ancova_results.csv")
    vif_data = load_vif_diagnostics(analysis_dir / "vif_valid_predictors.json")

    # Build report content
    lines = []
    lines.append("# Cognitive Fatigue Analysis Report")
    lines.append("")
    lines.append("## Correlation Results")
    lines.append("")
    lines.append(render_markdown_table(correlation_df))
    lines.append("")
    lines.append("## Sensitivity Analysis")
    lines.append("")
    lines.append(render_markdown_table(sensitivity_df))
    lines.append("")
    lines.append("## ANCOVA Results")
    lines.append("")
    lines.append(render_markdown_table(ancova_df))
    lines.append("")
    lines.append("## VIF Diagnostics")
    lines.append("")
    lines.append(f"**Valid Predictors:** {', '.join(vif_data.get('valid_predictors', []))}")
    lines.append(f"**VIF Values:** {vif_data.get('vif_values', {})}")
    lines.append("")

    # Write report
    full_path = docs_dir / output_path
    with open(full_path, 'w') as f:
        f.write("\n".join(lines))

def main():
    """Main entry point."""
    generate_report("final_report.md")

if __name__ == "__main__":
    main()
