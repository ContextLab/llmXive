import os
import sys
import json
import csv
import logging
from pathlib import Path
from datetime import datetime

# Ensure we can import from the code directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA_RESULTS_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_exclusion_log(log_path: Path) -> list:
    """
    Load the exclusion log from T024/T032.
    Returns a list of dictionaries with exclusion details.
    """
    excluded_ids = []
    if not log_path.exists():
        logger.warning(f"Exclusion log not found at {log_path}. Assuming no exclusions.")
        return excluded_ids

    try:
        with open(log_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Expected format: "REALIZATION_ID: REASON" or JSON
                if line.startswith('{'):
                    try:
                        excluded_ids.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse exclusion line as JSON: {line}")
                        # Fallback: treat as text
                        excluded_ids.append({"id": line, "reason": "parse_error"})
                else:
                    # Simple text format
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        excluded_ids.append({"id": parts[0].strip(), "reason": parts[1].strip()})
                    else:
                        excluded_ids.append({"id": line, "reason": "unknown"})
    except Exception as e:
        logger.error(f"Error reading exclusion log: {e}")
        raise

    return excluded_ids

def load_robustness_failures(log_path: Path) -> list:
    """
    Load the robustness failures log from T041.
    Returns a list of dictionaries with failure details.
    """
    failures = []
    if not log_path.exists():
        logger.warning(f"Robustness failures log not found at {log_path}. Assuming no failures.")
        return failures

    try:
        with open(log_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('{'):
                    try:
                        failures.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse robustness failure as JSON: {line}")
                        failures.append({"id": line, "reason": "parse_error"})
                else:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        failures.append({"id": parts[0].strip(), "reason": parts[1].strip()})
                    else:
                        failures.append({"id": line, "reason": "unknown"})
    except Exception as e:
        logger.error(f"Error reading robustness failures log: {e}")
        raise

    return failures

def load_budget_log(log_path: Path) -> dict:
    """
    Load the budget reduction log from T033.
    Returns a dictionary with budget configuration details.
    """
    budget_info = {
        "original_config": {},
        "final_config": {},
        "reductions_applied": [],
        "status": "unknown"
    }

    if not log_path.exists():
        logger.warning(f"Budget log not found at {log_path}. Assuming no budget constraints applied.")
        return budget_info

    try:
        with open(log_path, 'r') as f:
            content = f.read()
            # Try to parse as YAML/JSON if it looks structured
            if content.strip().startswith('{') or content.strip().startswith('-'):
                # Simple heuristic: if it looks like YAML, we might need a parser
                # For now, we'll try to extract key info manually or assume JSON
                try:
                    # Attempt JSON parsing first
                    data = json.loads(content)
                    budget_info.update(data)
                except json.JSONDecodeError:
                    # If JSON fails, we'll try a simple key-value extraction
                    # This is a fallback for YAML-like structures
                    logger.warning("Budget log format not strictly JSON, attempting manual parsing.")
                    lines = content.split('\n')
                    current_section = None
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if line.startswith('original_config:'):
                            current_section = 'original_config'
                        elif line.startswith('final_config:'):
                            current_section = 'final_config'
                        elif line.startswith('reductions_applied:'):
                            current_section = 'reductions_applied'
                        elif current_section and ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            if current_section == 'reductions_applied':
                                budget_info[current_section].append(value)
                            else:
                                budget_info[current_section][key] = value
                    budget_info["status"] = "parsed_manually"
            else:
                # Plain text log, just store the raw content summary
                budget_info["raw_log"] = content[:500] + "..." if len(content) > 500 else content
                budget_info["status"] = "raw_text"
    except Exception as e:
        logger.error(f"Error reading budget log: {e}")
        raise

    return budget_info

def count_valid_realizations(total_expected: int, excluded_ids: list, robustness_failures: list) -> int:
    """
    Calculate the number of valid realizations.
    Combines exclusions from T024/T032 and robustness failures from T041.
    """
    # Collect all unique excluded IDs
    all_excluded_ids = set()
    for item in excluded_ids:
        if 'id' in item:
            all_excluded_ids.add(item['id'])
    for item in robustness_failures:
        if 'id' in item:
            all_excluded_ids.add(item['id'])

    valid_count = total_expected - len(all_excluded_ids)
    return max(0, valid_count)

def generate_report(
    excluded_ids: list,
    robustness_failures: list,
    budget_info: dict,
    valid_count: int,
    min_required: int = 30,
    output_path: Path = None
) -> str:
    """
    Generate the final validation report content as a Markdown string.
    """
    if output_path is None:
        output_path = DATA_RESULTS_DIR / "final_validation_report.md"

    report_lines = []
    report_lines.append("# Final Validation Report")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().isoformat()}")
    report_lines.append(f"**Project:** PROJ-523-quantifying-the-impact-of-data-gaps-on-r")
    report_lines.append(f"**Task:** T046")
    report_lines.append("")
    report_lines.append("## Executive Summary")
    report_lines.append("")
    
    status = "PASS" if valid_count >= min_required else "FAIL"
    report_lines.append(f"**Overall Status:** {status}")
    report_lines.append(f"**Valid Realizations:** {valid_count} / {min_required} (Minimum Required)")
    report_lines.append("")
    
    if valid_count < min_required:
        report_lines.append(f"⚠️ **WARNING:** The number of valid realizations ({valid_count}) is below the minimum requirement ({min_required}).")
        report_lines.append("This may impact the statistical power of the analysis.")
        report_lines.append("")

    report_lines.append("## Exclusion Analysis (T024, T032)")
    report_lines.append("")
    report_lines.append(f"**Total Excluded Realizations:** {len(excluded_ids)}")
    report_lines.append("")
    
    if excluded_ids:
        report_lines.append("### Exclusion Details")
        report_lines.append("")
        report_lines.append("| Realization ID | Reason |")
        report_lines.append("|----------------|--------|")
        for item in excluded_ids:
            rid = item.get('id', 'Unknown')
            reason = item.get('reason', 'Unknown')
            report_lines.append(f"| {rid} | {reason} |")
        report_lines.append("")
    else:
        report_lines.append("No realizations were excluded during the main pipeline execution.")
        report_lines.append("")

    report_lines.append("## Robustness Check Failures (T041)")
    report_lines.append("")
    report_lines.append(f"**Total Robustness Failures:** {len(robustness_failures)}")
    report_lines.append("")
    
    if robustness_failures:
        report_lines.append("### Failure Details")
        report_lines.append("")
        report_lines.append("| Realization ID | Reason |")
        report_lines.append("|----------------|--------|")
        for item in robustness_failures:
            rid = item.get('id', 'Unknown')
            reason = item.get('reason', 'Unknown')
            report_lines.append(f"| {rid} | {reason} |")
        report_lines.append("")
    else:
        report_lines.append("All realizations passed the Fisher Matrix Hessian positive-definite check.")
        report_lines.append("")

    report_lines.append("## Budget Configuration (T033)")
    report_lines.append("")
    report_lines.append("**Budget Status:** " + budget_info.get('status', 'Unknown'))
    report_lines.append("")
    
    if budget_info.get('original_config'):
        report_lines.append("### Original Configuration")
        for key, value in budget_info['original_config'].items():
            report_lines.append(f"- **{key}:** {value}")
        report_lines.append("")
    
    if budget_info.get('final_config'):
        report_lines.append("### Final Configuration (After Reduction)")
        for key, value in budget_info['final_config'].items():
            report_lines.append(f"- **{key}:** {value}")
        report_lines.append("")
    
    if budget_info.get('reductions_applied'):
        report_lines.append("### Reductions Applied")
        for reduction in budget_info['reductions_applied']:
            report_lines.append(f"- {reduction}")
        report_lines.append("")
    else:
        report_lines.append("No configuration reductions were necessary.")
        report_lines.append("")

    report_lines.append("## Conclusion")
    report_lines.append("")
    if valid_count >= min_required:
        report_lines.append(f"The pipeline successfully produced **{valid_count}** valid realizations,")
        report_lines.append(f"which meets the minimum requirement of **{min_required}**. The dataset is")
        report_lines.append("considered valid for downstream analysis.")
    else:
        report_lines.append(f"The pipeline produced **{valid_count}** valid realizations,")
        report_lines.append(f"which is **below** the minimum requirement of **{min_required}**.")
        report_lines.append("The analysis should be halted or the configuration adjusted to increase")
        report_lines.append("the number of valid realizations (e.g., by relaxing constraints or")
        report_lines.append("increasing the time budget).")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*End of Report*")

    return "\n".join(report_lines)

def save_report(content: str, output_path: Path) -> None:
    """
    Save the generated report to the specified path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(content)
    logger.info(f"Final validation report saved to {output_path}")

def run_pipeline(total_expected: int = 50, min_required: int = 30) -> dict:
    """
    Main pipeline function to generate the final validation report.
    """
    logger.info("Starting Final Validation Report Generation (T046)")
    
    # Define paths
    exclusion_log_path = DATA_RESULTS_DIR / "excluded_realizations.log"
    robustness_log_path = DATA_RESULTS_DIR / "robustness_failures.log"
    budget_log_path = DATA_RESULTS_DIR / "run_log.yaml"
    output_report_path = DATA_RESULTS_DIR / "final_validation_report.md"

    # Load data
    excluded_ids = load_exclusion_log(exclusion_log_path)
    robustness_failures = load_robustness_failures(robustness_log_path)
    budget_info = load_budget_log(budget_log_path)

    # Calculate valid realizations
    valid_count = count_valid_realizations(total_expected, excluded_ids, robustness_failures)
    
    logger.info(f"Valid realizations: {valid_count} (Total expected: {total_expected})")

    # Generate report
    report_content = generate_report(
        excluded_ids=excluded_ids,
        robustness_failures=robustness_failures,
        budget_info=budget_info,
        valid_count=valid_count,
        min_required=min_required,
        output_path=output_report_path
    )

    # Save report
    save_report(report_content, output_report_path)

    # Return summary
    return {
        "valid_count": valid_count,
        "min_required": min_required,
        "status": "PASS" if valid_count >= min_required else "FAIL",
        "report_path": str(output_report_path)
    }

def main():
    """
    Entry point for the script.
    """
    try:
        result = run_pipeline()
        logger.info(f"Pipeline completed. Status: {result['status']}")
        if result['status'] == 'FAIL':
            logger.warning("Validation failed: Not enough valid realizations.")
            # Exit with error code to indicate failure
            sys.exit(1)
        else:
            logger.info("Validation passed.")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
