import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass

# Import from project structure
from config import (
    GITHUB_TOKEN,
    RATE_LIMIT_HOURLY,
    BACKOFF_INITIAL,
    BACKOFF_MAX,
    STRATIFICATION_SEED,
    MAX_REVIEW_DAYS,
)
from data.env_config import get_github_token, setup_github_credentials
from data.logging_config import setup_logging, get_logger
from data.rate_limiter import TokenBucketRateLimiter, create_limiter

# Setup logging
logger = get_logger(__name__)

# Keywords for LLM disclosure (used in T013 and T014)
LLM_KEYWORDS = ["copilot", "llm", "generated", "ai-generated", "code generation"]

@dataclass
class RepoStats:
    repo_id: str
    star_count: int
    pr_count: int
    disclosing_count: int
    disclosing_ratio: float

def load_repo_list(repo_list_path: str = "data/config/repo_list.txt") -> List[Dict[str, Any]]:
    """Load repository list from config file."""
    repos = []
    path = Path(repo_list_path)
    if not path.exists():
        logger.error(f"Repo list file not found: {repo_list_path}")
        return repos

    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(',')
                if len(parts) >= 2:
                    repos.append({
                        'repo_id': parts[0].strip(),
                        'star_count': int(parts[1].strip())
                    })
    return repos

def check_keywords(text: str) -> bool:
    """Check if text contains any LLM disclosure keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in LLM_KEYWORDS)

def fetch_prs_for_repo(
    repo_id: str,
    token: str,
    rate_limiter: TokenBucketRateLimiter
) -> List[Dict[str, Any]]:
    """Fetch PRs for a specific repository from GitHub API."""
    import requests

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    prs = []
    page = 1
    
    while True:
        url = f"https://api.github.com/repos/{repo_id}/pulls"
        params = {
            "state": "all",
            "per_page": 100,
            "page": page
        }
        
        rate_limiter.wait_if_needed()
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            for pr in data:
                prs.append({
                    "repo": repo_id,
                    "pr_number": pr["number"],
                    "title": pr.get("title", ""),
                    "body": pr.get("body", ""),
                    "created_at": pr.get("created_at", ""),
                    "merged_at": pr.get("merged_at", ""),
                    "author": pr.get("user", {}).get("login", ""),
                    "lines_changed": pr.get("additions", 0) + pr.get("deletions", 0),
                    "state": pr.get("state", "")
                })
            
            if len(data) < 100:
                break
            page += 1
            
        except requests.exceptions.RequestException as e:
            if hasattr(response, 'status_code') and response.status_code == 403:
                logger.warning(f"Rate limited for repo {repo_id}. Backing off...")
                rate_limiter.wait_if_needed(force_wait=True)
                continue
            logger.error(f"Error fetching PRs for {repo_id}: {e}")
            break
    
    return prs

def apply_stratified_sampling(
    prs_df: pd.DataFrame,
    repo_stats: List[RepoStats],
    sample_size_per_bin: int = 50
) -> pd.DataFrame:
    """
    Apply stratified sampling based on repo star count bins.
    Bins: 1k-10k, 10k-100k, >100k
    """
    np.random.seed(STRATIFICATION_SEED)
    
    # Define bins
    bins = [1000, 10000, 100000, float('inf')]
    labels = ['1k-10k', '10k-100k', '>100k']
    
    # Add star count to PRs dataframe
    repo_star_map = {r.repo_id: r.star_count for r in repo_stats}
    prs_df['star_count'] = prs_df['repo'].map(repo_star_map)
    
    # Create bin column
    prs_df['star_bin'] = pd.cut(
        prs_df['star_count'],
        bins=bins,
        labels=labels,
        right=False
    )
    
    # Sample from each bin
    sampled_dfs = []
    for bin_label in labels:
        bin_df = prs_df[prs_df['star_bin'] == bin_label]
        if len(bin_df) > 0:
            # Sample up to sample_size_per_bin
            sample_size = min(len(bin_df), sample_size_per_bin)
            sampled = bin_df.sample(n=sample_size, random_state=STRATIFICATION_SEED)
            sampled_dfs.append(sampled)
    
    if sampled_dfs:
        sampled_df = pd.concat(sampled_dfs, ignore_index=True)
        return sampled_df
    return prs_df

def apply_exclusion_logic(
    prs_df: pd.DataFrame,
    repo_stats: List[RepoStats],
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Exclude repositories where >50% of PRs contain LLM keywords.
    """
    # Calculate disclosing ratio for each repo
    repo_disclosing_stats = {}
    for repo_id, stats in zip(prs_df['repo'].unique(), repo_stats):
        repo_prs = prs_df[prs_df['repo'] == repo_id]
        total_prs = len(repo_prs)
        if total_prs == 0:
            continue
        
        disclosing_count = repo_prs['origin_label'].sum()
        ratio = disclosing_count / total_prs
        repo_disclosing_stats[repo_id] = ratio
    
    # Filter out repos exceeding threshold
    included_repos = [
        repo_id for repo_id, ratio in repo_disclosing_stats.items()
        if ratio <= threshold
    ]
    
    logger.info(f"Excluding repos with >{threshold*100}% disclosing PRs. "
               f"Kept {len(included_repos)} repos, excluded {len(repo_disclosing_stats) - len(included_repos)}")
    
    filtered_df = prs_df[prs_df['repo'].isin(included_repos)].copy()
    return filtered_df

