"""
Fetch real human review comments from the GitHub API for PRs extracted in T012.

This module fetches actual comments from:
1. Pull request review comments: /repos/{owner}/{repo}/pulls/{number}/comments
2. Issue comments on PRs: /repos/{owner}/{repo}/issues/{number}/comments

Output is saved to data/annotations/raw_comments.json
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

from code.config.settings import get_paths, get_target_repos, ensure_directories
from code.src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

def make_github_request(url: str, token: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Make a request to the GitHub API with rate limit handling.
    
    Args:
        url: The API endpoint URL
        token: GitHub personal access token
        params: Optional query parameters
        
    Returns:
        JSON response as dict, or None if request fails
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-research-pipeline"
    }
    
    max_retries = 5
    base_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 403:
                if "rate limit" in response.text.lower():
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    wait_time = max(reset_time - int(time.time()), 60)
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds.")
                    time.sleep(wait_time)
                    continue
                else:
                    # Forbidden for other reasons (e.g., missing scope)
                    logger.error(f"GitHub API forbidden (403): {response.text}")
                    return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(base_delay * (attempt + 1))
            continue
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
    return None

def fetch_review_comments_for_pr(owner: str, repo: str, pr_number: int, token: str) -> List[Dict[str, Any]]:
    """
    Fetch pull request review comments (inline code comments).
    
    Endpoint: GET /repos/{owner}/{repo}/pulls/{number}/comments
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
        token: GitHub API token
        
    Returns:
        List of review comment dictionaries
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    comments = []
    
    page = 1
    per_page = 100
    
    while True:
        params = {"per_page": per_page, "page": page}
        result = make_github_request(url, token, params)
        
        if result is None:
            logger.warning(f"Failed to fetch review comments for PR {pr_number} at page {page}")
            break
        
        if not result:
            break
        
        comments.extend(result)
        
        # Check if there are more pages
        if len(result) < per_page:
            break
        
        page += 1
        time.sleep(0.5)  # Be nice to the API
    
    return comments

