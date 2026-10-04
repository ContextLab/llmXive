"""
Repository filtering utilities for T016.
Enforces repository inclusion criteria: Exclude repos with <5 LLM and <5 Human blocks after tagging.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

# Import logging configuration from existing utility
from utils.logging_config import get_logger

# Constants
MIN_LLMS_BLOCKS = 5
MIN_HUMAN_BLOCKS = 5
INPUT_FILE = "data/processed/matched_pairs.csv"
OUTPUT_FILE = "data/processed/matched_pairs_filtered.csv"
EXCLUSIONS_LOG = "data/logs/repo_exclusions.csv"

logger = get_logger(__name__)


def load_matched_pairs(input_path: str) -> List[Dict]:
    """Load matched pairs from CSV."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    pairs = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append(row)
    return pairs


def count_blocks_by_repo_and_label(pairs: List[Dict]) -> Dict[str, Dict[str, int]]:
    """
    Count LLM and Human blocks per repository.
    Returns: { repo_id: { 'LLM': count, 'Human': count } }
    """
    counts = defaultdict(lambda: {'LLM': 0, 'Human': 0})
    for pair in pairs:
        repo_id = pair.get('repo_id')
        # The label is expected to be in 'label' or 'source_label' column based on matching output
        # Assuming 'label' contains the classification (LLM or Human)
        label = pair.get('label', '').strip()
        if label in ('LLM', 'Human'):
            counts[repo_id][label] += 1
    return dict(counts)


def identify_excluded_repos(counts: Dict[str, Dict[str, int]]) -> Set[str]:
    """
    Identify repositories that do not meet the inclusion criteria:
    Must have >= 5 LLM blocks AND >= 5 Human blocks.
    """
    excluded = set()
    for repo_id, label_counts in counts.items():
        llm_count = label_counts.get('LLM', 0)
        human_count = label_counts.get('Human', 0)
        if llm_count < MIN_LLMS_BLOCKS or human_count < MIN_HUMAN_BLOCKS:
          excluded.add(repo_id)
          logger.warning(
              "Repo %s excluded: LLM=%d, Human=%d (threshold: %d/%d)",
              repo_id, llm_count, human_count, MIN_LLMS_BLOCKS, MIN_HUMAN_BLOCKS
          )
    return excluded


def filter_matched_pairs(pairs: List[Dict], excluded_repos: Set[str]) -> List[Dict]:
    """Filter out pairs belonging to excluded repositories."""
    return [p for p in pairs if p.get('repo_id') not in excluded_repos]


def save_exclusions_log(excluded_repos: Set[str], counts: Dict[str, Dict[str, int]], output_path: str):
    """Save the list of excluded repositories and their counts to a CSV log."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['repo_id', 'llm_count', 'human_count', 'reason'])
        for repo_id in sorted(excluded_repos):
            counts_data = counts.get(repo_id, {'LLM': 0, 'Human': 0})
            llm = counts_data['LLM']
            human = counts_data['Human']
            reason = []
            if llm < MIN_LLMS_BLOCKS:
                reason.append(f"LLM < {MIN_LLMS_BLOCKS}")
            if human < MIN_HUMAN_BLOCKS:
                reason.append(f"Human < {MIN_HUMAN_BLOCKS}")
            writer.writerow([repo_id, llm, human, "; ".join(reason)])
    logger.info("Exclusions log saved to %s", output_path)


def save_filtered_pairs(pairs: List[Dict], output_path: str):
    """Save the filtered matched pairs to a new CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not pairs:
        logger.warning("No pairs remaining after filtering. Writing empty file with headers.")
        # Write headers only if no data
        with open(path, 'w', newline='', encoding='utf-8') as f:
            # We need to know headers; assume they exist in input or define standard ones
            # Since we loaded from CSV, we can infer headers from the first item if available,
            # but here we just write a generic header or rely on the fact that we usually have data.
            # To be safe, if pairs is empty, we might need to read headers from input file again.
            # However, for this task, we assume input exists and has headers.
            # We'll re-read input headers if pairs is empty to ensure schema correctness.
            pass 
        
        # Re-load headers from input to write empty file correctly
        input_file = Path(INPUT_FILE)
        if input_file.exists():
            with open(input_file, 'r', newline='', encoding='utf-8') as f_in:
                reader = csv.DictReader(f_in)
                fieldnames = reader.fieldnames
            with open(path, 'w', newline='', encoding='utf-8') as f_out:
                writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                writer.writeheader()
        return

    # Write with headers from the first pair (assuming uniform schema)
    fieldnames = list(pairs[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pairs)
    
    logger.info("Filtered pairs saved to %s (total: %d)", output_path, len(pairs))


def run_repo_filtering_pipeline(input_path: str = INPUT_FILE, 
                                output_path: str = OUTPUT_FILE, 
                                exclusions_path: str = EXCLUSIONS_LOG):
    """
    Execute the full filtering pipeline for T016.
    1. Load matched pairs.
    2. Count blocks per repo/label.
    3. Identify excluded repos.
    4. Filter pairs.
    5. Save exclusions log and filtered pairs.
    """
    logger.info("Starting repository filtering pipeline...")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file {input_path} not found. "
                                "Ensure T015 (matching) has completed successfully.")
    
    pairs = load_matched_pairs(input_path)
    logger.info("Loaded %d matched pairs.", len(pairs))
    
    counts = count_blocks_by_repo_and_label(pairs)
    logger.info("Analyzed block counts for %d repositories.", len(counts))
    
    excluded_repos = identify_excluded_repos(counts)
    logger.info("Identified %d excluded repositories.", len(excluded_repos))
    
    filtered_pairs = filter_matched_pairs(pairs, excluded_repos)
    logger.info("Remaining pairs after filtering: %d.", len(filtered_pairs))
    
    save_exclusions_log(excluded_repos, counts, exclusions_path)
    save_filtered_pairs(filtered_pairs, output_path)
    
    logger.info("Repository filtering pipeline completed successfully.")
    return filtered_pairs, excluded_repos


def main():
    """Entry point for the script."""
    setup_logging = None # Logging is configured globally or via config
    # Ensure logging is set up if not already done by the main runner
    try:
        run_repo_filtering_pipeline()
    except Exception as e:
        logger.error("Pipeline failed: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()