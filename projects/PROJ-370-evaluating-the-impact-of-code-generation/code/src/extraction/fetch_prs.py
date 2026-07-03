"""
Fetch Pull Requests from GitHub for target repositories.

This script implements Task T012:
(a) load and validate the list of 3-5 target repos from config/settings.py (FR-001),
(b) fetch PRs using GitHub API,
(c) handle missing linked issues (empty list),
(d) log unverified issues.
Output raw JSON to data/raw/.
"""
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Import project configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config.settings import (
    TARGET_REPOS,
    GITHUB_API_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    DATA_RAW_DIR,
    LOGS_DIR,
    PROJECT_ROOT
)
from code.src.utils.logger import get_logger, setup_pipeline_logging
from code.src.extraction.schema import PullRequest, BugDetection, Severity

# Setup logging
setup_pipeline_logging()
logger = get_logger(__name__)

def make_github_request(url: str, token: Optional[str] = None) -> Optional[Dict]:
    """
    Make a request to the GitHub API with retry logic.
    Returns parsed JSON or None on failure.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-Research-Agent"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    retries = 0
    while retries < MAX_RETRIES:
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=GITHUB_API_TIMEOUT) as response:
                return json.loads(response.read().decode('utf-8'))
        except HTTPError as e:
            if e.code == 403 and 'rate limit' in str(e).lower():
                logger.warning(f"Rate limit hit. Waiting {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                retries += 1
            else:
                logger.error(f"HTTP Error {e.code} for {url}: {e}")
                return None
        except URLError as e:
            logger.error(f"URL Error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None

    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} retries.")
    return None

def fetch_prs_for_repo(repo: str) -> List[PullRequest]:
    """
    Fetch PRs for a single repository.
    Returns a list of PullRequest objects.
    """
    owner, repo_name = repo.split('/')
    prs_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls?state=all&per_page=100"
    
    logger.info(f"Fetching PRs for {repo}...")
    data = make_github_request(prs_url)
    
    if not data:
        logger.warning(f"No data returned for {repo}. Skipping.")
        return []

    prs = []
    for item in data:
        pr_id = item['number']
        title = item['title']
        state = item['state']
        created_at = item['created_at']
        updated_at = item['updated_at']
        html_url = item['html_url']
        user_login = item['user']['login'] if item.get('user') else "unknown"
        
        # Fetch diff
        diff_url = item['url'] + '/diff'
        diff_content = ""
        try:
            req = Request(diff_url, headers={"Accept": "application/vnd.github.v3.diff"})
            with urlopen(req, timeout=GITHUB_API_TIMEOUT) as response:
                diff_content = response.read().decode('utf-8')
        except Exception as e:
            logger.warning(f"Could not fetch diff for PR #{pr_id}: {e}")

        # Fetch linked issues
        # Issues are linked via comments or body text mentioning #issue_number
        linked_issue_ids = []
        unverified_issues = []
        
        # Check PR body
        body = item.get('body', '') or ''
        import re
        issue_pattern = r'#(\d+)'
        found_issues = re.findall(issue_pattern, body)
        
        # Check comments for issue references
        comments_url = item['comments_url']
        comments_data = make_github_request(comments_url)
        if comments_data:
            for comment in comments_data:
                comment_body = comment.get('body', '') or ''
                comment_issues = re.findall(issue_pattern, comment_body)
                found_issues.extend(comment_issues)
        
        # Deduplicate and convert to int
        unique_issues = list(set([int(x) for x in found_issues]))
        
        # Validate issues (check if they exist) - for this task we log them as "reported"
        # but do not verify them as ground truth yet (FR-011)
        for issue_id in unique_issues:
            # We assume they are reported but unverified for now
            linked_issue_ids.append(issue_id)
            # In a real scenario, we might check issue status here
            # For T012, we just log that we found them
            logger.debug(f"Found linked issue #{issue_id} in PR #{pr_id}")

        # Create PullRequest object
        pr = PullRequest(
            pr_id=pr_id,
            repo=repo,
            title=title,
            state=state,
            created_at=created_at,
            updated_at=updated_at,
            html_url=html_url,
            author=user_login,
            diff=diff_content,
            linked_issue_ids=linked_issue_ids,
            is_verified=False  # Not verified until T017
        )
        prs.append(pr)

    return prs

def main():
    """
    Main entry point for fetching PRs.
    """
    logger.info("Starting PR extraction pipeline (T012).")
    
    # Validate target repos
    if not TARGET_REPOS:
        logger.error("No target repositories configured in settings.py")
        return 1

    if len(TARGET_REPOS) < 3 or len(TARGET_REPOS) > 5:
        logger.warning(f"Number of target repos ({len(TARGET_REPOS)}) is outside recommended range (3-5).")

    all_prs = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for repo in TARGET_REPOS:
        logger.info(f"Processing repository: {repo}")
        try:
            repo_prs = fetch_prs_for_repo(repo)
            all_prs.extend(repo_prs)
            logger.info(f"Fetched {len(repo_prs)} PRs from {repo}.")
        except Exception as e:
            logger.error(f"Error processing {repo}: {e}")
            continue

    if not all_prs:
        logger.warning("No PRs fetched. Exiting.")
        return 0

    # Save raw JSON
    output_path = DATA_RAW_DIR / f"raw_prs_{timestamp}.json"
    
    # Convert to dict for JSON serialization
    prs_dict = [asdict(pr) for pr in all_prs]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(prs_dict, f, indent=2, default=str)

    logger.info(f"Successfully saved {len(all_prs)} PRs to {output_path}")
    
    # Summary log
    repos_summary = {}
    for pr in all_prs:
        if pr.repo not in repos_summary:
            repos_summary[pr.repo] = 0
        repos_summary[pr.repo] += 1
    
    logger.info("PRs fetched per repo:")
    for repo, count in repos_summary.items():
        logger.info(f"  {repo}: {count}")

    return 0

if __name__ == "__main__":
    exit(main())
