"""
T017: Generate Triangulated Ground Truth.

Consumes:
  - data/derived/human_confirmations.json (from T014c)
  - data/raw/*.json (for fallback closed issue lookup, if needed)

Produces:
  - data/derived/human_baseline.json

Logic:
  1. Identify bugs confirmed by >= 2 independent human reviewers OR 1 senior maintainer.
  2. If insufficient real human data exists for a specific location, fallback to
     "Closed Issue with Bug Label" (secondary fallback).
  3. Output schema: list of objects with pr_id, file_path, line_start, line_end,
     severity, is_verified, verification_method.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict

# Import local config and utils
from code.config.settings import get_paths, ensure_directories
from code.src.utils.logger import get_logger

# Constants for triangulation
MIN_HUMAN_REVIEWERS = 2
SENIOR_MAINTAINER_KEYWORDS = ["maintainer", "owner", "admin", "core", "senior"]

logger = get_logger(__name__)

def load_human_confirmations(path: Path) -> List[Dict[str, Any]]:
    """Load human confirmations from T014c."""
    if not path.exists():
        raise FileNotFoundError(f"Human confirmations file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}, got {type(data)}")
    
    return data

def load_fallback_issues(raw_data_dir: Path) -> List[Dict[str, Any]]:
    """
    Load closed issues with bug labels from raw data for fallback.
    This assumes T012 fetched issue data and stored it in data/raw/.
    We look for files containing issue data.
    """
    fallback_issues = []
    # Search for JSON files in raw data dir that might contain issues
    # In a real scenario, we'd have a specific file like 'issues.json'
    for file_path in raw_data_dir.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Handle list of issues or dict containing issues
            items = []
            if isinstance(content, list):
                items = content
            elif isinstance(content, dict):
                items = content.get('issues', content.get('data', []))
            
            for item in items:
                # Check if it's a closed issue with a bug label
                if (item.get('state') == 'closed' and 
                    any('bug' in label.get('name', '').lower() 
                        for label in item.get('labels', []))):
                    fallback_issues.append(item)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Skipping file {file_path} due to error: {e}")
            continue
    
    return fallback_issues

def is_senior_maintainer(reviewer_id: str) -> bool:
    """Check if reviewer is likely a senior maintainer based on ID."""
    # Simple heuristic: check for keywords in ID or assume specific known maintainers
    # In production, this would use a real maintainer list
    return any(kw in reviewer_id.lower() for kw in SENIOR_MAINTAINER_KEYWORDS)

def triangulate_bugs(confirmations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply triangulation logic to identify verified bugs.
    
    Group confirmations by (pr_id, file_path, line_start, line_end)
    and count independent reviewers.
    """
    # Group by location
    location_groups: Dict[Tuple, List[Dict[str, Any]]] = defaultdict(list)
    
    for conf in confirmations:
        key = (
            conf.get('pr_id'),
            conf.get('file_path'),
            conf.get('line_start'),
            conf.get('line_end')
        )
        location_groups[key].append(conf)
    
    verified_bugs = []
    triangulation_met_count = 0
    fallback_count = 0
    
    for (pr_id, file_path, line_start, line_end), confs in location_groups.items():
        # Count unique reviewers
        unique_reviewers = set(conf.get('reviewer_id') for conf in confs)
        senior_count = sum(1 for conf in confs if is_senior_maintainer(conf.get('reviewer_id', '')))
        
        # Check triangulation criteria: >= 2 independent reviewers OR 1 senior maintainer
        is_strict = (len(unique_reviewers) >= MIN_HUMAN_REVIEWERS) or (senior_count >= 1)
        
        if is_strict:
            # Determine severity from confirmations (take most severe)
            severity = "minor"
            severity_priority = {"critical": 4, "major": 3, "minor": 2, "style": 1}
            
            for conf in confs:
                conf_severity = conf.get('confirmation_type', 'minor')
                if severity_priority.get(conf_severity, 0) > severity_priority.get(severity, 0):
                    severity = conf_severity
            
            verified_bugs.append({
                "pr_id": pr_id,
                "file_path": file_path,
                "line_start": line_start,
                "line_end": line_end,
                "severity": severity,
                "is_verified": True,
                "verification_method": "strict_triangulation",
                "reviewer_count": len(unique_reviewers),
                "senior_count": senior_count
            })
            triangulation_met_count += 1
        else:
            logger.debug(
                f"Location ({pr_id}, {file_path}, {line_start}-{line_end}) "
                f"has only {len(unique_reviewers)} reviewers, no senior. "
                f"Marking for fallback check."
            )
            # Store for fallback check
            verified_bugs.append({
                "pr_id": pr_id,
                "file_path": file_path,
                "line_start": line_start,
                "line_end": line_end,
                "severity": "minor", # Default, will be updated if fallback found
                "is_verified": False, # Initially unverified, will be updated
                "verification_method": "pending_fallback",
                "reviewer_count": len(unique_reviewers),
                "senior_count": senior_count
            })
    
    return verified_bugs, triangulation_met_count

