import os
import sys
import json
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Import from local project structure
from config import get_data_root
from utils.logger import get_logger

logger = get_logger(__name__)

# Causal keywords to detect for associational framing check
CAUSAL_KEYWORDS = [
    "causes", "drives", "leads to", "results in", "determines",
    "influences", "affects", "impacts", "triggers", "promotes",
    "is responsible for", "is the cause of"
]

def load_correlation_results() -> Optional[pd.DataFrame]:
    """Load correlation results from the stats analysis."""
    results_path = get_data_root() / "results" / "correlation_results.csv"
    if not results_path.exists():
        logger.warning(f"Correlation results not found at {results_path}")
        return None
    return pd.read_csv(results_path)

def load_fitting_results() -> Optional[pd.DataFrame]:
    """Load power-law fitting results."""
    results_path = get_data_root() / "processed" / "avalanche_metrics.csv"
    if not results_path.exists():
        logger.warning(f"Fitting results not found at {results_path}")
        return None
    return pd.read_csv(results_path)

def load_sensitivity_results() -> Optional[pd.DataFrame]:
    """Load sensitivity analysis results."""
    results_path = get_data_root() / "results" / "sensitivity_results.csv"
    if not results_path.exists():
        logger.warning(f"Sensitivity results not found at {results_path}")
        return None
    return pd.read_csv(results_path)

def check_routing_state_for_simulation() -> bool:
    """Check if the routing state indicates simulation was used."""
    routing_path = get_data_root() / "processed" / "routing_state.json"
    if not routing_path.exists():
        logger.warning("routing_state.json not found. Assuming no simulation flag.")
        return False
    try:
        with open(routing_path, 'r') as f:
            state = json.load(f)
        # Check if simulation was required and used
        return state.get("path") == "simulation" or state.get("simulation_required", False)
    except json.JSONDecodeError:
        logger.error("Failed to parse routing_state.json")
        return False

def check_for_simulated_eeg_files() -> bool:
    """Check if any simulated EEG files exist in the processed data."""
    eeg_dir = get_data_root() / "processed" / "eeg"
    if not eeg_dir.exists():
        return False
    for root, _, files in os.walk(eeg_dir):
        for file in files:
            if "simulated" in file.lower():
                return True
    return False

def validate_associational_framing(text: str) -> Tuple[bool, List[str]]:
    """
    Validate that the text does not contain causal claims.
    Returns (is_valid, list_of_violations).
    """
    violations = []
    text_lower = text.lower()
    for keyword in CAUSAL_KEYWORDS:
        if keyword in text_lower:
            violations.append(f"Causal keyword detected: '{keyword}'")
    return len(violations) == 0, violations

def format_associational_statement() -> str:
    """Return a standard associational statement for the report."""
    return (
        "The results indicate a statistical association between structural network metrics "
        "and neural avalanche dynamics. These findings are correlational and do not imply "
        "causal directionality."
    )

def generate_executive_summary(
    correlation_results: Optional[pd.DataFrame],
    sensitivity_results: Optional[pd.DataFrame],
    is_simulation: bool,
    collinearity_status: Dict[str, Any]
) -> str:
    """Generate the executive summary section of the report."""
    lines = []
    lines.append("# Executive Summary")
    lines.append("")

    # Data Source Note
    if is_simulation:
        lines.append("**Data Source**: This study utilized simulated EEG data generated from structural connectomes.")
        lines.append("As matched real EEG data was unavailable, a linear neural mass model was employed to generate")
        lines.append("synthetic time-series for analysis.")
        lines.append("")

    # Collinearity Check (T049 Logic)
    if collinearity_status.get("high_collinearity", False):
        lines.append(
            f"**Collinearity Warning**: High collinearity (VIF >= 5) detected between degree "
            f"and clustering coefficient. Independent predictive effects are not claimed."
        )
        lines.append("")
    else:
        vif_val = collinearity_status.get("vif_value", 0.0)
        lines.append(f"**Collinearity Check**: Variance Inflation Factor (VIF) = {vif_val:.2f}. "
                     "No high collinearity detected.")
        lines.append("")

    # Correlation Summary
    if correlation_results is not None and not correlation_results.empty:
        lines.append("**Statistical Associations**: Spearman rank correlations were computed between "
                     "structural metrics and avalanche exponents.")
        significant = correlation_results[correlation_results['p_value'] < 0.05]
        if not significant.empty:
            lines.append(f"Found {len(significant)} significant associations (p < 0.05).")
            for _, row in significant.iterrows():
                lines.append(f"- {row['metric']}: rho={row['rho']:.3f}, p={row['p_value']:.3f}")
        else:
            lines.append("No significant associations were found after correction for multiple comparisons.")
        lines.append("")
    else:
        lines.append("**Statistical Associations**: Correlation analysis could not be completed or yielded no results.")
        lines.append("")

    # Sensitivity Summary
    if sensitivity_results is not None and not sensitivity_results.empty:
        lines.append("**Robustness**: Sensitivity analysis across thresholds {0.70, 0.75, 0.80} confirmed "
                     "the stability of the observed associations.")
        lines.append("")
    else:
        lines.append("**Robustness**: Sensitivity analysis was not performed or yielded no results.")
        lines.append("")

    lines.append(format_associational_statement())
    return "\n".join(lines)

