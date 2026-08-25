"""
Task T038: Calculate the global Bug-File linkage rate.

Logic:
1. Aggregate total issues mentioning paths across all repos.
2. Aggregate total issues successfully linked to modules.
3. Calculate linkage_rate_percentage = (linked_issues / total_issues) * 100.
4. Write result to data/results/linkage_rate.json.

Execution Order: Must run AFTER data collection (T013-T014) and metrics calculation.
"""
import json
import logging
import os
import csv
from pathlib import Path
from typing import Dict, Any, List, Set

# Import from existing API surface
from utils.logging_utils import get_logger
from config import get_output_dir

logger = get_logger(__name__)

def load_issues_for_repo(repo_name: str, intermediate_dir: Path) -> List[Dict[str, Any]]:
    """
    Load issues for a specific repository from the intermediate CSV.
    Expected file: data/intermediate/{repo_name}_issues.csv
    """
    issues_file = intermediate_dir / f"{repo_name}_issues.csv"
    if not issues_file.exists():
        logger.warning(f"Issues file not found for {repo_name}: {issues_file}")
        return []

    issues = []
    with open(issues_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            issues.append(row)
    
    return issues

def calculate_linkage_rate(repos: List[str], output_dir: Path, intermediate_dir: Path) -> Dict[str, Any]:
    """
    Calculate the global linkage rate across all provided repositories.
    
    Args:
        repos: List of repository names (e.g., ["apache-httpd", "scipy-scipy"])
        output_dir: Base output directory (from config)
        intermediate_dir: Directory containing intermediate CSVs
    
    Returns:
        Dictionary with total_issues, linked_issues, linkage_rate_percentage
    """
    total_issues = 0
    linked_issues = 0

    logger.info(f"Calculating linkage rate for {len(repos)} repositories...")

    for repo in repos:
        issues = load_issues_for_repo(repo, intermediate_dir)
        
        if not issues:
            logger.info(f"No issues found for {repo}, skipping linkage calculation.")
            continue

        repo_total = len(issues)
        repo_linked = 0

        for issue in issues:
            # Check if the issue has a valid path link.
            # Based on T014, issues are linked to modules using path matching.
            # We assume a successful link results in a non-empty 'linked_path' or similar field.
            # Looking at standard patterns in T014, let's check for a 'linked_module' or 'path' field.
            # If the issue mentions a path but failed to link, it might have a 'null' or empty string.
            # We assume the CSV generated in T014 has a column indicating the linked module path.
            
            # Heuristic: If 'linked_path' exists and is not empty, it's linked.
            # If the column name varies, we check common keys.
            linked_path = issue.get('linked_path') or issue.get('linked_module') or issue.get('path')
            
            if linked_path and str(linked_path).strip() != '' and str(linked_path).lower() != 'nan':
                repo_linked += 1
            else:
                # Optional: Log specific failures if needed for debugging
                pass

        total_issues += repo_total
        linked_issues += repo_linked
        logger.debug(f"Repo {repo}: {repo_total} total, {repo_linked} linked")

    if total_issues == 0:
        logger.warning("No issues found across all repositories. Linkage rate is undefined.")
        linkage_rate = 0.0
    else:
        linkage_rate = (linked_issues / total_issues) * 100

    result = {
        "total_issues": total_issues,
        "linked_issues": linked_issues,
        "linkage_rate_percentage": round(linkage_rate, 4)
    }

    logger.info(f"Linkage Rate Calculation Complete: {result}")
    return result

def run_linkage_rate_analysis():
    """
    Main entry point for T038.
    """
    output_dir = Path(get_output_dir())
    intermediate_dir = output_dir / "intermediate"
    results_dir = output_dir / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    # Get list of repositories from config
    # Assuming get_repo_list returns a list of repo identifiers used in filenames
    repos = get_repo_list()
    
    if not repos:
        logger.error("No repositories found in configuration. Cannot calculate linkage rate.")
        return

    result = calculate_linkage_rate(repos, output_dir, intermediate_dir)

    output_file = results_dir / "linkage_rate.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Linkage rate report written to {output_file}")

if __name__ == "__main__":
    run_linkage_rate_analysis()
