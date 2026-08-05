"""
code/02_human_baseline.py

Implements the Human Review Baseline for User Story 2.
Fetches merged PR review comments from GitHub repositories collected in Phase 3 (US1).
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to resolve imports relative to code/
# This script is intended to be run from the project root: python code/02_human_baseline.py
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.github_client import create_client, GitHubRateLimitExceeded
from utils.config import get_data_raw_dir, get_data_processed_dir, get_github_token

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_acquired_repos() -> List[Dict[str, Any]]:
    """
    Loads the list of repositories that were successfully acquired and processed
    in the previous phase (T019 output).
    """
    raw_dir = get_data_raw_dir()
    manifest_path = Path(raw_dir) / "repos_manifest.json"
    
    if not manifest_path.exists():
        logger.error(f"Acquisition manifest not found at {manifest_path}. "
                     "Please ensure T019 (01_data_acquisition.py) has run successfully.")
        sys.exit(1)
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Expected schema: {"repos": [{"owner": "...", "name": "...", "full_name": "...", ...}, ...]}
    return data.get("repos", [])

def fetch_pr_review_comments(github_client, owner: str, repo_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetches review comments from merged Pull Requests for a specific repository.
    
    Strategy:
    1. Query the GitHub API for merged PRs in the repo.
    2. For each PR, fetch the associated review comments.
    3. Collect comments that are likely defect annotations.
    
    Note: Uses the GitHub REST API via the existing github_client.
    """
    comments = []
    pr_count = 0
    
    # Endpoint: /repos/{owner}/{repo}/pulls?state=closed&merged=true
    # We need to handle pagination manually or use the generator if available.
    # The github_client provides a generic request method or specific helpers.
    # Assuming we use the raw request method with pagination handling.
    
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
    params = {
        "state": "closed",
        "per_page": 100,
        "sort": "updated",
        "direction": "desc"
    }
    
    page = 1
    while True:
        params["page"] = page
        try:
            response = github_client.request("GET", url, params=params)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch PRs for {owner}/{repo_name}: {response.status_code}")
                break
            
            prs = response.json()
            if not prs:
                break
            
            for pr in prs:
                # Only process merged PRs
                if not pr.get("merged_at"):
                    continue
                
                pr_count += 1
                pr_number = pr.get("number")
                
                # Fetch comments for this PR
                comments_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/comments"
                # Note: This endpoint fetches "review comments" (inline), not the PR body or general review events.
                # We might also need /repos/{owner}/{repo}/pulls/{pr_number}/reviews for the actual review objects.
                # The task asks for "merged PR review comments". We will fetch both inline comments and review bodies.
                
                # 1. Inline comments
                inline_params = {"per_page": 100}
                page_comment = 1
                while True:
                    inline_params["page"] = page_comment
                    try:
                        resp_comments = github_client.request("GET", comments_url, params=inline_params)
                        if resp_comments.status_code != 200:
                            break
                        cmts = resp_comments.json()
                        if not cmts:
                            break
                        for cmt in cmts:
                            comments.append({
                                "source": "inline_comment",
                                "owner": owner,
                                "repo": repo_name,
                                "pr_number": pr_number,
                                "pr_url": pr.get("html_url"),
                                "comment_id": cmt.get("id"),
                                "body": cmt.get("body", ""),
                                "path": cmt.get("path"),
                                "line": cmt.get("line"),
                                "position": cmt.get("position"),
                                "created_at": cmt.get("created_at"),
                                "user": cmt.get("user", {}).get("login", "unknown")
                            })
                        page_comment += 1
                    except Exception as e:
                        logger.warning(f"Error fetching inline comments for PR {pr_number}: {e}")
                        break

                # 2. Review objects (which contain a body)
                reviews_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/reviews"
                page_review = 1
                while True:
                    page_review_params = {"per_page": 100}
                    page_review_params["page"] = page_review
                    try:
                        resp_reviews = github_client.request("GET", reviews_url, params=page_review_params)
                        if resp_reviews.status_code != 200:
                            break
                        revs = resp_reviews.json()
                        if not revs:
                            break
                        for rev in revs:
                            body = rev.get("body")
                            if body: # Only collect if there is actual text
                                comments.append({
                                    "source": "review_body",
                                    "owner": owner,
                                    "repo": repo_name,
                                    "pr_number": pr_number,
                                    "pr_url": pr.get("html_url"),
                                    "review_id": rev.get("id"),
                                    "state": rev.get("state"),
                                    "body": body,
                                    "created_at": rev.get("submitted_at"),
                                    "user": rev.get("user", {}).get("login", "unknown")
                                })
                        page_review += 1
                    except Exception as e:
                        logger.warning(f"Error fetching reviews for PR {pr_number}: {e}")
                        break

            if limit and len(comments) >= limit:
                break
            
            page += 1
        except GitHubRateLimitExceeded:
            logger.error("GitHub Rate Limit exceeded. Stopping fetch.")
            break
        except Exception as e:
            logger.error(f"Unexpected error fetching PRs for {owner}/{repo_name}: {e}")
            break
    
    logger.info(f"Fetched {len(comments)} comments from {pr_count} merged PRs for {owner}/{repo_name}")
    return comments

def main():
    """
    Main entry point for T022.
    1. Loads acquired repos.
    2. Initializes GitHub Client.
    3. Iterates through repos to fetch review comments.
    4. Aggregates and saves to data/processed/heuristic_candidates.json (intermediate step for T023).
    """
    logger.info("Starting T022: Fetching merged PR review comments")
    
    repos = load_acquired_repos()
    if not repos:
        logger.error("No repositories found in acquisition manifest.")
        sys.exit(1)
    
    token = get_github_token()
    if not token:
        logger.error("GitHub token not found. Please set GITHUB_TOKEN in .env")
        sys.exit(1)
    
    client = create_client(token)
    
    all_comments = []
    processed_count = 0
    
    for repo in repos:
        owner = repo.get("owner")
        name = repo.get("name")
        if not owner or not name:
            logger.warning(f"Skipping repo entry with missing owner/name: {repo}")
            continue
        
        logger.info(f"Processing {owner}/{name}...")
        try:
            comments = fetch_pr_review_comments(client, owner, name)
            all_comments.extend(comments)
            processed_count += 1
        except Exception as e:
            logger.error(f"Failed to process {owner}/{name}: {e}")
            continue
    
    if not all_comments:
        logger.warning("No comments were collected. Check if repos have PRs or API access.")
    
    # Save the raw collected data. This serves as the input for T023 (heuristics).
    # We save it as 'heuristic_candidates.json' because T023 will filter this list.
    processed_dir = get_data_processed_dir()
    output_path = Path(processed_dir) / "heuristic_candidates.json"
    
    os.makedirs(output_path.parent, exist_ok=True)
    
    output_data = {
        "metadata": {
            "source": "T022_GitHub_API_Fetch",
            "total_comments": len(all_comments),
            "repos_processed": processed_count,
            "total_repos_in_manifest": len(repos)
        },
        "comments": all_comments
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Successfully saved {len(all_comments)} comments to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
