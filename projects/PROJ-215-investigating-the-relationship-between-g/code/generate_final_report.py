import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime

from code.config import get_output_path
from code.utils.logging import get_logger

logger = get_logger(__name__)

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not path.exists():
        logger.warning(f"JSON file not found: {path}")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading JSON {path}: {e}")
        return None

def load_csv_safe(path: Path) -> Optional[pd.DataFrame]:
    """Load a CSV file safely, returning None if it doesn't exist or is invalid."""
    if not path.exists():
        logger.warning(f"CSV file not found: {path}")
        return None
    try:
        return pd.read_csv(path)
    except (pd.errors.EmptyDataError, IOError) as e:
        logger.error(f"Error loading CSV {path}: {e}")
        return None

def format_section(title: str, content: str) -> str:
    """Format a section with a header and content."""
    return f"\n{'='*60}\n{title}\n{'='*60}\n{content}\n"

def generate_final_report(
    association_results: Optional[pd.DataFrame],
    covariate_check: Optional[Dict[str, Any]],
    ks_test_results: Optional[Dict[str, Any]],
    validation_results: Optional[Dict[str, Any]],
    validation_report_text: Optional[str],
    metrics: Optional[Dict[str, Any]]
) -> str:
    """
    Generate the final project report summarizing all findings, data gaps,
    and success criteria status.
    """
    report_parts = []
    report_parts.append(f"Final Project Report: Gut Microbiome and Mental Health")
    report_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Section 1: Executive Summary
    exec_summary = []
    if association_results is not None and not association_results.empty:
        sig_taxa = association_results[association_results['qval'] < 0.05]
        exec_summary.append(f"- Significant taxa found: {len(sig_taxa)}")
    else:
        exec_summary.append("- No significant taxa identified (data not available).")
    
    if covariate_check:
        exec_summary.append(f"- Covariate adjustment check (SC-005): {'PASS' if covariate_check.get('threshold_met') else 'FAIL'}")
    else:
        exec_summary.append("- Covariate adjustment check: SKIPPED (no data)")
    
    if ks_test_results:
        exec_summary.append(f"- KS Test for uniformity (SC-002): {ks_test_results.get('result', 'UNKNOWN').upper()}")
    else:
        exec_summary.append("- KS Test for uniformity: SKIPPED (no data)")
    
    if validation_report_text:
        # Extract pass/fail from validation text if possible
        if "PASS" in validation_report_text:
            exec_summary.append("- Independent Cohort Validation (SC-003): PASS")
        elif "Not Applicable" in validation_report_text or "Skipped" in validation_report_text:
            exec_summary.append("- Independent Cohort Validation (SC-003): Not Applicable")
        else:
            exec_summary.append("- Independent Cohort Validation (SC-003): FAIL or PENDING")
    else:
        exec_summary.append("- Independent Cohort Validation: No report available")
    
    report_parts.append(format_section("1. Executive Summary", "\n".join(exec_summary)))

    # Section 2: Association Analysis Results
    assoc_text = []
    if association_results is not None and not association_results.empty:
        sig_df = association_results[association_results['qval'] < 0.05]
        if not sig_df.empty:
            assoc_text.append(f"Found {len(sig_df)} significant associations (q < 0.05):")
            for _, row in sig_df.iterrows():
                direction = "increased" if row.get('direction') == 'positive' else "decreased"
                assoc_text.append(f"  - {row['taxon']}: {direction} with mental health score (r={row.get('coef', 0):.3f}, q={row.get('qval', 0):.3f})")
        else:
            assoc_text.append("No significant taxa found at q < 0.05 threshold.")
    else:
        assoc_text.append("Association results not available.")
    report_parts.append(format_section("2. Statistical Association Results", "\n".join(assoc_text)))

    # Section 3: Success Criteria Checks
    checks_text = []
    
    # SC-005: Covariate Adjustment
    if covariate_check:
        status = "PASS" if covariate_check.get('threshold_met') else "FAIL"
        max_delta = covariate_check.get('max_delta', 0)
        checks_text.append(f"SC-005 (Covariate Adjustment Impact): {status}")
        checks_text.append(f"  - Max delta (|p_adj - p_unadj|): {max_delta:.4f}")
        checks_text.append(f"  - Threshold (> 0.01): {'Met' if max_delta > 0.01 else 'Not Met'}")
    else:
        checks_text.append("SC-005: Not executed (missing data).")
    
    # SC-002: KS Test
    if ks_test_results:
        status = "PASS" if ks_test_results.get('result') == 'pass' else "FAIL"
        p_val = ks_test_results.get('p_value', 0)
        checks_text.append(f"SC-002 (Distribution of P-values): {status}")
        checks_text.append(f"  - KS Statistic: {ks_test_results.get('statistic', 0):.4f}")
        checks_text.append(f"  - P-value vs Uniform: {p_val:.4f}")
    else:
        checks_text.append("SC-002: Not executed (no significant taxa to test or missing data).")
    
    # SC-003: Validation
    if validation_report_text:
        checks_text.append("SC-003 (Independent Cohort Validation):")
        # Simple parsing of the validation report text for status
        if "PASS" in validation_report_text:
            checks_text.append("  - Result: PASS")
        elif "Not Applicable" in validation_report_text:
            checks_text.append("  - Result: Not Applicable (No independent cohort available)")
        elif "FAIL" in validation_report_text or "skipped" in validation_report_text.lower():
            checks_text.append("  - Result: FAIL or SKIPPED")
        else:
            checks_text.append("  - Result: Pending review of validation report.")
    else:
        checks_text.append("SC-003: No validation report available.")
    
    report_parts.append(format_section("3. Success Criteria Status", "\n".join(checks_text)))

    # Section 4: Data Gaps and Limitations
    gaps_text = []
    if metrics:
        if 'retention_rate' in metrics:
            gaps_text.append(f"- Data Retention: {metrics['retention_rate']:.1f}% of initial samples retained.")
        if 'total_runtime_hours' in metrics:
            gaps_text.append(f"- Pipeline Runtime: {metrics['total_runtime_hours']:.2f} hours.")
    else:
        gaps_text.append("- Metrics data not available.")
    
    if not (association_results is not None and not association_results.empty):
        gaps_text.append("- Limitation: No significant associations were found to validate.")
    
    if not validation_report_text:
        gaps_text.append("- Limitation: Independent cohort validation could not be performed or reported.")
    
    report_parts.append(format_section("4. Data Gaps and Limitations", "\n".join(gaps_text)))

    # Section 5: Detailed Validation Report (if available)
    if validation_report_text:
        report_parts.append(format_section("5. Independent Cohort Validation Details", validation_report_text))

    return "\n".join(report_parts)