def main():
    """
    Main execution for T014: Stratified sampling and exclusion logic.
    
    Reads raw PR data from T013 output, applies stratified sampling
    and exclusion logic, saves filtered dataset.
    """
    setup_logging()
    
    # Initialize rate limiter
    token = get_github_token()
    if not token:
        logger.error("GitHub token not configured. Run setup first.")
        return
    
    rate_limiter = create_limiter()
    
    # Load raw PR data (output from T013)
    raw_data_path = Path("data/raw/prs_raw.json")
    if not raw_data_path.exists():
        logger.error(f"Raw data not found at {raw_data_path}. Run T013 first.")
        return
    
    logger.info("Loading raw PR data...")
    with open(raw_data_path, 'r') as f:
        raw_prs = json.load(f)
    
    if not raw_prs:
        logger.warning("No PRs found in raw data.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(raw_prs)
    
    # Calculate origin_label (disclosing vs non-disclosing)
    # This should have been done in T013, but we ensure it's here for safety
    if 'origin_label' not in df.columns:
        logger.info("Calculating origin_label from keywords...")
        df['title_body'] = df['title'].fillna('') + ' ' + df['body'].fillna('')
        df['origin_label'] = df['title_body'].apply(lambda x: 1 if check_keywords(x) else 0)
    
    # Load repo stats for stratification
    repos = load_repo_list()
    repo_stats = []
    for repo in repos:
        repo_id = repo['repo_id']
        star_count = repo['star_count']
        
        # Count PRs for this repo
        repo_prs = df[df['repo'] == repo_id]
        pr_count = len(repo_prs)
        disclosing_count = repo_prs['origin_label'].sum()
        disclosing_ratio = disclosing_count / pr_count if pr_count > 0 else 0
        
        repo_stats.append(RepoStats(
            repo_id=repo_id,
            star_count=star_count,
            pr_count=pr_count,
            disclosing_count=disclosing_count,
            disclosing_ratio=disclosing_ratio
        ))
    
    logger.info(f"Loaded {len(repo_stats)} repositories for processing")
    
    # Step 1: Apply stratified sampling
    logger.info("Applying stratified sampling...")
    sampled_df = apply_stratified_sampling(df, repo_stats, sample_size_per_bin=100)
    logger.info(f"Sampled {len(sampled_df)} PRs across star count bins")
    
    # Step 2: Apply exclusion logic (>50% exclusion)
    logger.info("Applying >50% exclusion logic...")
    filtered_df = apply_exclusion_logic(sampled_df, repo_stats, threshold=0.5)
    logger.info(f"Final dataset: {len(filtered_df)} PRs after exclusion")
    
    # Prepare output columns
    output_cols = [
        'repo', 'pr_number', 'title', 'body', 'created_at', 
        'merged_at', 'author', 'lines_changed', 'origin_label',
        'star_count', 'star_bin'
    ]
    
    # Ensure all columns exist
    for col in output_cols:
        if col not in filtered_df.columns:
            filtered_df[col] = None
    
    output_df = filtered_df[output_cols]
    
    # Save to processed directory
    output_path = Path("data/processed/sampled_prs.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered dataset to {output_path}")
    
    # Log summary statistics
    logger.info("=== Sampling Summary ===")
    logger.info(f"Total raw PRs: {len(df)}")
    logger.info(f"After stratified sampling: {len(sampled_df)}")
    logger.info(f"After exclusion (>50% disclosing): {len(filtered_df)}")
    logger.info(f"Disclosing ratio in final set: {filtered_df['origin_label'].mean():.2%}")
    
    # Log repo exclusion details
    excluded_repos = [
        r for r in repo_stats 
        if r.repo_id not in filtered_df['repo'].unique()
    ]
    if excluded_repos:
        logger.info("Excluded repos:")
        for r in excluded_repos:
            logger.info(f"  {r.repo_id}: {r.disclosing_ratio:.2%} disclosing ({r.disclosing_count}/{r.pr_count} PRs)")

if __name__ == "__main__":
    main()