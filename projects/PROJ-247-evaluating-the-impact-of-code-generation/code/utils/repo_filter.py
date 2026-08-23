"""
Repository inclusion criteria enforcement module.

Filters matched pairs based on repository-level block counts.
Excludes repositories with fewer than 5 LLM-generated and 5 Human-written code blocks.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

from .models import MatchedPair, LabelType

# Constants
MIN_LLM_BLOCKS = 5
MIN_HUMAN_BLOCKS = 5
REPO_EXCLUSIONS_LOG = "data/logs/repo_exclusions.csv"
MATCHED_PAIRS_INPUT = "data/processed/matched_pairs.csv"
MATCHED_PAIRS_OUTPUT = "data/processed/matched_pairs_filtered.csv"

logger = logging.getLogger(__name__)


def load_matched_pairs(input_path: str) -> List[Dict]:
    """Load matched pairs from CSV file."""
    pairs = []
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append(row)
    
    logger.info(f"Loaded {len(pairs)} matched pairs from {input_path}")
    return pairs


def count_blocks_by_repo_and_label(pairs: List[Dict]) -> Dict[str, Dict[LabelType, int]]:
    """
    Count LLM and Human blocks per repository.
    
    Args:
        pairs: List of matched pair dictionaries containing block_id, repo_id, and label.
    
    Returns:
        Dictionary mapping repo_id to counts of LLM and Human blocks.
    """
    repo_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"LLM": 0, "HUMAN": 0})
    
    for pair in pairs:
        repo_id = pair.get("repo_id")
        label = pair.get("label")  # Expected values: "LLM" or "HUMAN"
        
        if not repo_id or not label:
            logger.warning(f"Skipping pair with missing repo_id or label: {pair}")
            continue
        
        if label not in ("LLM", "HUMAN"):
            logger.warning(f"Invalid label '{label}' for repo {repo_id}")
            continue
        
        repo_counts[repo_id][label] += 1
    
    return repo_counts


def identify_excluded_repos(repo_counts: Dict[str, Dict[str, int]]) -> Set[str]:
    """
    Identify repositories that do not meet inclusion criteria.
    
    A repository is excluded if it has fewer than MIN_LLM_BLOCKS LLM blocks
    OR fewer than MIN_HUMAN_BLOCKS Human blocks.
    
    Args:
        repo_counts: Dictionary of block counts per repository.
    
    Returns:
        Set of repo_ids that should be excluded.
    """
    excluded = set()
    
    for repo_id, counts in repo_counts.items():
        llm_count = counts.get("LLM", 0)
        human_count = counts.get("HUMAN", 0)
        
        if llm_count < MIN_LLM_BLOCKS:
            excluded.add(repo_id)
            logger.info(f"Excluding repo {repo_id}: LLM count {llm_count} < {MIN_LLM_BLOCKS}")
        elif human_count < MIN_HUMAN_BLOCKS:
            excluded.add(repo_id)
            logger.info(f"Excluding repo {repo_id}: Human count {human_count} < {MIN_HUMAN_BLOCKS}")
    
    return excluded


def filter_matched_pairs(
    pairs: List[Dict], 
    excluded_repos: Set[str]
) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter matched pairs to exclude those from excluded repositories.
    
    Args:
        pairs: List of all matched pairs.
        excluded_repos: Set of repo_ids to exclude.
    
    Returns:
        Tuple of (filtered_pairs, excluded_pairs)
    """
    filtered = []
    excluded = []
    
    for pair in pairs:
        repo_id = pair.get("repo_id")
        if repo_id in excluded_repos:
            excluded.append(pair)
        else:
            filtered.append(pair)
    
    return filtered, excluded


