import logging
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from utils import api_request_with_backoff, validate_json_schema
from logging_config import get_logger, capture_rate_limit_headers

# Configure logger for this module
logger = get_logger(__name__)

def extract_commit_keywords(commit_messages: List[str]) -> List[str]:
    """
    Extract keywords from commit messages that suggest AI involvement.
    FR-002: Keywords include 'copilot', 'ai-generated', etc.
    """
    keywords = ["copilot", "ai-generated", "ai-assisted", "llm-code"]
    found_keywords = []
    for msg in commit_messages:
        msg_lower = msg.lower()
        for kw in keywords:
            if kw in msg_lower and kw not in found_keywords:
                found_keywords.append(kw)
    return found_keywords

def check_labels(labels: List[str]) -> List[str]:
    """
    Check if any of the PR labels indicate AI involvement.
    FR-002: Labels include 'ai-generated', 'copilot-assisted', 'llm-code'.
    """
    ai_labels = ["ai-generated", "copilot-assisted", "llm-code"]
    found_labels = []
    for label in labels:
        label_lower = label.lower()
        if label_lower in ai_labels:
            found_labels.append(label_lower)
    return found_labels

def classify_pr(commit_messages: List[str], labels: List[str]) -> str:
    """
    Classify a PR as 'AI-assisted' or 'Non-AI' based on commit messages and labels.
    FR-002: Logic combines keyword detection and label checking.
    """
    msg_keywords = extract_commit_keywords(commit_messages)
    pr_labels = check_labels(labels)

    if msg_keywords or pr_labels:
        return "AI-assisted"
    return "Non-AI"

def fetch_repos_from_github() -> List[Dict[str, Any]]:
    """
    Fetch top Python and JavaScript repositories by star count.
    T012a: Uses GitHub API search endpoints.
    """
    repos = []
    languages = ["Python", "JavaScript"]
    
    for lang in languages:
        query = f"language:{lang}+stars:>10000"
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=5"
        
        logger.info(f"Fetching top repos for {lang}...")
        response, headers = api_request_with_backoff(url, {})
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            for item in items:
                repos.append({
                    "name": item["full_name"],
                    "stars": item["stargazers_count"]
                })
            capture_rate_limit_headers(headers)
        else:
            logger.error(f"Failed to fetch repos for {lang}: {response.status_code}")
    
    return repos

def fetch_prs_for_repo(repo_name: str) -> List[Dict[str, Any]]:
    """
    Fetch all Pull Requests for a given repository.
    T012b: Iterates through PRs to extract metadata.
    """
    prs = []
    url = f"https://api.github.com/repos/{repo_name}/pulls?state=all&per_page=100"
    page = 1
    
    while url:
        logger.debug(f"Fetching PRs for {repo_name}, page {page}...")
        response, headers = api_request_with_backoff(url, {})
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch PRs for {repo_name}: {response.status_code}")
            break
        
        data = response.json()
        if not data:
            break
        
        prs.extend(data)
        capture_rate_limit_headers(headers)
        
        # Check for next page link
        if 'Link' in headers:
            links = headers['Link'].split(',')
            next_url = None
            for link in links:
                if 'rel="next"' in link:
                    next_url = link.split(';')[0].strip('<>').strip()
                    break
            url = next_url
            page += 1
        else:
            url = None
    
    return prs

def fetch_commits_for_pr(repo_name: str, pr_number: int) -> List[str]:
    """
    Fetch commit messages for a specific PR.
    T012b: Iterates through commits to extract messages.
    """
    messages = []
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/commits?per_page=100"
    
    while url:
        response, headers = api_request_with_backoff(url, {})
        if response.status_code != 200:
            logger.error(f"Failed to fetch commits for PR #{pr_number}: {response.status_code}")
            break
        
        data = response.json()
        for commit in data:
            msg = commit.get("commit", {}).get("message", "")
            if msg:
                messages.append(msg)
        
        capture_rate_limit_headers(headers)
        
        if 'Link' in headers:
            links = headers['Link'].split(',')
            next_url = None
            for link in links:
                if 'rel="next"' in link:
                    next_url = link.split(';')[0].strip('<>').strip()
                    break
            url = next_url
        else:
            url = None
    
    return messages

def parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse ISO 8601 datetime string to datetime object.
    Handles 'Z' suffix and standard formats.
    """
    if not date_str:
        return None
    try:
        # Handle 'Z' suffix by replacing with '+00:00' for fromisoformat
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str)
    except ValueError:
        # Fallback for formats without timezone info if necessary
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return None

def calculate_turnaround_hours(created_at: str, merged_at: str) -> Optional[float]:
    """
    Calculate turnaround time in total calendar hours.
    T016 / FR-003: (merged_at - created_at) in hours.
    Returns None if either timestamp is missing or invalid.
    """
    if not created_at or not merged_at:
        return None
    
    created_dt = parse_iso_datetime(created_at)
    merged_dt = parse_iso_datetime(merged_at)
    
    if not created_dt or not merged_dt:
        return None
    
    # Ensure merged is after created
    if merged_dt < created_dt:
        logger.warning(f"Merged time before created time for PR. Setting to 0.")
        return 0.0
    
    delta = merged_dt - created_dt
    return delta.total_seconds() / 3600.0

def process_pr_data(pr: Dict[str, Any], repo_name: str) -> Optional[Dict[str, Any]]:
    """
    Process a single PR object into a standardized record.
    T013: Excludes PRs with missing merged_at.
    T015: Classifies PR as AI or Non-AI.
    T016: Calculates turnaround hours.
    """
    # T013: Exclude PRs with missing merged_at
    merged_at = pr.get("merged_at")
    created_at = pr.get("created_at")
    
    if not merged_at:
        return None
    
    # Extract necessary fields
    pr_id = str(pr.get("number", ""))
    labels = [label.get("name", "") for label in pr.get("labels", [])]
    
    # We need to fetch commits for classification (T015)
    # Note: In a real pipeline, this might be done in a separate step or cached
    # For this implementation, we fetch commits here to ensure we have the data
    commit_messages = fetch_commits_for_pr(repo_name, int(pr_id))
    
    # T015: Classify
    classification = classify_pr(commit_messages, labels)
    
    # T016: Calculate turnaround
    turnaround_hours = calculate_turnaround_hours(created_at, merged_at)
    
    if turnaround_hours is None:
        logger.warning(f"Could not calculate turnaround for PR {pr_id} in {repo_name}")
        return None
    
    return {
        "pr_id": pr_id,
        "repo_name": repo_name,
        "created_at": created_at,
        "merged_at": merged_at,
        "labels": labels,
        "commit_messages": commit_messages,
        "turnaround_hours": turnaround_hours,
        "classification": classification
    }

def main():
    """
    Main entry point for data fetching and processing.
    Orchestrates the flow: Fetch repos -> Fetch PRs -> Process -> Save.
    """
    logger.info("Starting data acquisition pipeline...")
    
    # T012a: Fetch repos
    repos = fetch_repos_from_github()
    if not repos:
        logger.error("No repositories fetched. Aborting.")
        return
    
    logger.info(f"Fetched {len(repos)} repositories.")
    
    all_processed_prs = []
    skipped_repos = []
    
    for repo in repos:
        repo_name = repo["name"]
        logger.info(f"Processing repository: {repo_name}")
        
        # T012b: Fetch PRs
        prs = fetch_prs_for_repo(repo_name)
        if not prs:
            logger.warning(f"No PRs found for {repo_name}")
            continue
        
        processed_prs = []
        for pr in prs:
            result = process_pr_data(pr, repo_name)
            if result:
                processed_prs.append(result)
            else:
                # T013: Count exclusions
                pass 
        
        # T014: Skip repos with < 50 PRs after filtering
        if len(processed_prs) < 50:
            logger.warning(f"Skipping {repo_name}: only {len(processed_prs)} valid PRs (threshold: 50)")
            skipped_repos.append(repo_name)
            continue
        
        all_processed_prs.extend(processed_prs)
        logger.info(f"Added {len(processed_prs)} PRs from {repo_name}")
    
    if skipped_repos:
        logger.info(f"Skipped repos due to low PR count: {skipped_repos}")
    
    logger.info(f"Total processed PRs: {len(all_processed_prs)}")
    
    # Save raw and processed data (T018 placeholder logic)
    import json
    import pandas as pd
    
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    
    # Save raw repos list
    with open("data/raw/repos.json", "w") as f:
        json.dump(repos, f, indent=2)
    
    # Save processed PRs
    if all_processed_prs:
        df = pd.DataFrame(all_processed_prs)
        df.to_csv("data/processed/pr_data.csv", index=False)
        logger.info("Saved processed data to data/processed/pr_data.csv")
    else:
        logger.warning("No processed data to save.")

if __name__ == "__main__":
    main()