def fetch_issue_comments_for_pr(owner: str, repo: str, pr_number: int, token: str) -> List[Dict[str, Any]]:
    """
    Fetch issue comments on a pull request (top-level discussion comments).
    
    Endpoint: GET /repos/{owner}/{repo}/issues/{number}/comments
    Note: PRs are also issues in GitHub's API, so we use the issue endpoint.
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
        token: GitHub API token
        
    Returns:
        List of issue comment dictionaries
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    comments = []
    
    page = 1
    per_page = 100
    
    while True:
        params = {"per_page": per_page, "page": page}
        result = make_github_request(url, token, params)
        
        if result is None:
            logger.warning(f"Failed to fetch issue comments for PR {pr_number} at page {page}")
            break
        
        if not result:
            break
        
        comments.extend(result)
        
        if len(result) < per_page:
            break
        
        page += 1
        time.sleep(0.5)
    
    return comments

def normalize_comment(comment: Dict[str, Any], comment_type: str) -> Dict[str, Any]:
    """
    Normalize a GitHub comment to our standard schema.
    
    Args:
        comment: Raw comment from GitHub API
        comment_type: Either 'review' (inline) or 'issue' (top-level)
        
    Returns:
        Normalized comment dictionary with fields:
        - reviewer_id: String identifier of the commenter
        - comment_body: The comment text
        - timestamp: ISO 8601 timestamp
        - is_confirmed: Boolean (always False for raw fetch, determined later)
        - linked_pr_id: The PR number this comment belongs to
        - comment_type: 'review' or 'issue'
        - file_path: For review comments, the file path (None for issue comments)
        - line_start: For review comments, the line number (None for issue comments)
        """
    normalized = {
        "reviewer_id": comment.get("user", {}).get("login", "unknown"),
        "comment_body": comment.get("body", ""),
        "timestamp": comment.get("created_at", ""),
        "is_confirmed": False,  # Will be determined by T014c
        "linked_pr_id": None,
        "comment_type": comment_type,
        "file_path": None,
        "line_start": None,
        "github_comment_id": comment.get("id"),
        "original_url": comment.get("html_url")
    }
    
    if comment_type == "review":
        # Review comments are inline on specific files
        normalized["file_path"] = comment.get("path")
        normalized["line_start"] = comment.get("line") or comment.get("original_line")
        normalized["linked_pr_id"] = comment.get("pull_request_review_id")
    else:
        # Issue comments are top-level
        normalized["linked_pr_id"] = comment.get("pull_request", {}).get("url")
        
        # Extract PR number from URL if possible
        url = comment.get("pull_request", {}).get("url", "")
        if url:
            try:
                # URL format: https://api.github.com/repos/{owner}/{repo}/pulls/{number}
                parts = url.split("/")
                if len(parts) >= 2:
                    normalized["linked_pr_id"] = int(parts[-1])
            except (ValueError, IndexError):
                pass
    
    return normalized

def load_existing_prs(raw_data_dir: Path) -> List[Dict[str, Any]]:
    """
    Load PR data from T012 (raw fetched JSON).
    
    Args:
        raw_data_dir: Path to data/raw directory
        
    Returns:
        List of PR dictionaries
    """
    prs = []
    
    # Look for JSON files in data/raw
    for file_path in raw_data_dir.glob("*.json"):
        if file_path.name.startswith(".") or file_path.name == "checksums.json":
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Handle both list and dict formats
            if isinstance(data, list):
                prs.extend(data)
            elif isinstance(data, dict):
                if "prs" in data:
                    prs.extend(data["prs"])
                else:
                    prs.append(data)
                    
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {file_path}: {e}")
            continue
    
    logger.info(f"Loaded {len(prs)} PRs from raw data")
    return prs

def extract_repo_info(pr_data: Dict[str, Any]) -> tuple:
    """
    Extract owner, repo, and PR number from PR data.
    
    Args:
        pr_data: PR dictionary from T012
        
    Returns:
        Tuple of (owner, repo, pr_number) or (None, None, None) if not found
    """
    # Try different possible field names
    owner = pr_data.get("owner") or pr_data.get("repository_owner")
    repo = pr_data.get("repo") or pr_data.get("repository") or pr_data.get("base", {}).get("repo", {}).get("name")
    pr_number = pr_data.get("number")
    
    # If we have a full_url, try to parse it
    full_url = pr_data.get("url") or pr_data.get("full_url")
    if not owner and full_url:
        # URL format: https://api.github.com/repos/{owner}/{repo}/pulls/{number}
        parts = full_url.split("/")
        if len(parts) >= 6 and parts[3] == "repos":
            owner = parts[4]
            repo = parts[5]
            if len(parts) >= 8 and parts[6] == "pulls":
                try:
                    pr_number = int(parts[7])
                except ValueError:
                    pass
    
    return owner, repo, pr_number

def fetch_human_comments_for_all_prs(prs: List[Dict[str, Any]], token: str) -> List[Dict[str, Any]]:
    """
    Fetch human comments for all PRs.
    
    Args:
        prs: List of PR dictionaries
        token: GitHub API token
        
    Returns:
        List of normalized comment dictionaries
    """
    all_comments = []
    
    for pr_data in prs:
        owner, repo, pr_number = extract_repo_info(pr_data)
        
        if not owner or not repo or not pr_number:
            logger.warning(f"Could not extract repo info from PR data: {pr_data.get('id', 'unknown')}")
            continue
        
        logger.info(f"Fetching comments for {owner}/{repo}#{pr_number}")
        
        # Fetch review comments (inline code comments)
        review_comments = fetch_review_comments_for_pr(owner, repo, pr_number, token)
        for comment in review_comments:
            normalized = normalize_comment(comment, "review")
            normalized["linked_pr_id"] = pr_number
            all_comments.append(normalized)
        
        # Fetch issue comments (top-level discussion)
        issue_comments = fetch_issue_comments_for_pr(owner, repo, pr_number, token)
        for comment in issue_comments:
            normalized = normalize_comment(comment, "issue")
            normalized["linked_pr_id"] = pr_number
            all_comments.append(normalized)
        
        # Rate limit courtesy
        time.sleep(1)
    
    logger.info(f"Total comments fetched: {len(all_comments)}")
    return all_comments

def save_comments(comments: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save comments to JSON file.
    
    Args:
        comments: List of comment dictionaries
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(comments)} comments to {output_path}")

def main():
    """
    Main entry point for fetching human comments.
    """
    # Get configuration
    paths = get_paths()
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        logger.error("GITHUB_TOKEN environment variable not set. Cannot fetch from GitHub API.")
        logger.error("Please set GITHUB_TOKEN with a personal access token that has 'public_repo' scope.")
        return 1
    
    # Ensure output directory exists
    ensure_directories([paths["annotations"]])
    
    # Load existing PRs from T012
    raw_data_dir = Path(paths["raw"])
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        logger.error("Please run T012 (fetch_prs.py) first to populate data/raw/")
        return 1
    
    prs = load_existing_prs(raw_data_dir)
    if not prs:
        logger.error("No PRs found in data/raw/. Please run T012 first.")
        return 1
    
    logger.info(f"Found {len(prs)} PRs to process")
    
    # Fetch comments
    comments = fetch_human_comments_for_all_prs(prs, token)
    
    # Save output
    output_path = Path(paths["annotations"]) / "raw_comments.json"
    save_comments(comments, output_path)
    
    logger.info("Human comment fetching completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())
