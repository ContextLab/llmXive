"""
Repository filtering utilities for T016.

Implements:
- Loading matched pairs
- Counting blocks by repo and label
- Identifying excluded repos (<5 LLM and <5 Human blocks)
- Filtering matched pairs
- Saving exclusions log and filtered pairs
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

from utils.models import MatchedPair
from utils.logging_config import get_logger

def load_matched_pairs(input_path: Path) -> List[MatchedPair]:
    """
    Load matched pairs from CSV file.
    
    Args:
        input_path: Path to matched_pairs.csv
        
    Returns:
        List of MatchedPair objects
    """
    pairs = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pair = MatchedPair(
                llm_block_id=row.get('llm_block_id', ''),
                human_block_id=row.get('human_block_id', ''),
                repo_name=row.get('repo_name', ''),
                propensity_score_llm=float(row.get('propensity_score_llm', 0)),
                propensity_score_human=float(row.get('propensity_score_human', 0)),
                match_id=row.get('match_id', '')
            )
            pairs.append(pair)
    return pairs

def count_blocks_by_repo_and_label(pairs: List[MatchedPair]) -> Dict[str, Dict[str, int]]:
    """
    Count LLM and Human blocks per repository.
    
    Args:
        pairs: List of MatchedPair objects
        
    Returns:
        Dict mapping repo_name -> {'llm': count, 'human': count}
    """
    repo_counts = defaultdict(lambda: {'llm': 0, 'human': 0})
    
    for pair in pairs:
        repo_name = pair.repo_name
        if pair.llm_block_id:
            repo_counts[repo_name]['llm'] += 1
        if pair.human_block_id:
            repo_counts[repo_name]['human'] += 1
    
    return dict(repo_counts)

def identify_excluded_repos(
    repo_counts: Dict[str, Dict[str, int]],
    min_llm_blocks: int = 5,
    min_human_blocks: int = 5
) -> Set[str]:
    """
    Identify repos that don't meet inclusion criteria.
    
    A repo is excluded if it has < min_llm_blocks LLM blocks
    OR < min_human_blocks Human blocks.
    
    Args:
        repo_counts: Dict of repo -> {'llm': count, 'human': count}
        min_llm_blocks: Minimum required LLM blocks
        min_human_blocks: Minimum required Human blocks
        
    Returns:
        Set of excluded repo names
    """
    excluded = set()
    
    for repo_name, counts in repo_counts.items():
        llm_count = counts.get('llm', 0)
        human_count = counts.get('human', 0)
        
        if llm_count < min_llm_blocks or human_count < min_human_blocks:
          excluded.add(repo_name)
    
    return excluded

def filter_matched_pairs(
    pairs: List[MatchedPair],
    excluded_repos: Set[str]
) -> List[MatchedPair]:
    """
    Filter out matched pairs from excluded repos.
    
    Args:
        pairs: List of MatchedPair objects
        excluded_repos: Set of repo names to exclude
        
    Returns:
        List of filtered MatchedPair objects
    """
    return [p for p in pairs if p.repo_name not in excluded_repos]

def save_exclusions_log(
    excluded_repos: Set[str],
    repo_counts: Dict[str, Dict[str, int]],
    output_path: Path
) -> None:
    """
    Save exclusions log to CSV.
    
    Args:
        excluded_repos: Set of excluded repo names
        repo_counts: Dict of repo -> {'llm': count, 'human': count}
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['repo_name', 'llm_block_count', 'human_block_count', 'exclusion_reason'])
        
        for repo_name in sorted(excluded_repos):
            counts = repo_counts.get(repo_name, {'llm': 0, 'human': 0})
            llm_count = counts.get('llm', 0)
            human_count = counts.get('human', 0)
            
            reasons = []
            if llm_count < 5:
                reasons.append(f"<5 LLM blocks ({llm_count})")
            if human_count < 5:
                reasons.append(f"<5 Human blocks ({human_count})")
            
            reason_str = "; ".join(reasons)
            writer.writerow([repo_name, llm_count, human_count, reason_str])

def save_filtered_pairs(pairs: List[MatchedPair], output_path: Path) -> None:
    """
    Save filtered matched pairs to CSV.
    
    Args:
        pairs: List of MatchedPair objects
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'llm_block_id', 'human_block_id', 'repo_name',
            'propensity_score_llm', 'propensity_score_human', 'match_id'
        ])
        
        for pair in pairs:
            writer.writerow([
                pair.llm_block_id,
                pair.human_block_id,
                pair.repo_name,
                pair.propensity_score_llm,
                pair.propensity_score_human,
                pair.match_id
            ])

def run_repo_filtering_pipeline(
    input_path: Path,
    output_path: Path,
    exclusions_log_path: Path,
    min_llm_blocks: int = 5,
    min_human_blocks: int = 5
) -> Tuple[List[MatchedPair], Set[str]]:
    """
    Run the complete repository filtering pipeline.
    
    Args:
        input_path: Path to input matched_pairs.csv
        output_path: Path to output matched_pairs_filtered.csv
        exclusions_log_path: Path to output repo_exclusions.csv
        min_llm_blocks: Minimum required LLM blocks per repo
        min_human_blocks: Minimum required Human blocks per repo
        
    Returns:
        Tuple of (filtered_pairs, excluded_repos)
    """
    logger = get_logger(__name__)
    
    # Load data
    logger.info(f"Loading matched pairs from {input_path}")
    pairs = load_matched_pairs(input_path)
    logger.info(f"Loaded {len(pairs)} matched pairs")
    
    # Count blocks per repo
    repo_counts = count_blocks_by_repo_and_label(pairs)
    logger.info(f"Analyzed {len(repo_counts)} repositories")
    
    # Identify excluded repos
    excluded_repos = identify_excluded_repos(repo_counts, min_llm_blocks, min_human_blocks)
    logger.info(f"Identified {len(excluded_repos)} excluded repositories")
    
    # Filter pairs
    filtered_pairs = filter_matched_pairs(pairs, excluded_repos)
    logger.info(f"Filtered to {len(filtered_pairs)} matched pairs")
    
    # Save outputs
    save_exclusions_log(excluded_repos, repo_counts, exclusions_log_path)
    logger.info(f"Saved exclusions log to {exclusions_log_path}")
    
    save_filtered_pairs(filtered_pairs, output_path)
    logger.info(f"Saved filtered pairs to {output_path}")
    
    return filtered_pairs, excluded_repos

# For backward compatibility with existing imports
def main():
    """CLI entry point."""
    import sys
    
    input_path = Path("data/processed/matched_pairs.csv")
    output_path = Path("data/processed/matched_pairs_filtered.csv")
    exclusions_log_path = Path("data/logs/repo_exclusions.csv")
    
    filtered_pairs, excluded_repos = run_repo_filtering_pipeline(
        input_path=input_path,
        output_path=output_path,
        exclusions_log_path=exclusions_log_path,
        min_llm_blocks=5,
        min_human_blocks=5
    )
    
    print(f"Excluded {len(excluded_repos)} repositories")
    print(f"Filtered pairs saved to: {output_path}")
    print(f"Exclusions log saved to: {exclusions_log_path}")
    
    return 0