def apply_fallback(
    candidate_bugs: List[Dict[str, Any]], 
    fallback_issues: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Apply fallback logic: "Closed Issue with Bug Label".
    
    For bugs that didn't meet strict triangulation, check if there's a 
    closed issue with a bug label that matches the PR/Location.
    """
    fallback_count = 0
    updated_bugs = []
    
    # Create a lookup for fallback issues by PR ID (simplified matching)
    # In reality, we'd need to match by issue number or body content
    issue_lookup = {}
    for issue in fallback_issues:
        # Try to extract PR/Issue number from URL or number field
        issue_num = issue.get('number')
        if issue_num:
            issue_lookup[issue_num] = issue
    
    for bug in candidate_bugs:
        if bug["verification_method"] == "pending_fallback":
            pr_id = bug["pr_id"]
            # Try to match PR ID to issue number (assuming PR numbers are issue numbers)
            fallback_match = issue_lookup.get(pr_id)
            
            if fallback_match:
                bug["is_verified"] = True
                bug["verification_method"] = "fallback_closed_issue"
                bug["severity"] = fallback_match.get('labels', [{'name': 'minor'}])[0].get('name', 'minor')
                fallback_count += 1
                logger.info(
                    f"Fallback matched for PR {pr_id}: "
                    f"Closed issue with bug label found."
                )
            else:
                # Keep as unverified
                bug["verification_method"] = "insufficient_data"
                bug["is_verified"] = False
        else:
            # Already verified by strict triangulation
            updated_bugs.append(bug)
            continue
        
        # Only add if it was updated (either matched fallback or marked insufficient)
        updated_bugs.append(bug)
    
    return updated_bugs, fallback_count

def run_ground_truth_generation() -> None:
    """Main execution function for T017."""
    paths = get_paths()
    ensure_directories(paths)
    
    input_path = paths["derived"] / "human_confirmations.json"
    output_path = paths["derived"] / "human_baseline.json"
    raw_data_dir = paths["raw"]
    
    logger.info(f"Starting ground truth generation from {input_path}")
    
    # Load input data
    try:
        confirmations = load_human_confirmations(input_path)
        logger.info(f"Loaded {len(confirmations)} human confirmations")
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        logger.error("Ensure T014c has run and produced data/derived/human_confirmations.json")
        sys.exit(1)
    
    if not confirmations:
        logger.warning("No human confirmations found. Generating empty baseline.")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return
    
    # Step 1: Triangulate
    candidate_bugs, triangulation_count = triangulate_bugs(confirmations)
    logger.info(f"Strict triangulation met for {triangulation_count} locations")
    
    # Step 2: Apply fallback if needed
    fallback_issues = load_fallback_issues(raw_data_dir)
    logger.info(f"Loaded {len(fallback_issues)} potential fallback issues")
    
    final_bugs, fallback_count = apply_fallback(candidate_bugs, fallback_issues)
    
    # Filter out unverified bugs (keep only verified ones for the baseline)
    verified_final_bugs = [b for b in final_bugs if b["is_verified"]]
    
    # Log summary
    logger.info(f"Triangulation strict: {triangulation_count}")
    logger.info(f"Fallback applied: {fallback_count}")
    logger.info(f"Total verified bugs in baseline: {len(verified_final_bugs)}")
    
    if len(verified_final_bugs) == 0 and triangulation_count == 0 and fallback_count == 0:
        logger.warning("Strict triangulation not met AND no fallback matches found. "
                     "Baseline is empty. This may indicate insufficient data.")
    
    # Save output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(verified_final_bugs, f, indent=2)
    
    logger.info(f"Ground truth baseline saved to {output_path}")

def main():
    """Entry point for script execution."""
    setup_logger = logging.getLogger()
    setup_logger.setLevel(logging.INFO)
    
    run_ground_truth_generation()

if __name__ == "__main__":
    main()
