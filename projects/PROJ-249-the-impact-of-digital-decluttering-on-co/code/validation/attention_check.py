"""
Attention Check Validation Module

This module implements validation logic to identify low-quality participants
based on attention check performance, specifically SART accuracy.

Participants with SART accuracy < 50% are flagged as 'low_quality' and
excluded from primary analysis.
"""

import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths (relative to project root)
BASELINE_DATA_PATH = Path("data/raw/baseline_raw.csv")
EXCLUSIONS_PATH = Path("data/processed/exclusions.json")
QUALITY_REPORT_PATH = Path("results/quality_report.md")

# Threshold for SART accuracy
SART_ACCURACY_THRESHOLD = 0.50

def load_baseline_data(data_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load baseline data from CSV file.

    Args:
        data_path: Path to the baseline data CSV file. Defaults to BASELINE_DATA_PATH.

    Returns:
        List of dictionaries containing baseline data records.

    Raises:
        FileNotFoundError: If the baseline data file does not exist.
        ValueError: If the CSV is empty or has invalid format.
    """
    if data_path is None:
        data_path = BASELINE_DATA_PATH

    if not data_path.exists():
        raise FileNotFoundError(f"Baseline data file not found: {data_path}")

    data = []
    with open(data_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    if not data:
        raise ValueError(f"Baseline data file is empty: {data_path}")

    logger.info(f"Loaded {len(data)} records from {data_path}")
    return data

def calculate_sart_accuracy(participant_data: List[Dict[str, Any]]) -> float:
    """
    Calculate SART accuracy for a single participant.

    SART accuracy is calculated as:
    accuracy = (total_trials - commission_errors - omission_errors) / total_trials

    Args:
        participant_data: List of SART trial records for one participant.

    Returns:
        SART accuracy as a float between 0 and 1.
    """
    total_trials = 0
    commission_errors = 0
    omission_errors = 0

    for trial in participant_data:
        if trial.get('metric_type') == 'sart':
            total_trials += 1
            if trial.get('commission_error', 'False').lower() == 'true':
                commission_errors += 1
            if trial.get('omission_error', 'False').lower() == 'true':
                omission_errors += 1

    if total_trials == 0:
        logger.warning("No SART trials found for participant")
        return 0.0

    # Correct responses = total - errors
    correct_responses = total_trials - commission_errors - omission_errors
    accuracy = correct_responses / total_trials

    return accuracy

def identify_low_quality_participants(baseline_data: List[Dict[str, Any]], threshold: float = SART_ACCURACY_THRESHOLD) -> List[Dict[str, Any]]:
    """
    Identify participants with SART accuracy below the threshold.

    Args:
        baseline_data: List of all baseline data records.
        threshold: Accuracy threshold below which participants are flagged.

    Returns:
        List of dictionaries containing low-quality participant information.
    """
    # Group data by participant
    participant_sart_data: Dict[str, List[Dict[str, Any]]] = {}

    for record in baseline_data:
        participant_id = record.get('participant_id')
        if participant_id not in participant_sart_data:
            participant_sart_data[participant_id] = []
        participant_sart_data[participant_id].append(record)

    low_quality_participants = []

    for participant_id, trials in participant_sart_data.items():
        # Filter for SART trials only
        sart_trials = [t for t in trials if t.get('metric_type') == 'sart']

        if not sart_trials:
            logger.warning(f"No SART data found for participant {participant_id}")
            continue

        accuracy = calculate_sart_accuracy(sart_trials)

        if accuracy < threshold:
            low_quality_participants.append({
                'participant_id': participant_id,
                'reason': 'low_sart_accuracy',
                'sart_accuracy': accuracy,
                'threshold': threshold
            })
            logger.info(f"Flagged participant {participant_id} with SART accuracy {accuracy:.2%}")

    return low_quality_participants

def load_existing_exclusions(exclusions_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load existing exclusions file if it exists.

    Args:
        exclusions_path: Path to the exclusions JSON file.

    Returns:
        Dictionary containing existing exclusions data.
    """
    if exclusions_path is None:
        exclusions_path = EXCLUSIONS_PATH

    if exclusions_path.exists():
        with open(exclusions_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    return {'exclusions': [], 'generated_at': None}

def save_exclusions(exclusions_data: Dict[str, Any], exclusions_path: Optional[Path] = None) -> None:
    """
    Save exclusions data to JSON file.

    Args:
        exclusions_data: Dictionary containing exclusions information.
        exclusions_path: Path to the output JSON file.
    """
    if exclusions_path is None:
        exclusions_path = EXCLUSIONS_PATH

    # Ensure directory exists
    exclusions_path.parent.mkdir(parents=True, exist_ok=True)

    with open(exclusions_path, 'w', encoding='utf-8') as f:
        json.dump(exclusions_data, f, indent=2)

    logger.info(f"Saved exclusions to {exclusions_path}")

def append_low_quality_exclusions(low_quality_participants: List[Dict[str, Any]], exclusions_path: Optional[Path] = None) -> None:
    """
    Append low quality participant exclusions to the existing exclusions file.

    Args:
        low_quality_participants: List of low quality participant dictionaries.
        exclusions_path: Path to the exclusions JSON file.
    """
    if not low_quality_participants:
        logger.info("No low quality participants to add to exclusions")
        return

    existing = load_existing_exclusions(exclusions_path)

    # Add new exclusions
    for participant in low_quality_participants:
        exclusion_entry = {
            'participant_id': participant['participant_id'],
            'reason': participant['reason'],
            'details': {
                'sart_accuracy': participant['sart_accuracy'],
                'threshold': participant['threshold']
            }
        }
        existing['exclusions'].append(exclusion_entry)

    existing['generated_at'] = str(Path().resolve())  # Update timestamp

    save_exclusions(existing, exclusions_path)

def generate_quality_report(low_quality_participants: List[Dict[str, Any]], report_path: Optional[Path] = None) -> None:
    """
    Generate a markdown quality report listing all excluded participants.

    Args:
        low_quality_participants: List of low quality participant dictionaries.
        report_path: Path to the output report file.
    """
    if report_path is None:
        report_path = QUALITY_REPORT_PATH

    # Ensure directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# Data Quality Report",
        "",
        "## Attention Check Validation Results",
        "",
        f"**Threshold**: SART accuracy < {SART_ACCURACY_THRESHOLD:.0%}",
        "",
        f"**Total Low-Quality Participants**: {len(low_quality_participants)}",
        "",
    ]

    if low_quality_participants:
        report_lines.append("### Excluded Participants")
        report_lines.append("")
        report_lines.append("| Participant ID | SART Accuracy | Reason |")
        report_lines.append("|----------------|---------------|--------|")

        for participant in low_quality_participants:
            report_lines.append(
                f"| {participant['participant_id']} | "
                f"{participant['sart_accuracy']:.2%} | "
                f"{participant['reason']} |"
            )

        report_lines.append("")
        report_lines.append("### Summary")
        report_lines.append("")
        report_lines.append(
            f"The following {len(low_quality_participants)} participant(s) were excluded "
            f"from primary analysis due to poor attention check performance (SART accuracy "
            f"below {SART_ACCURACY_THRESHOLD:.0%}). This ensures that the final analysis "
            "is based on data from participants who were engaged with the task."
        )
    else:
        report_lines.append("### Summary")
        report_lines.append("")
        report_lines.append(
            "All participants passed the attention check. No exclusions were made "
            "based on SART accuracy."
        )

    report_content = "\n".join(report_lines)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"Generated quality report at {report_path}")

