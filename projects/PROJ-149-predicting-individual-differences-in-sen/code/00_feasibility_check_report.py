"""
T008b: Generate feasibility report based on join results.

This script is the second part of the Phase 0.5 Gate. It is designed to run
after T008a (code/00_feasibility_check_join.py).

It reads the join status and metadata from the JSON file produced by T008a
and generates a human-readable Markdown report at:
data/processed/feasibility_report.md

If the join failed or datasets were incompatible, this report details the
reasons and provides a recommendation to halt or adjust the pipeline.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports from sibling modules
# Assuming this script is in code/ and we need to access config or utils if needed
# However, this task is standalone based on JSON output from T008a.
# We will import config just to ensure path consistency if we need to construct paths.
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from code.config import get_path
except (ImportError, ModuleNotFoundError):
    # Fallback if config is not yet available or import fails
    from config import get_path

# Constants
JOIN_STATUS_FILE = "data/processed/join_status.json"
REPORT_OUTPUT_FILE = "data/processed/feasibility_report.md"


def load_join_status() -> dict:
    """
    Load the join status JSON produced by T008a.
    
    Returns:
        dict: The status dictionary.
        
    Raises:
        FileNotFoundError: If the join status file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    status_path = get_path(JOIN_STATUS_FILE)
    if not status_path.exists():
        raise FileNotFoundError(
            f"Join status file not found at {status_path}. "
            "Please ensure T008a (00_feasibility_check_join.py) has run successfully."
        )
    
    with open(status_path, 'r') as f:
        return json.load(f)


def generate_report_content(status: dict) -> str:
    """
    Generate the Markdown content for the feasibility report.
    
    Args:
        status (dict): The join status dictionary from T008a.
        
    Returns:
        str: The formatted Markdown report string.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    is_success = status.get("success", False)
    
    lines = [
        "# Feasibility Check Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Source:** {JOIN_STATUS_FILE}",
        "",
        "## Executive Summary",
        "",
    ]
    
    if is_success:
        lines.append("✅ **Feasibility Check PASSED.**")
        lines.append("The EEG and behavioral datasets were successfully joined.")
        lines.append("Demographic metadata validation passed.")
        lines.append("Proceed to User Story 1 (Preprocessing).")
    else:
        lines.append("❌ **Feasibility Check FAILED.**")
        lines.append("The datasets could not be joined or are incompatible.")
        lines.append("The pipeline should be halted.")
    
    lines.append("")
    lines.append("## Join Details")
    lines.append("")
    
    # Extract relevant fields
    eeg_count = status.get("eeg_participants", 0)
    rt_count = status.get("rt_participants", 0)
    joined_count = status.get("joined_participants", 0)
    
    lines.append(f"- **EEG Participants Found:** {eeg_count}")
    lines.append(f"- **Behavioral (RT) Participants Found:** {rt_count}")
    lines.append(f"- **Successfully Joined:** {joined_count}")
    lines.append("")
    
    if not is_success:
        lines.append("## Failure Analysis")
        lines.append("")
        failure_reason = status.get("failure_reason", "Unknown reason.")
        lines.append(f"**Reason:** {failure_reason}")
        lines.append("")
        
        # Add specific recommendations based on failure type
        if "metadata" in failure_reason.lower():
            lines.append("### Recommendation")
            lines.append("Check the raw metadata files in `data/raw/`. Ensure participant IDs match format.")
        elif "empty" in failure_reason.lower():
            lines.append("### Recommendation")
            lines.append("Verify that both datasets have been downloaded correctly via `01_download_data.py`.")
        elif "incompatible" in failure_reason.lower():
            lines.append("### Recommendation")
            lines.append("Review data schemas. The key fields (e.g., `participant_id`) may not align.")
        
        lines.append("")
    else:
        lines.append("## Demographic Validation")
        lines.append("")
        # If success, show what was validated
        demographics = status.get("demographic_validation", {})
        if demographics:
            for key, value in demographics.items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        else:
            lines.append("- No specific demographic validation details recorded.")
        lines.append("")
        
        lines.append("## Next Steps")
        lines.append("")
        lines.append("1. Proceed to **T010**: Implement `02_preprocess_eeg.py`.")
        lines.append("2. Ensure `data/processed/` contains the joined features if applicable.")
        lines.append("3. Run the full pipeline starting from data ingestion.")
    
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by code/00_feasibility_check_report.py*")
    
    return "\n".join(lines)


def main():
    """
    Main entry point for the feasibility report generation.
    
    1. Loads join status from T008a.
    2. Generates the Markdown report.
    3. Writes the report to `data/processed/feasibility_report.md`.
    4. Exits with code 1 if the join failed (to signal downstream blocks), 
       otherwise exits with 0.
    """
    print(f"Loading join status from {JOIN_STATUS_FILE}...")
    try:
        status = load_join_status()
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"CRITICAL ERROR: Invalid JSON in status file: {e}")
        sys.exit(1)
    
    print("Generating report content...")
    report_content = generate_report_content(status)
    
    output_path = get_path(REPORT_OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing report to {output_path}...")
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    print(f"Report successfully generated: {output_path}")
    
    # Exit with non-zero code if the underlying join failed, 
    # signaling that the pipeline should stop.
    if not status.get("success", False):
        print("WARNING: Underlying join failed. Exiting with code 1.")
        sys.exit(1)
    
    print("Feasibility check passed. Proceeding.")
    sys.exit(0)


if __name__ == "__main__":
    main()