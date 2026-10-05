"""
Validation logic for linked_issue_ids to ensure they are explicitly labeled as "reported"
and not treated as ground truth, adhering to FR-011.

This module processes the raw PR data extracted in T012 and adds validation flags
to distinguish between reported issues and confirmed ground truth.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config.settings import get_paths, ensure_directories
from code.src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

def validate_linked_issues(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate linked_issue_ids in a PR data object.

    Per FR-011:
    - linked_issue_ids must be explicitly labeled as "reported" status.
    - They must NOT be treated as ground truth.

    Args:
        pr_data: Dictionary containing PR information including 'linked_issue_ids'.

    Returns:
        Updated pr_data dictionary with validation metadata:
        - 'linked_issues_status': List of dicts with issue_id and status ("reported")
        - 'is_ground_truth': Boolean, always False for linked issues at this stage
        - 'validation_flag': Boolean, True if validation was performed
    """
    if not isinstance(pr_data, dict):
        logger.error(f"Invalid pr_data type: {type(pr_data)}")
        return pr_data

    linked_issues = pr_data.get("linked_issue_ids", [])
    
    if not linked_issues:
        # No linked issues found, nothing to validate
        pr_data["linked_issues_status"] = []
        pr_data["is_ground_truth"] = False
        pr_data["validation_flag"] = True
        return pr_data

    validated_issues = []
    for issue_id in linked_issues:
        # Per FR-011: All linked issues at extraction stage are "reported" only
        # They are NOT ground truth until verified by human confirmations (T014c)
        validated_issues.append({
            "issue_id": issue_id,
            "status": "reported",
            "is_ground_truth": False,
            "validation_source": "extraction_phase"
        })

    pr_data["linked_issues_status"] = validated_issues
    pr_data["is_ground_truth"] = False  # Explicitly mark as not ground truth
    pr_data["validation_flag"] = True
    
    logger.debug(f"Validated {len(validated_issues)} linked issues for PR {pr_data.get('pr_id', 'unknown')}")
    return pr_data


def process_pr_dataset(raw_data_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Process a dataset file containing PR data and validate all linked_issue_ids.

    Args:
        raw_data_path: Path to the raw PR data JSON file (from T012).
        output_path: Path to save the validated data.

    Returns:
        Summary statistics of the validation process.
    """
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")

    logger.info(f"Loading raw data from {raw_data_path}")
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        pr_data_list = json.load(f)

    if not isinstance(pr_data_list, list):
        raise ValueError(f"Expected list of PR data, got {type(pr_data_list)}")

    validated_data = []
    stats = {
        "total_prs": len(pr_data_list),
        "prs_with_linked_issues": 0,
        "total_linked_issues": 0,
        "validation_errors": 0
    }

    for idx, pr_data in enumerate(pr_data_list):
        try:
            validated_pr = validate_linked_issues(pr_data)
            validated_data.append(validated_pr)
            
            if validated_pr.get("linked_issues_status"):
                stats["prs_with_linked_issues"] += 1
                stats["total_linked_issues"] += len(validated_pr["linked_issues_status"])
        except Exception as e:
            logger.error(f"Error validating PR at index {idx}: {e}")
            stats["validation_errors"] += 1
            # Add failed entry with error flag
            pr_data["validation_error"] = str(e)
            pr_data["validation_flag"] = False
            validated_data.append(pr_data)

    # Ensure output directory exists
    ensure_directories()
    
    logger.info(f"Saving validated data to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validated_data, f, indent=2, default=str)

    logger.info(f"Validation complete. Stats: {stats}")
    return stats


def main():
    """Main entry point for the validation script."""
    paths = get_paths()
    raw_data_path = paths["raw_prs_json"]
    output_path = paths["validated_prs_json"]

    logger.info("Starting linked issue validation (T016)")
    logger.info(f"Input: {raw_data_path}")
    logger.info(f"Output: {output_path}")

    try:
        stats = process_pr_dataset(raw_data_path, output_path)
        logger.info(f"Validation completed successfully. Processed {stats['total_prs']} PRs.")
        logger.info(f"Found {stats['prs_with_linked_issues']} PRs with {stats['total_linked_issues']} linked issues.")
        if stats["validation_errors"] > 0:
            logger.warning(f"Encountered {stats['validation_errors']} validation errors.")
        else:
            logger.info("No validation errors encountered.")
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise


if __name__ == "__main__":
    main()