def run_attention_check_validation(
    baseline_path: Optional[Path] = None,
    exclusions_path: Optional[Path] = None,
    report_path: Optional[Path] = None,
    threshold: float = SART_ACCURACY_THRESHOLD
) -> Dict[str, Any]:
    """
    Run the complete attention check validation pipeline.

    This function:
    1. Loads baseline data
    2. Identifies low-quality participants based on SART accuracy
    3. Appends exclusions to the exclusions file
    4. Generates a quality report

    Args:
        baseline_path: Path to baseline data CSV.
        exclusions_path: Path to exclusions JSON file.
        report_path: Path to quality report markdown file.
        threshold: Accuracy threshold for flagging low-quality participants.

    Returns:
        Dictionary containing validation results.
    """
    logger.info("Starting attention check validation")

    # Load baseline data
    baseline_data = load_baseline_data(baseline_path)
    logger.info(f"Loaded {len(baseline_data)} baseline records")

    # Identify low-quality participants
    low_quality_participants = identify_low_quality_participants(baseline_data, threshold)
    logger.info(f"Identified {len(low_quality_participants)} low-quality participants")

    # Append to exclusions file
    append_low_quality_exclusions(low_quality_participants, exclusions_path)

    # Generate quality report
    generate_quality_report(low_quality_participants, report_path)

    # Return results
    return {
        'total_participants_checked': len(set(
            r['participant_id'] for r in baseline_data if r.get('metric_type') == 'sart'
        )),
        'low_quality_count': len(low_quality_participants),
        'threshold': threshold,
        'exclusions_path': str(exclusions_path) if exclusions_path else str(EXCLUSIONS_PATH),
        'report_path': str(report_path) if report_path else str(QUALITY_REPORT_PATH)
    }

def main():
    """Main entry point for the attention check validation script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate participant attention using SART accuracy'
    )
    parser.add_argument(
        '--baseline',
        type=str,
        default=str(BASELINE_DATA_PATH),
        help='Path to baseline data CSV file'
    )
    parser.add_argument(
        '--exclusions',
        type=str,
        default=str(EXCLUSIONS_PATH),
        help='Path to exclusions JSON file'
    )
    parser.add_argument(
        '--report',
        type=str,
        default=str(QUALITY_REPORT_PATH),
        help='Path to quality report markdown file'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=SART_ACCURACY_THRESHOLD,
        help='SART accuracy threshold for flagging low-quality participants'
    )

    args = parser.parse_args()

    try:
        results = run_attention_check_validation(
            baseline_path=Path(args.baseline),
            exclusions_path=Path(args.exclusions),
            report_path=Path(args.report),
            threshold=args.threshold
        )

        print("\n=== Attention Check Validation Results ===")
        print(f"Participants checked: {results['total_participants_checked']}")
        print(f"Low-quality participants: {results['low_quality_count']}")
        print(f"Threshold: {results['threshold']:.0%}")
        print(f"Exclusions saved to: {results['exclusions_path']}")
        print(f"Quality report saved to: {results['report_path']}")
        print("==========================================\n")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise

if __name__ == '__main__':
    main()