def main():
    """Main entry point for generating the final project report."""
    logger.info("Starting final report generation (T036)...")
    
    # Define paths
    results_dir = Path(get_output_path("results"))
    interim_dir = Path(get_output_path("data/interim"))
    processed_dir = Path(get_output_path("data/processed"))
    
    # Load inputs
    # T025: association_results.csv
    assoc_path = processed_dir / "association_results.csv"
    association_results = load_csv_safe(assoc_path)
    
    # T023: covariate_delta.json
    covariate_path = results_dir / "covariate_delta.json"
    covariate_check = load_json_safe(covariate_path)
    
    # T024: ks_test_results.json
    ks_path = processed_dir / "ks_test_results.json"
    ks_test_results = load_json_safe(ks_path)
    
    # T032a/T032b: validation_report.txt
    validation_path = results_dir / "validation_report.txt"
    validation_report_text = None
    if validation_path.exists():
        try:
            with open(validation_path, 'r') as f:
                validation_report_text = f.read()
        except IOError as e:
            logger.error(f"Could not read validation report: {e}")
    
    # Metrics (from T037, though T037 is pending, we try to load if it exists)
    metrics_path = results_dir / "metrics.json"
    metrics = load_json_safe(metrics_path)
    
    # Generate report
    report_content = generate_final_report(
        association_results=association_results,
        covariate_check=covariate_check,
        ks_test_results=ks_test_results,
        validation_results=None, # We use the text directly
        validation_report_text=validation_report_text,
        metrics=metrics
    )
    
    # Write output
    output_path = results_dir / "final_project_report.txt"
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Final report generated successfully at: {output_path}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
