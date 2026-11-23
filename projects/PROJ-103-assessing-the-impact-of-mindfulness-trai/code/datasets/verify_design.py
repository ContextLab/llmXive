"""
Verify that downloaded datasets match the required research design.
Checks for mindfulness intervention metadata and paired pre/post resting-state scans.
"""
import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any

from code.datasets.openneuro_client import list_datasets
from code.src.utils.gap_logging import log_gap
from code.src.datasets.metadata_schema import DatasetMetadata, validate_schema
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def verify_dataset_design(dataset_id: str) -> Tuple[bool, str]:
    """
    Check if a dataset has pre/post scans and mindfulness metadata using the BIDS structure.
    
    Args:
        dataset_id: The OpenNeuro dataset identifier.
        
    Returns:
        Tuple of (design_verified, reason).
    """
    raw_dir = paths.data(f"raw/{dataset_id}")
    if not raw_dir.exists():
        return False, "dataset_directory_missing"

    desc_path = raw_dir / "dataset_description.json"
    if not desc_path.exists():
        return False, "missing_description"

    # 1. Verify Mindfulness Metadata
    try:
        with open(desc_path, "r", encoding="utf-8") as f:
            desc = json.load(f)
        desc_text = str(desc).lower()
    except json.JSONDecodeError:
        return False, "invalid_json_description"
    except Exception as e:
        return False, f"description_read_error: {str(e)}"

    mindfulness_keywords = ["mindfulness", "mbsr", "meditation", "mindful"]
    if not any(kw in desc_text for kw in mindfulness_keywords):
        return False, "design_missing_mindfulness_metadata"

    # 2. Verify Pre/Post Scan Design
    # Scan BIDS structure: sub-XX/ses-XX/func/
    subjects = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    if not subjects:
        return False, "no_subjects_found"

    paired_count = 0
    total_pre = 0
    total_post = 0

    for sub in subjects:
        sessions = [d for d in sub.iterdir() if d.is_dir() and d.name.startswith("ses-")]
        
        # Identify pre and post sessions (case-insensitive substring match)
        pre_sessions = [s for s in sessions if "pre" in s.name.lower() or "baseline" in s.name.lower()]
        post_sessions = [s for s in sessions if "post" in s.name.lower() or "followup" in s.name.lower()]
        
        if pre_sessions:
            total_pre += 1
        if post_sessions:
            total_post += 1
        if pre_sessions and post_sessions:
            paired_count += 1

    if paired_count == 0:
        return False, "no_paired_pre_post_scans"

    # 3. Validate against Schema from T017
    try:
        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            pre_scan_count=total_pre,
            post_scan_count=total_post,
            intervention_type="mindfulness",
            scan_type="resting_state",
            version="1.0"
        )
        # validate_schema returns True or raises/returns False
        if not validate_schema(metadata):
            return False, "schema_validation_failed"
    except Exception as e:
        return False, f"metadata_creation_error: {str(e)}"

    return True, "verified"

def main():
    """
    Main entry point to verify all candidate datasets and generate reports.
    """
    candidates = list_datasets()
    qualified = []
    report_data = {}

    for ds_id in candidates:
        is_valid, reason = verify_dataset_design(ds_id)
        
        report_data[ds_id] = {
            "design_verified": is_valid,
            "reason": reason
        }

        if is_valid:
            log.info(f"Dataset {ds_id} verified successfully.")
            qualified.append(ds_id)
        else:
            log.warning(f"Dataset {ds_id} failed verification: {reason}")
            log_gap(ds_id, reason)

    # Save qualified list
    meta_path = paths.data("metadata/qualified_datasets.json")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"qualified_datasets": qualified}, f, indent=2)

    # Save detailed verification report
    report_path = paths.data("metadata/verification_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    if len(qualified) < 3:
        log.warning(f"Warning: Fewer than 3 qualified mindfulness datasets found ({len(qualified)}).")

    print(f"Verification complete. Qualified datasets: {qualified}")

if __name__ == "__main__":
    main()
