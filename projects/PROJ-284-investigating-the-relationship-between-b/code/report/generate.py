"""Report generation."""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import get_logger

logger = get_logger(__name__)


def load_template(template_path: str = "templates/report_template.md") -> str:
    """Load report template."""
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            return f.read()
    return ""


def format_correlation_table(correlations_csv: Optional[str] = None) -> str:
    """Format correlation results as table."""
    if correlations_csv is None or not os.path.exists(correlations_csv):
        return "No correlation data available."

    import pandas as pd
    df = pd.read_csv(correlations_csv)
    return df.to_markdown(index=False)


def format_power_analysis(power_csv: Optional[str] = None) -> str:
    """Format power analysis results."""
    if power_csv is None or not os.path.exists(power_csv):
        return "No power analysis data available."

    import pandas as pd
    df = pd.read_csv(power_csv)
    return df.to_markdown(index=False)


def format_plots(plot_dir: Optional[str] = None) -> str:
    """Format plot references."""
    if plot_dir is None or not os.path.exists(plot_dir):
        return "No plots generated."

    plots = []
    for f in os.listdir(plot_dir):
        if f.endswith('.png'):
            plots.append(f"![{f}]({os.path.join(plot_dir, f)})")
    return "\n".join(plots) if plots else "No plots found."


def generate_conclusion(has_significant_correlations: bool = False) -> str:
    """Generate conclusion section."""
    base_text = "This analysis examined the associational relationship between brain network metrics and motor task performance."

    if has_significant_correlations:
        return base_text + " Significant correlational evidence was found for certain network metrics."
    else:
        return base_text + " No significant correlational evidence was found."


def generate_report(
    output_path: str = "docs/report.md",
    correlations_csv: Optional[str] = None,
    power_csv: Optional[str] = None,
    plot_dir: Optional[str] = None
) -> None:
    """Generate comprehensive report."""
    logger.info("Generating report")

    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Load template or create basic report
    template = load_template()

    if not template:
        # Create basic report
        report_content = f"""# Brain Network Analysis Report

Generated: {datetime.now().isoformat()}

## Executive Summary

This report presents the results of analyzing the relationship between brain network dynamics and individual differences in sensorimotor performance.

## Methods

- **Data Source**: ADHD-200 dataset via nilearn
- **Atlas**: Schaefer 400-node parcellation
- **Analysis**: Correlation analysis with FDR correction

## Results

### Correlation Analysis

{format_correlation_table(correlations_csv)}

### Power Analysis

{format_power_analysis(power_csv)}

## Visualizations

{format_plots(plot_dir)}

## Limitations

Motor Task Performance is a proxy for proprioceptive accuracy.

## Conclusion

{generate_conclusion()}
"""
    else:
        report_content = template
        report_content = report_content.replace("{{correlation_table}}", format_correlation_table(correlations_csv))
        report_content = report_content.replace("{{power_analysis}}", format_power_analysis(power_csv))
        report_content = report_content.replace("{{plots}}", format_plots(plot_dir))
        report_content = report_content.replace("{{limitations}}", "Motor Task Performance is a proxy for proprioceptive accuracy.")
        report_content = report_content.replace("{{conclusion}}", generate_conclusion())

    # Write report
    with open(output_path, 'w') as f:
        f.write(report_content)

    logger.info(f"Saved report to {output_path}")


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate report")
    parser.add_argument("--correlations", help="Correlations CSV")
    parser.add_argument("--power", help="Power analysis CSV")
    parser.add_argument("--plots", help="Plots directory")
    parser.add_argument("--output", default="docs/report.md", help="Output report path")

    args = parser.parse_args()

    generate_report(
        output_path=args.output,
        correlations_csv=args.correlations,
        power_csv=args.power,
        plot_dir=args.plots
    )


if __name__ == "__main__":
    main()