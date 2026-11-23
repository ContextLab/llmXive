"""
T012c: Data Integrity Check and Merge.

This module implements the data integrity check logic:
1. Verifies existence of `data/processed/pr_turnaround_partial.csv`.
2. Merges it with `data/processed/pr_turnaround.csv` if both exist.
3. Promotes partial to canonical if the main file is missing.
4. Logs 'TRUNCATED' flag to `data/processed/data_quality_warning.log`.
5. Updates `data/processed/truncated_repos.txt` with repository names.
"""
import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Set

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this script (assuming script is in code/)
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PARTIAL_FILE = PROCESSED_DIR / "pr_turnaround_partial.csv"
CANONICAL_FILE = PROCESSED_DIR / "pr_turnaround.csv"
TRUNCATED_REPOS_FILE = PROCESSED_DIR / "truncated_repos.txt"
QUALITY_LOG_FILE = PROCESSED_DIR / "data_quality_warning.log"

def load_csv_to_dicts(filepath: Path) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    if not filepath.exists():
        return []
    
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def save_dicts_to_csv(data: List[Dict[str, Any]], filepath: Path) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        # Write empty file with no headers if no data
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    fieldnames = list(data[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_truncated_repos(filepath: Path) -> Set[str]:
    """Load repository names from the truncated repos text file."""
    repos = set()
    if not filepath.exists():
        return repos
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                repos.add(line)
    return repos

def save_truncated_repos(repos: Set[str], filepath: Path) -> None:
    """Save repository names to the truncated repos text file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# List of repositories where data fetching was truncated.\n")
        f.write("# Format: One repo name per line.\n\n")
        for repo in sorted(repos):
            f.write(f"{repo}\n")

def append_to_quality_log(message: str, filepath: Path) -> None:
    """Append a message to the data quality warning log."""
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f"{message}\n")

def integrate_data() -> None:
    """
    Main logic for T012c:
    - Check for partial data.
    - Merge or promote.
    - Log warnings and update repo lists.
    """
    logger.info("Starting T012c: Data Integrity Check and Merge.")
    
    # Ensure processed directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    has_partial = PARTIAL_FILE.exists()
    has_canonical = CANONICAL_FILE.exists()
    
    if not has_partial and not has_canonical:
        logger.warning("No data files found (neither partial nor canonical). Exiting.")
        # Ensure canonical exists even if empty to prevent downstream crashes
        save_dicts_to_csv([], CANONICAL_FILE)
        return

    canonical_data = []
    truncated_repos = set()
    is_truncated = False

    # Load truncated repos list if it exists
    if TRUNCATED_REPOS_FILE.exists():
        truncated_repos = load_truncated_repos(TRUNCATED_REPOS_FILE)
        logger.info(f"Loaded existing truncated repos list: {len(truncated_repos)} repos.")

    # Logic 1: Partial exists, Canonical exists -> Merge
    if has_partial and has_canonical:
        logger.info("Both partial and canonical files exist. Merging...")
        canonical_data = load_csv_to_dicts(CANONICAL_FILE)
        partial_data = load_csv_to_dicts(PARTIAL_FILE)
        
        # Simple merge: append partial rows to canonical
        # In a real scenario, we might deduplicate by PR ID, but T012b implies
        # partial data is for specific repos that were cut off, so appending is safe
        # provided the PR IDs are unique across the set or we trust the pipeline flow.
        # To be safe, we assume partial data contains new rows not in canonical.
        
        original_count = len(canonical_data)
        canonical_data.extend(partial_data)
        new_count = len(canonical_data)
        
        logger.info(f"Merged {len(partial_data)} rows from partial. Total rows: {new_count}.")
        is_truncated = True

    # Logic 2: Partial exists, Canonical missing -> Promote
    elif has_partial and not has_canonical:
        logger.info("Partial file exists, canonical missing. Promoting partial to canonical.")
        canonical_data = load_csv_to_dicts(PARTIAL_FILE)
        logger.info(f"Promoted {len(canonical_data)} rows to canonical.")
        is_truncated = True

    # Logic 3: Canonical exists, Partial missing -> Keep canonical
    elif not has_partial and has_canonical:
        logger.info("Only canonical file exists. No merge needed.")
        canonical_data = load_csv_to_dicts(CANONICAL_FILE)
        # Check if truncated_repos.txt has entries but no partial file?
        # If truncated_repos.txt is not empty, we should still log a warning
        if truncated_repos:
            is_truncated = True
            logger.warning("Truncated repos list exists but no partial file found. Logging warning.")

    # If we have truncated repos (from file or merge), update logs
    if is_truncated:
        # Ensure truncated_repos set is updated (in case we just merged)
        # We need to identify which repos are in the partial data if we don't have the list yet.
        # However, T012b is responsible for writing the list. We trust that list.
        # If the list is empty but we merged, we should probably infer or just log.
        # For now, we rely on the list written by T012b.
        
        if not truncated_repos and has_partial:
            # Fallback: try to extract unique repo names from partial data if list is missing
            # This handles edge cases where T012b might have run but failed to write the list
            partial_data = load_csv_to_dicts(PARTIAL_FILE)
            partial_repos = set(row.get('repo_name', 'unknown') for row in partial_data if row.get('repo_name'))
            if partial_repos:
                truncated_repos.update(partial_repos)
                logger.info(f"Inferred {len(partial_repos)} truncated repos from partial data.")
        
        if truncated_repos:
            save_truncated_repos(truncated_repos, TRUNCATED_REPOS_FILE)
            
            # Log to quality warning log
            log_entry = f"TRUNCATED: Data merging occurred. Repos affected: {len(truncated_repos)}. List: {', '.join(sorted(truncated_repos))}"
            append_to_quality_log(log_entry, QUALITY_LOG_FILE)
            logger.warning(log_entry)
        else:
            logger.warning("Merge occurred but no repository names were found to log as truncated.")

    # Save the final canonical file
    save_dicts_to_csv(canonical_data, CANONICAL_FILE)
    logger.info(f"Canonical data saved to {CANONICAL_FILE} with {len(canonical_data)} rows.")
    
    # Clean up partial file if it was merged or promoted
    if has_partial:
        # Only remove if we successfully merged or promoted to avoid data loss in case of error
        # But the task implies the partial is temporary.
        os.remove(PARTIAL_FILE)
        logger.info(f"Removed temporary partial file: {PARTIAL_FILE}")

def main():
    """Entry point for the script."""
    try:
        integrate_data()
        logger.info("T012c completed successfully.")
    except Exception as e:
        logger.error(f"T012c failed with error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
