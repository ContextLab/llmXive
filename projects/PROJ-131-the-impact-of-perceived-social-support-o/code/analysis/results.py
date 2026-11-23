import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

def load_analysis_cohort(file_path: Path, logger: logging.Logger):
    """Load analysis cohort."""
    import pandas as pd
    if not file_path.exists():
        logger.error(f"Cohort file not found: {file_path}")
        return None
    return pd.read_csv(file_path)

def load_regression_results(file_path: Path, logger: logging.Logger):
    """Load regression results."""
    import pandas as pd
    if not file_path.exists():
        logger.error(f"Regression results not found: {file_path}")
        return None
    return pd.read_csv(file_path)

def generate_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics for the cohort."""
    return {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": list(df.columns),
        "missing_counts": df.isnull().sum().to_dict()
    }

def format_coefficient(coef: float, se: float = None, p: float = None) -> str:
    """Format a coefficient for display."""
    s = f"{coef:.4f}"
    if se is not None:
        s += f" (SE: {se:.4f})"
    if p is not None:
        s += f" [p={p:.4f}]"
    return s

def generate_markdown_report(cohort_stats: Dict, reg_results: List[Dict], logger: logging.Logger) -> str:
    """Generate a markdown summary report."""
    md = "# Regression Summary Report\n\n"
    md += "## Cohort Summary\n\n"
    md += f"- Rows: {cohort_stats['n_rows']}\n"
    md += f"- Columns: {cohort_stats['n_cols']}\n\n"
    
    md += "## Regression Results\n\n"
    md += "| Outcome | Interaction Coef | SE | P-value | Interpretation |\n"
    md += "|---------|------------------|----|---------|----------------|\n"
    
    for res in reg_results:
        outcome = res.get('outcome', 'Unknown')
        coef = res.get('interaction_coef', 0)
        se = res.get('interaction_se', 0)
        p = res.get('interaction_p', 1)
        
        interp = "Significant buffering" if p < 0.05 else "Not significant"
        md += f"| {outcome} | {coef:.4f} | {se:.4f} | {p:.4f} | {interp} |\n"
    
    md += "\n## Interpretation\n\n"
    md += "The interaction term represents the buffering effect of social support on harassment severity.\n"
    
    return md

def save_report(md_content: str, output_path: Path, logger: logging.Logger):
    """Save report to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(md_content)
    logger.info(f"Report saved to {output_path}")

def main():
    """Entry point for report generation (T025)."""
    logger = get_logger(__name__)
    logger.info("Generating Regression Summary Report")
    
    # Load data
    cohort_path = project_root / "data" / "results" / "analysis_cohort.csv"
    reg_path = project_root / "data" / "results" / "regression_results.csv"
    
    cohort = load_analysis_cohort(cohort_path, logger)
    reg_df = load_regression_results(reg_path, logger)
    
    if cohort is None or reg_df is None:
        logger.error("Missing data for report generation.")
        return
    
    # Generate stats
    cohort_stats = generate_summary_stats(cohort)
    
    # Convert reg_df to list of dicts
    reg_results = reg_df.to_dict('records')
    
    # Generate report
    md_content = generate_markdown_report(cohort_stats, reg_results, logger)
    
    # Save
    output_path = project_root / "data" / "results" / "regression_summary.md"
    save_report(md_content, output_path, logger)
    
    logger.info("Report generation completed.")

if __name__ == "__main__":
    main()