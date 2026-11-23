"""
Feasibility Check Report Generator (Phase 0.5 Gate Part 2)

This script generates a comprehensive markdown report documenting the reasons for
dataset incompatibility if the join operation (T008a) fails. It reads the join
status from a JSON file produced by the join script and formats a human-readable
diagnostic report.

Output: data/processed/feasibility_report.md
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, ensure_dirs

def load_join_status(status_path: str) -> dict:
    """
    Load the join status JSON file produced by 00_feasibility_check_join.py.

    Args:
        status_path: Path to the join status JSON file.

    Returns:
        Dictionary containing join status details.

    Raises:
        FileNotFoundError: If the status file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(status_path):
        raise FileNotFoundError(
            f"Join status file not found at {status_path}. "
            "Ensure code/00_feasibility_check_join.py has been run first."
        )

    with open(status_path, 'r') as f:
        return json.load(f)

def generate_report_content(status: dict) -> str:
    """
    Generate the markdown content for the feasibility report based on join status.

    Args:
        status: Dictionary containing join status details from the join script.

    Returns:
        Markdown string content for the report.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success = status.get('success', False)
    reason = status.get('reason', 'Unknown reason')
    details = status.get('details', {})

    report_lines = [
        "# Feasibility Check Report: Dataset Join Analysis",
        "",
        f"**Generated:** {timestamp}",
        "",
        "## Summary",
        "",
        f"**Join Status:** {'SUCCESS' if success else 'FAILED'}",
        ""
    ]

    if not success:
        report_lines.extend([
            "### Failure Analysis",
            "",
            f"**Primary Reason:** {reason}",
            ""
        ])

        # Add specific diagnostic details
        if details:
            report_lines.append("### Diagnostic Details")
            report_lines.append("")
            for key, value in details.items():
                # Format keys nicely
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, (list, dict)):
                    report_lines.append(f"- **{formatted_key}**: {json.dumps(value, indent=2)}")
                else:
                    report_lines.append(f"- **{formatted_key}**: {value}")
            report_lines.append("")

        # Add specific recommendations based on common failure modes
        report_lines.append("### Recommendations")
        report_lines.append("")
        
        if 'missing_physionet' in reason.lower() or 'physionet' in str(details).lower():
            report_lines.append("1. **Data Download Issue**: The PhysioNet EEG dataset appears to be missing or incomplete.")
            report_lines.append("   - Run `code/01_download_data.py` to fetch the required data.")
            report_lines.append("   - Verify network connectivity to PhysioNet.")
            report_lines.append("   - Check disk space availability.")
            report_lines.append("")
        elif 'missing_behavioral' in reason.lower() or 'behavioral' in str(details).lower():
            report_lines.append("1. **Behavioral Data Issue**: The behavioral metadata file is missing or inaccessible.")
            report_lines.append("   - Verify the path to behavioral metadata in `config.py`.")
            report_lines.append("   - Ensure the file format is compatible (CSV/JSON).")
            report_lines.append("")
        elif 'no_overlap' in reason.lower() or 'common' in reason.lower():
            report_lines.append("1. **Participant ID Mismatch**: No common participant IDs found between datasets.")
            report_lines.append("   - Verify the ID format in both datasets (e.g., 'sub-01' vs '01').")
            report_lines.append("   - Check if the datasets cover different subject pools.")
            report_lines.append("   - Consider implementing an ID mapping strategy if formats differ.")
            report_lines.append("")
        elif 'schema' in reason.lower() or 'column' in reason.lower():
            report_lines.append("1. **Schema Incompatibility**: Required columns are missing in one or both datasets.")
            report_lines.append("   - Review the expected schema in `code/00_feasibility_check_join.py`.")
            report_lines.append("   - Ensure data preprocessing steps have not removed necessary columns.")
            report_lines.append("")
        else:
            report_lines.append("1. **General Investigation Required**: The specific cause of failure requires manual investigation.")
            report_lines.append("   - Review the diagnostic details above.")
            report_lines.append("   - Check raw data files for corruption or unexpected format changes.")
            report_lines.append("   - Verify environment configuration and file paths.")
            report_lines.append("")

        report_lines.append("### Next Steps")
        report_lines.append("")
        report_lines.append("1. Address the identified issues based on the recommendations above.")
        report_lines.append("2. Re-run `code/00_feasibility_check_join.py` after fixes.")
        report_lines.append("3. If the issue persists, contact the data provider or review dataset documentation.")
        report_lines.append("")
    else:
        # Success case - though this script is primarily for failure, we document success too
        report_lines.extend([
            "### Success Details",
            "",
            "The join operation completed successfully. This report is generated for archival purposes.",
            "",
            f"- **Total Participants in EEG Dataset:** {details.get('eeg_count', 'N/A')}",
            f"- **Total Participants in Behavioral Dataset:** {details.get('behavioral_count', 'N/A')}",
            f"- **Joined Participants:** {details.get('joined_count', 'N/A')}",
            f"- **Excluded from EEG:** {details.get('eeg_excluded', 'N/A')}",
            f"- **Excluded from Behavioral:** {details.get('behavioral_excluded', 'N/A')}",
            ""
        ])

    report_lines.extend([
        "---",
        "",
        "*Report generated by code/00_feasibility_check_report.py*",
        "*Part of the llmXive automated science pipeline for PROJ-149*"
    ])

    return "\n".join(report_lines)

def main():
    """
    Main entry point for the feasibility check report generator.

    Reads join status from the default location, generates the report,
    and writes it to the specified output path.
    """
    # Define paths
    status_path = get_path('interim', 'join_status.json')
    output_path = get_path('processed', 'feasibility_report.md')
    
    # Ensure output directory exists
    ensure_dirs(output_path)

    print(f"Loading join status from: {status_path}")
    
    try:
        # Load status
        status = load_join_status(status_path)
        
        # Generate report content
        print("Generating report content...")
        report_content = generate_report_content(status)
        
        # Write report
        print(f"Writing report to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"Feasibility report successfully generated: {output_path}")
        
        # Exit with code 1 if join failed (as per task requirements)
        if not status.get('success', False):
            print("WARNING: Join operation failed. See report for details.")
            sys.exit(1)
        else:
            print("Join operation was successful.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in status file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()