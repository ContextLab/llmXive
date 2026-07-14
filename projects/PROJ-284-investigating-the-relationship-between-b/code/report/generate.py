"""
Report generation module.
Implements T033.

Generates a comprehensive Markdown report including correlation results,
power analysis, and explicit limitation statements as per requirements.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from code.logging_config import get_logger

logger = get_logger(__name__)

def load_template(template_path: str) -> str:
    """Loads the report template from disk."""
    path = Path(template_path)
    if not path.exists():
        # Fallback to default template if custom one missing
        return """
# Research Report: Brain Network Dynamics and Sensorimotor Performance

## Executive Summary
This report presents the findings from the analysis of the relationship between 
brain network dynamics and individual differences in sensorimotor performance.

## Correlation Results

{{correlation_table}}

## Power Analysis

{{power_analysis}}

## Visualizations

{{plots}}

## Limitations

{{limitations}}

## Conclusion

{{conclusion}}
"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def format_correlation_table(df: pd.DataFrame) -> str:
    """Formats correlation table for Markdown with significant results highlighted."""
    if df.empty:
        return "No correlation results available."
    
    # Ensure required columns exist
    required_cols = ['metric_name', 'r', 'p', 'q', 'significant']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        return f"Correlation table missing required columns: {missing_cols}"
    
    # Format numeric columns
    formatted_df = df.copy()
    formatted_df['r'] = formatted_df['r'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
    formatted_df['p'] = formatted_df['p'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
    formatted_df['q'] = formatted_df['q'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
    formatted_df['significant'] = formatted_df['significant'].apply(
        lambda x: "Yes" if x else "No"
    )
    
    return formatted_df.to_markdown(index=False)

def format_power_analysis(report: str) -> str:
    """Formats power analysis report."""
    if not report or report.strip() == "":
        return "Power analysis not available."
    return report

def format_plots(plot_dir: str) -> str:
    """Formats plot references in Markdown."""
    if not os.path.exists(plot_dir):
        return "No visualization plots generated."
    
    plots_md = []
    for file in sorted(Path(plot_dir).glob("*.png")):
        plots_md.append(f"![{file.stem}]({file.name})")
    
    if not plots_md:
        return "No visualization plots found in the output directory."
    
    return "\n\n".join(plots_md)

def generate_conclusion(results: List[Dict], correlation_df: Optional[pd.DataFrame] = None) -> str:
    """
    Generates conclusion text with required phrases.
    
    CRITICAL: Must include 'associational relationship' or 'correlational evidence'.
    Must reference the limitation about motor task performance as a proxy.
    """
    significant_count = 0
    if correlation_df is not None and not correlation_df.empty:
        significant_count = correlation_df.get('significant', pd.Series(dtype=bool)).sum()
    
    base_conclusion = (
        "The analysis provides **correlational evidence** for an **associational relationship** "
        "between brain network dynamics (specifically Participation Coefficient and Within-Module Degree) "
        "and individual differences in sensorimotor performance. "
        f"Out of {len(results) if results else 'analyzed'} metrics, {significant_count} showed "
        "statistically significant correlations after FDR correction."
    )
    
    limitation_note = (
        "\n\n**Important Note on Interpretation:** "
        "While these findings suggest a link between network organization and performance, "
        "it is critical to acknowledge that **Motor Task Performance is a proxy for proprioceptive accuracy**. "
        "The observed associations may reflect broader sensorimotor integration capabilities rather than "
        "purely proprioceptive mechanisms."
    )
    
    return base_conclusion + limitation_note

def generate_report(
    correlation_df: pd.DataFrame, 
    power_report: str, 
    output_path: str,
    plots_dir: str = "figures"
) -> None:
    """
    Generates the full Markdown report.
    
    Args:
        correlation_df: DataFrame with correlation results (metric_name, r, p, q, significant)
        power_report: Text content of the power analysis
        output_path: Path to save the generated report
        plots_dir: Directory containing generated plots
    """
    # Load template
    template_path = "templates/report_template.md"
    template = load_template(template_path)
    
    # Format sections
    correlation_table_md = format_correlation_table(correlation_df)
    power_analysis_md = format_power_analysis(power_report)
    plots_md = format_plots(plots_dir)
    
    # Generate conclusion with required phrases
    conclusion_md = generate_conclusion([], correlation_df)
    
    # Limitations section (explicit requirement)
    limitations_md = (
        "## Limitations\n\n"
        "1. **Measurement Proxy**: Motor Task Performance is a proxy for proprioceptive accuracy. "
        "The behavioral measure used in this study captures general sensorimotor integration but "
        "may not isolate pure proprioceptive processing.\n\n"
        "2. **Associational Nature**: This study demonstrates an **associational relationship** between "
        "brain network metrics and performance. Causal inferences cannot be made from this cross-sectional "
        "correlational design.\n\n"
        "3. **Sample Characteristics**: The analysis relies on publicly available HCP data, which may "
        "limit generalizability to clinical populations or specific age groups.\n\n"
        "4. **Multiple Comparisons**: Despite FDR correction, the high-dimensional nature of network "
        "analysis increases the risk of Type I errors."
    )
    
    # Perform substitutions
    content = template
    content = content.replace("{{correlation_table}}", correlation_table_md)
    content = content.replace("{{power_analysis}}", power_analysis_md)
    content = content.replace("{{plots}}", plots_md)
    content = content.replace("{{limitations}}", limitations_md)
    content = content.replace("{{conclusion}}", conclusion_md)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.log(
        "generate_report",
        status="success",
        path=str(output_path),
        correlation_rows=len(correlation_df),
        timestamp=datetime.utcnow().isoformat()
    )

def main() -> None:
    """
    Main entry point for report generation.
    
    Reads correlation results and power analysis from disk,
    generates the full report, and saves to docs/report.md.
    """
    # Define paths
    corr_path = Path("data/analysis/correlations.csv")
    power_path = Path("data/analysis/power_analysis.txt")
    output_path = Path("docs/report.md")
    plots_dir = Path("figures")
    
    # Load correlation results
    if not corr_path.exists():
        logger.log(
            "report_main",
            status="error",
            message=f"Correlation results not found at {corr_path}"
        )
        print(f"Error: Correlation results not found at {corr_path}")
        sys.exit(1)
    
    try:
        correlation_df = pd.read_csv(corr_path)
        logger.log("report_main", status="info", message=f"Loaded {len(correlation_df)} correlation results")
    except Exception as e:
        logger.log("report_main", status="error", message=f"Failed to load correlations: {e}")
        print(f"Error loading correlation results: {e}")
        sys.exit(1)
    
    # Load power analysis
    power_report = "Power analysis not available."
    if power_path.exists():
        try:
            with open(power_path, "r", encoding="utf-8") as f:
                power_report = f.read()
            logger.log("report_main", status="info", message="Loaded power analysis report")
        except Exception as e:
            logger.log("report_main", status="warning", message=f"Failed to load power analysis: {e}")
    
    # Generate report
    try:
        generate_report(
            correlation_df=correlation_df,
            power_report=power_report,
            output_path=str(output_path),
            plots_dir=str(plots_dir)
        )
        print(f"Report successfully generated at {output_path}")
    except Exception as e:
        logger.log("report_main", status="error", message=f"Report generation failed: {e}")
        print(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