def save_exclusions_log(
    excluded_repos: Set[str],
    repo_counts: Dict[str, Dict[str, int]],
    output_path: str
) -> None:
    """
    Save repository exclusions log to CSV.
    
    Args:
        excluded_repos: Set of excluded repo_ids.
        repo_counts: Dictionary of block counts per repository.
        output_path: Path to output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["repo_id", "llm_count", "human_count", "exclusion_reason"])
        
        for repo_id in excluded_repos:
            counts = repo_counts.get(repo_id, {"LLM": 0, "HUMAN": 0})
            llm_count = counts.get("LLM", 0)
            human_count = counts.get("HUMAN", 0)
            
            if llm_count < MIN_LLM_BLOCKS:
                reason = f"LLM blocks ({llm_count}) < {MIN_LLM_BLOCKS}"
            elif human_count < MIN_HUMAN_BLOCKS:
                reason = f"Human blocks ({human_count}) < {MIN_HUMAN_BLOCKS}"
            else:
                reason = "Unknown"
            
            writer.writerow([repo_id, llm_count, human_count, reason])
    
    logger.info(f"Saved {len(excluded_repos)} exclusions to {output_path}")


def save_filtered_pairs(pairs: List[Dict], output_path: str) -> None:
    """
    Save filtered matched pairs to CSV.
    
    Args:
        pairs: List of filtered matched pairs.
        output_path: Path to output CSV file.
    """
    if not pairs:
        logger.warning("No pairs to save after filtering")
        # Still create empty file with headers
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([])  # Will be overwritten with actual headers
        return
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get fieldnames from first pair
    fieldnames = list(pairs[0].keys())
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pairs)
    
    logger.info(f"Saved {len(pairs)} filtered pairs to {output_path}")


def run_repo_filtering_pipeline(
    input_path: str = MATCHED_PAIRS_INPUT,
    output_path: str = MATCHED_PAIRS_OUTPUT,
    exclusions_log_path: str = REPO_EXCLUSIONS_LOG
) -> Dict:
    """
    Run the complete repository filtering pipeline.
    
    Args:
        input_path: Path to input matched pairs CSV.
        output_path: Path to output filtered pairs CSV.
        exclusions_log_path: Path to exclusions log CSV.
    
    Returns:
        Dictionary with pipeline statistics.
    """
    logger.info("Starting repository filtering pipeline")
    
    # Load input data
    pairs = load_matched_pairs(input_path)
    total_pairs = len(pairs)
    
    if total_pairs == 0:
        logger.warning("No matched pairs found in input file")
        return {
            "total_pairs": 0,
            "filtered_pairs": 0,
            "excluded_pairs": 0,
            "excluded_repos": 0,
            "status": "empty_input"
        }
    
    # Count blocks per repository
    repo_counts = count_blocks_by_repo_and_label(pairs)
    total_repos = len(repo_counts)
    
    # Identify excluded repositories
    excluded_repos = identify_excluded_repos(repo_counts)
    
    # Filter pairs
    filtered_pairs, excluded_pairs = filter_matched_pairs(pairs, excluded_repos)
    
    # Save outputs
    save_exclusions_log(excluded_repos, repo_counts, exclusions_log_path)
    save_filtered_pairs(filtered_pairs, output_path)
    
    stats = {
        "total_pairs": total_pairs,
        "total_repos": total_repos,
        "filtered_pairs": len(filtered_pairs),
        "excluded_pairs": len(excluded_pairs),
        "excluded_repos": len(excluded_repos),
        "min_llm_blocks": MIN_LLM_BLOCKS,
        "min_human_blocks": MIN_HUMAN_BLOCKS,
        "status": "success"
    }
    
    logger.info(f"Pipeline completed. Stats: {stats}")
    return stats


def main():
    """Main entry point for CLI execution."""
    import sys
    
    # Setup logging
    from utils.logging_config import setup_logging
    setup_logging()
    
    logger.info("Repository Filtering Pipeline - T016")
    
    try:
        stats = run_repo_filtering_pipeline()
        
        # Print summary
        print(f"\nRepository Filtering Summary:")
        print(f"  Total pairs processed: {stats['total_pairs']}")
        print(f"  Total repositories: {stats['total_repos']}")
        print(f"  Pairs retained: {stats['filtered_pairs']}")
        print(f"  Pairs excluded: {stats['excluded_pairs']}")
        print(f"  Repositories excluded: {stats['excluded_repos']}")
        print(f"  Output file: {MATCHED_PAIRS_OUTPUT}")
        print(f"  Exclusions log: {REPO_EXCLUSIONS_LOG}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Pipeline failed with unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
