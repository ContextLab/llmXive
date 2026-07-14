"""
Report generation module.
Implements T033: Markdown/PDF assembly with specific limitation and conclusion phrasing.
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
    """Loads the report template from the specified path."""
    path = Path(template_path)
    if not path.exists():
        # Fallback to inline template if file missing, but prefer file
        logger.log("load_template", path=str(path), status="fallback")
        return """
        # Research Report: Brain Network Dynamics

        ## Correlation Results
        {{correlation_table}}

        ## Power Analysis
        {{power_analysis}}

        ## Plots
        {{plots}}

        ## Limitations
        {{limitations}}

        ## Conclusion
        {{conclusion}}
        """
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def format_correlation_table(df: pd.DataFrame) -> str:
    """Formats correlation table for Markdown."""
    if df.empty:
        return "No correlation data available."
    return df.to_markdown(index=False)

def format_power_analysis(report: str) -> str:
    """Formats power analysis results."""
    return report if report else "Power analysis not performed."

def format_plots(plot_dir: str) -> str:
    """Formats plot references as Markdown image links."""
    if not os.path.exists(plot_dir):
        return "No plots generated."
    
    plots = []
    for file in sorted(Path(plot_dir).glob("*.png")):
        plots.append(f"![{file.stem}]({file.name})")
    
    if not plots:
        return "No plots found in directory."
    
    return "\n\n".join(plots)

def generate_conclusion(results: List[Dict]) -> str:
    """
    Generates conclusion text based on correlation results.
    CRITICAL: Must include 'associational relationship' or 'correlational evidence'
    if significant correlations are found.
    """
    significant_count = 0
    if results:
        significant_count = sum(
            1 for r in results 
            if r.get('significant', False) or r.get('q', 1.0) < 0.05
        )

    base_text = (
        "This study investigated the relationship between brain network dynamics "
        "and individual differences in sensorimotor performance."
    )

    if significant_count > 0:
        return (
            f"{base_text} The analysis reveals significant associations, "
            "providing **correlational evidence** for an **associational relationship** "
            "between specific network metrics and motor performance scores. "
            f"Specifically, {significant_count} metric(s) showed significant correlations "
            "after FDR correction."
        )
    else:
        return (
            f"{base_text} No significant associations were detected after FDR correction. "
            "While this does not rule out a relationship, the current data does not provide "
            "sufficient **correlational evidence** to support a strong **associational relationship** "
            "between the measured network dynamics and sensorimotor performance."
        )

def generate_report(
    correlation_df: pd.DataFrame,
    power_report: str,
    output_path: str,
    plot_dir: Optional[str] = None,
    limitation_text: Optional[str] = None
) -> None:
    """
    Generates the full Markdown report.
    
    Args:
        correlation_df: DataFrame with correlation results (metric_name, r, p, q, significant).
        power_report: String containing power analysis details.
        output_path: Path to save the generated report.
        plot_dir: Directory containing generated plots (optional).
        limitation_text: Custom limitation text (optional, defaults to required phrase).
    """
    # Default limitation statement as per requirements
    if limitation_text is None:
        limitation_text = (
            "**Limitation Statement:** Motor Task Performance is a proxy for proprioceptive accuracy. "
            "This study relies on correlational data, which cannot establish causality. "
            "The observed relationships may be influenced by unmeasured confounding variables."
        )

    # Load template
    template_path = "templates/report_template.md"
    template = load_template(template_path)

    # Prepare variables
    corr_table_md = format_correlation_table(correlation_df)
    plots_md = format_plots(plot_dir) if plot_dir else ""
    conclusion_md = generate_conclusion(correlation_df.to_dict('records'))

    # Render template
    content = template
    content = content.replace("{{correlation_table}}", corr_table_md)
    content = content.replace("{{power_analysis}}", power_report)
    content = content.replace("{{plots}}", plots_md)
    content = content.replace("{{limitations}}", limitation_text)
    content = content.replace("{{conclusion}}", conclusion_md)

    # Write file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.log(
        "generate_report", 
        output=str(output_file),
        rows=len(correlation_df),
        status="success"
    )

def main():
    """Main runner for report generation.
    
    Reads correlation results and power analysis, then generates the final report.
    """
    # Paths relative to project root
    corr_path = Path("data/analysis/correlations.csv")
    power_path = Path("data/analysis/power_analysis.txt")
    plot_dir = Path("figures")
    output_path = Path("docs/report.md")

    # Validate inputs
    if not corr_path.exists():
        logger.log("report_main", error="Correlation results not found", path=str(corr_path))
        print(f"Error: {corr_path} not found. Run correlations step first.")
        sys.exit(1)

    # Load data
    try:
        df = pd.read_csv(corr_path)
    except Exception as e:
        logger.log("report_main", error=f"Failed to load CSV: {e}")
        sys.exit(1)

    # Load power analysis if available
    power_report = "Power analysis not available."
    if power_path.exists():
        try:
            with open(power_path, "r") as f:
                power_report = f.read()
        except Exception as e:
            logger.log("report_main", warning=f"Could not read power analysis: {e}")

    # Generate report
    generate_report(
        correlation_df=df,
        power_report=power_report,
        output_path=str(output_path),
        plot_dir=str(plot_dir)
    )

    print(f"Report generated: {output_path}")

if __name__ == "__main__":
    main()
