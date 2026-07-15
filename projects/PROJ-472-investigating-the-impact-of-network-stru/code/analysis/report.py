import os
import sys
import json
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

# Local imports matching the provided API surface
from config import get_data_root
from utils.logger import get_logger, AnalysisError

# Initialize logger
logger = get_logger(__name__)

# Causal keywords to enforce associational framing (FR-010)
CAUSAL_KEYWORDS = [
    "causes", "caused", "cause", "causing",
    "drives", "driven", "drive", "driving",
    "leads to", "led to",
    "determines", "determined",
    "results in", "resulted in",
    "induces", "induced",
    "forces", "forced",
    "triggers", "triggered",
    "influences"  # Often ambiguous, but flagged for review in strict associational context if used as direct causation
]

def load_correlation_results() -> Dict[str, Any]:
    """Loads correlation analysis results from the stored CSV."""
    data_root = get_data_root()
    results_path = data_root / "results" / "correlation_report.csv"
    
    if not results_path.exists():
        logger.warning(f"Correlation results file not found at {results_path}. Returning empty dict.")
        return {}
    
    try:
        df = pd.read_csv(results_path)
        # Convert to list of dicts for easier processing if needed
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        raise

def load_fitting_results() -> Dict[str, Any]:
    """Loads power-law fitting results."""
    data_root = get_data_root()
    results_path = data_root / "results" / "fitting_results.json"
    
    if not results_path.exists():
        logger.warning(f"Fitting results file not found at {results_path}. Returning empty dict.")
        return {}
    
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load fitting results: {e}")
        raise

def load_sensitivity_results() -> Dict[str, Any]:
    """Loads sensitivity analysis results."""
    data_root = get_data_root()
    results_path = data_root / "results" / "sensitivity_analysis.json"
    
    if not results_path.exists():
        logger.warning(f"Sensitivity results file not found at {results_path}. Returning empty dict.")
        return {}
    
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load sensitivity results: {e}")
        raise

def format_associational_statement(metric_name: str, correlation: float, p_value: float) -> str:
    """
    Formats a statistical finding as an associational statement.
    Explicitly avoids causal language.
    """
    direction = "positive" if correlation > 0 else "negative"
    significance = "statistically significant" if p_value < 0.05 else "not statistically significant"
    
    return (
        f"A {direction} correlation was observed between {metric_name} and the avalanche exponent "
        f"(r = {correlation:.3f}, p = {p_value:.4f}). This association is {significance}."
    )

def generate_executive_summary(results: Dict[str, Any]) -> str:
    """Generates a high-level summary of the findings."""
    if not results:
        return "No correlation results available to summarize."
    
    summary_parts = []
    for item in results:
        metric = item.get('metric', 'Unknown Metric')
        corr = item.get('correlation', 0.0)
        p_val = item.get('p_value', 1.0)
        
        statement = format_associational_statement(metric, corr, p_val)
        summary_parts.append(statement)
    
    return "\n\n".join(summary_parts)

def generate_detailed_results(correlation_data: List[Dict], fitting_data: Dict, sensitivity_data: Dict) -> str:
    """Generates the detailed body of the report."""
    lines = []
    lines.append("## Detailed Results")
    lines.append("")
    
    lines.append("### Structural-Avalanche Associations")
    for item in correlation_data:
        metric = item.get('metric', 'N/A')
        corr = item.get('correlation', 'N/A')
        p_val = item.get('p_value', 'N/A')
        ci_low = item.get('ci_low', 'N/A')
        ci_high = item.get('ci_high', 'N/A')
        
        lines.append(f"- **{metric}**: r={corr}, p={p_val}, 95% CI [{ci_low}, {ci_high}]")
    
    lines.append("")
    lines.append("### Power-Law Fit Quality")
    # Assuming fitting_data is a dict of subject_id -> stats or similar structure
    if isinstance(fitting_data, dict):
        count = len(fitting_data)
        lines.append(f"- Analyzed {count} subjects for power-law fit convergence.")
    
    lines.append("")
    lines.append("### Sensitivity Analysis")
    if sensitivity_data:
        lines.append("- Stability of exponents across thresholds (0.70, 0.75, 0.80) was assessed.")
    else:
        lines.append("- No sensitivity data available.")
        
    return "\n".join(lines)

def _validate_text_for_causal_language(text: str) -> None:
    """
    Scans text for causal keywords. Raises RuntimeError if found.
    This enforces FR-010 and US-3 requirements.
    """
    text_lower = text.lower()
    found_causal = []
    
    for keyword in CAUSAL_KEYWORDS:
        # Use word boundaries to avoid false positives on substrings (e.g., "causes" inside "precursors")
        # Simple regex check for the keyword surrounded by non-word chars or start/end
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            found_causal.append(keyword)
    
    if found_causal:
        unique_found = list(set(found_causal))
        raise RuntimeError(
            f"Associational Framing Violation: The report text contains causal language "
            f"which is forbidden by FR-010. Found keywords: {unique_found}. "
            f"Please rephrase the generated text to use associational terms (e.g., 'associated with', 'correlated with')."
        )

def generate_report(output_path: Optional[Path] = None) -> Path:
    """
    Generates the final research report, validating for associational framing.
    
    Steps:
    1. Load results.
    2. Generate text content.
    3. VALIDATE: Scan for causal keywords.
    4. Write to file.
    """
    data_root = get_data_root()
    if output_path is None:
        output_path = data_root / "results" / "final_report.md"
    
    logger.info("Generating final research report...")
    
    # Load data
    correlation_data = load_correlation_results()
    fitting_data = load_fitting_results()
    sensitivity_data = load_sensitivity_results()
    
    # Generate content
    executive_summary = generate_executive_summary(correlation_data)
    detailed_results = generate_detailed_results(correlation_data, fitting_data, sensitivity_data)
    
    # Construct full report text
    report_content = [
        "# Neural Avalanche Dynamics and Network Structure Report",
        "",
        "## Executive Summary",
        executive_summary,
        "",
        detailed_results,
        "",
        "## Conclusion",
        "This study investigated the association between structural network properties and neural avalanche dynamics. "
        "All findings are presented as correlational associations and do not imply causal directionality."
    ]
    
    full_text = "\n".join(report_content)
    
    # VALIDATION STEP: Enforce Associational Framing (T032)
    logger.info("Validating report for causal language compliance...")
    try:
        _validate_text_for_causal_language(full_text)
        logger.info("Associational framing validation passed.")
    except RuntimeError as e:
        logger.error(f"Validation failed: {e}")
        raise e
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    logger.info(f"Report successfully generated and validated at {output_path}")
    return output_path

def main():
    """Entry point for the report generation script."""
    try:
        output_file = generate_report()
        print(f"Report generated: {output_file}")
    except RuntimeError as e:
        # Re-raise the validation error so the pipeline halts
        print(f"Report generation failed due to validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()