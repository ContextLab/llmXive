"""
T027: Generate a markdown report summarizing thresholds and sensitivity results.

This module reads the output from T026 (us2_threshold_candidates.json) and
generates a human-readable Markdown report at:
data/results/us2_threshold_report.md

The report includes:
1. Identified Threshold (breakpoint location and model preference)
2. Sensitivity Sweep Results (table of perturbation magnitudes vs. threshold shifts)
3. Dataset Perturbation Results (bootstrap distribution summary)
4. Justification for the selected model/threshold
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import from existing API surface
from analysis.threshold import load_threshold_candidates, load_correlation_stats
from config import get_project_root, get_config

logger = logging.getLogger(__name__)

def load_feasibility_report() -> Dict[str, Any]:
    """Load the feasibility report to get perturbation parameters."""
    project_root = get_project_root()
    path = project_root / "data" / "results" / "feasibility_report.json"
    if not path.exists():
        raise FileNotFoundError(f"Feasibility report not found at {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Generate a Markdown table from headers and rows."""
    if not rows:
        return "No data available."
    
    # Calculate column widths
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(str(header))
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width)
    
    lines = []
    # Header
    header_line = "| " + " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    lines.append(header_line)
    # Separator
    sep_line = "| " + " | ".join("-" * w for w in col_widths) + " |"
    lines.append(sep_line)
    # Rows
    for row in rows:
        row_line = "| " + " | ".join(str(val).ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i]) for i, val in enumerate(row)) + " |"
        lines.append(row_line)
    
    return "\n".join(lines)