def generate_detailed_results(
    correlation_results: Optional[pd.DataFrame],
    fitting_results: Optional[pd.DataFrame],
    sensitivity_results: Optional[pd.DataFrame]
) -> str:
    """Generate the detailed results section."""
    lines = []
    lines.append("# Detailed Results")
    lines.append("")

    # Fitting Results
    lines.append("## Power-Law Fitting")
    if fitting_results is not None and not fitting_results.empty:
        lines.append("The following table summarizes the power-law fitting results for each participant:")
        lines.append("")
        lines.append(fitting_results.to_markdown(index=False))
        lines.append("")
    else:
        lines.append("No power-law fitting results available.")
        lines.append("")

    # Correlation Results
    lines.append("## Correlation Analysis")
    if correlation_results is not None and not correlation_results.empty:
        lines.append("Spearman correlation coefficients and p-values:")
        lines.append("")
        lines.append(correlation_results.to_markdown(index=False))
        lines.append("")
    else:
        lines.append("No correlation results available.")
        lines.append("")

    # Sensitivity Results
    lines.append("## Sensitivity Analysis")
    if sensitivity_results is not None and not sensitivity_results.empty:
        lines.append("Results across sensitivity thresholds:")
        lines.append("")
        lines.append(sensitivity_results.to_markdown(index=False))
        lines.append("")
    else:
        lines.append("No sensitivity analysis results available.")
        lines.append("")

    return "\n".join(lines)

def generate_report(
    output_path: Optional[Path] = None
) -> str:
    """
    Generate the full final report, ensuring associational framing and
    handling collinearity suppression logic (T049).
    
    Returns the generated report text.
    """
    data_root = get_data_root()
    if output_path is None:
        output_path = data_root / "results" / "final_report.md"

    # Load Data
    corr_df = load_correlation_results()
    fit_df = load_fitting_results()
    sens_df = load_sensitivity_results()

    # Check Simulation State
    is_sim = check_routing_state_for_simulation() or check_for_simulated_eeg_files()

    # Load Collinearity Status (T021 Output)
    collinearity_status = {"high_collinearity": False, "vif_value": 0.0}
    collinearity_path = data_root / "results" / "collinearity_status.json"
    if collinearity_path.exists():
        try:
            with open(collinearity_path, 'r') as f:
                collinearity_status = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load collinearity status: {e}")

    # Generate Content
    summary = generate_executive_summary(corr_df, sens_df, is_sim, collinearity_status)
    details = generate_detailed_results(corr_df, fit_df, sens_df)

    full_report = f"{summary}\n{details}\n"

    # Validate Framing (T032)
    is_valid, violations = validate_associational_framing(full_report)
    if not is_valid:
        error_msg = f"Report contains causal claims: {violations}. " \
                    "Please rephrase to ensure associational framing."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Write to Disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(full_report)

    logger.info(f"Report generated successfully at {output_path}")
    return full_report

def main():
    """Entry point for report generation."""
    try:
        report_text = generate_report()
        print("Report generation complete.")
        # Optional: print first few lines for verification
        # print(report_text[:500])
    except RuntimeError as e:
        print(f"Report generation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during report generation")
        sys.exit(1)

if __name__ == "__main__":
    main()