def generate_report_content(
    threshold_data: Dict[str, Any],
    correlation_data: Dict[str, Any],
    feasibility_data: Dict[str, Any]
) -> str:
    """Generate the full Markdown report content."""
    report_lines = []
    
    # Title and Metadata
    report_lines.append("# Threshold Detection and Sensitivity Analysis Report")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Project:** llmXive follow-up: extending Mellum2 Technical Report")
    report_lines.append("")
    
    # Section 1: Identified Threshold
    report_lines.append("## 1. Identified Threshold")
    report_lines.append("")
    
    model_preference = threshold_data.get("model_preference", {})
    threshold_value = model_preference.get("preferred_threshold", "N/A")
    preferred_model = model_preference.get("preferred_model", "N/A")
    aic_bic_diff = model_preference.get("improvement", "N/A")
    
    report_lines.append(f"- **Preferred Model:** {preferred_model}")
    report_lines.append(f"- **Identified Threshold (Breakpoint):** {threshold_value}")
    report_lines.append(f"- **Model Improvement (AIC/BIC difference):** {aic_bic_diff}")
    report_lines.append("")
    
    if "threshold_candidates" in threshold_data:
        candidates = threshold_data["threshold_candidates"]
        if candidates:
            report_lines.append("### Candidate Thresholds")
            report_lines.append("")
            cand_headers = ["Candidate Index", "Threshold Value", "AIC", "BIC", "Slope Change"]
            cand_rows = []
            for i, cand in enumerate(candidates):
                cand_rows.append([
                    i,
                    f"{cand.get('threshold', 'N/A'):.4f}",
                    f"{cand.get('aic', 'N/A'):.2f}",
                    f"{cand.get('bic', 'N/A'):.2f}",
                    f"{cand.get('slope_change', 'N/A'):.4f}"
                ])
            report_lines.append(format_table(cand_headers, cand_rows))
            report_lines.append("")
    
    # Section 2: Sensitivity Sweep Results
    report_lines.append("## 2. Sensitivity Sweep Results")
    report_lines.append("")
    report_lines.append("The following table shows the shift in the identified threshold")
    report_lines.append("when the input data is perturbed by varying magnitudes.")
    report_lines.append("")
    
    sweep_data = threshold_data.get("threshold_shifts_by_magnitude", [])
    if sweep_data:
        sweep_headers = ["Perturbation Magnitude", "Threshold Shift (Delta)", "Direction"]
        sweep_rows = []
        for entry in sweep_data:
            mag = entry.get("magnitude", 0)
            shift = entry.get("delta", 0)
            direction = "Increase" if shift > 0 else ("Decrease" if shift < 0 else "No Change")
            sweep_rows.append([
                f"{mag:.4f}",
                f"{shift:.4f}",
                direction
            ])
        report_lines.append(format_table(sweep_headers, sweep_rows))
    else:
        report_lines.append("No sensitivity sweep data available.")
    report_lines.append("")
    
    # Section 3: Dataset Perturbation (Bootstrap) Results
    report_lines.append("## 3. Dataset Perturbation Results (Bootstrap)")
    report_lines.append("")
    report_lines.append("Distribution of threshold shifts obtained from bootstrap resampling.")
    report_lines.append("")
    
    bootstrap_data = threshold_data.get("dataset_perturbation_shifts", {})
    if bootstrap_data:
        count = bootstrap_data.get("count", 0)
        mean_shift = bootstrap_data.get("mean", 0)
        std_shift = bootstrap_data.get("std", 0)
        median_shift = bootstrap_data.get("median", 0)
        min_shift = bootstrap_data.get("min", 0)
        max_shift = bootstrap_data.get("max", 0)
        
        report_lines.append(f"- **Bootstrap Samples:** {count}")
        report_lines.append(f"- **Mean Shift:** {mean_shift:.4f}")
        report_lines.append(f"- **Standard Deviation:** {std_shift:.4f}")
        report_lines.append(f"- **Median Shift:** {median_shift:.4f}")
        report_lines.append(f"- **Range:** [{min_shift:.4f}, {max_shift:.4f}]")
        report_lines.append("")
        
        # If percentiles are available
        if "percentiles" in bootstrap_data:
            percs = bootstrap_data["percentiles"]
            report_lines.append("### Percentiles")
            report_lines.append("")
            perc_headers = ["Percentile", "Shift Value"]
            perc_rows = []
            for key in sorted(percs.keys()):
                perc_rows.append([key, f"{percs[key]:.4f}"])
            report_lines.append(format_table(perc_headers, perc_rows))
            report_lines.append("")
    else:
        report_lines.append("No bootstrap perturbation data available.")
    report_lines.append("")
    
    # Section 4: Justification
    report_lines.append("## 4. Justification")
    report_lines.append("")
    
    report_lines.append("### Model Selection")
    if preferred_model == "piecewise_linear":
        report_lines.append("The piecewise linear model was selected over the linear model based on")
        report_lines.append("information criteria (AIC/BIC). The significant improvement in fit")
        report_lines.append("suggests a non-linear relationship between code complexity and prediction loss.")
        report_lines.append(f"The identified breakpoint at **{threshold_value}** indicates a structural shift")
        report_lines.append("in how complexity impacts model performance.")
    elif preferred_model == "linear":
        report_lines.append("The linear model was preferred based on AIC/BIC, suggesting that")
        report_lines.append("within the observed range, the relationship between complexity and loss")
        report_lines.append("is adequately described by a linear trend. The threshold detection")
        report_lines.append("did not find a statistically significant breakpoint.")
    else:
        report_lines.append("Model preference could not be determined.")
    report_lines.append("")
    
    report_lines.append("### Sensitivity Analysis")
    if sweep_data:
        max_shift = max(abs(entry.get("delta", 0)) for entry in sweep_data)
        if max_shift < 0.01: # Arbitrary small threshold for stability
            report_lines.append("The identified threshold is **stable** across the range of perturbation magnitudes.")
            report_lines.append("Small changes in the input data do not significantly alter the breakpoint location.")
        else:
            report_lines.append("The identified threshold shows **moderate sensitivity** to data perturbations.")
            report_lines.append("The stability of the threshold should be interpreted with caution, especially")
            report_lines.append("in regions where the complexity distribution is sparse.")
    else:
        report_lines.append("Sensitivity analysis was not performed or returned no results.")
    report_lines.append("")
    
    if bootstrap_data and bootstrap_data.get("count", 0) > 0:
        std_val = bootstrap_data.get("std", 0)
        if std_val < 0.01:
            report_lines.append("The bootstrap analysis confirms the stability of the threshold estimate.")
        else:
            report_lines.append("The bootstrap distribution indicates some variability in the threshold estimate.")
            report_lines.append("The confidence interval for the threshold should be considered when drawing conclusions.")
    report_lines.append("")
    
    # Footer
    report_lines.append("---")
    report_lines.append("*End of Report*")
    
    return "\n".join(report_lines)

def write_report(content: str, output_path: Path) -> None:
    """Write the report content to the specified path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Report written to {output_path}")

def main() -> int:
    """Main entry point for T027."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        project_root = get_project_root()
        
        # Load inputs
        logger.info("Loading threshold candidates...")
        threshold_data = load_threshold_candidates()
        
        logger.info("Loading correlation stats...")
        correlation_data = load_correlation_stats()
        
        logger.info("Loading feasibility report...")
        feasibility_data = load_feasibility_report()
        
        # Generate report
        logger.info("Generating report content...")
        report_content = generate_report_content(
            threshold_data,
            correlation_data,
            feasibility_data
        )
        
        # Write output
        output_path = project_root / "data" / "results" / "us2_threshold_report.md"
        write_report(report_content, output_path)
        
        logger.info("T027 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON input: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())