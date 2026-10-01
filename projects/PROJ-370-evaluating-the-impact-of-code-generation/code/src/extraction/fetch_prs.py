"""
Fetch Pull Requests from GitHub for target repositories.

This module implements T012:
(a) Load and validate target repos from config
(b) Fetch PRs using GitHub API
(c) Handle missing linked issues (empty list)
(d) Log unverified issues
(e) Output raw JSON to data/raw/
"""
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import from project API surface
from code.config.settings import get_target_repos, get_paths, ensure_directories
from code.src.utils.logger import get_logger, increment_pr_processed, increment_pr_skipped, increment_errors

# Configure module logger
logger = get_logger(__name__)

# GitHub API rate limit handling
# GitHub API allows 60 unauthenticated requests per hour per IP
# We implement exponential backoff for rate limit errors
MAX_RETRIES = 5
BASE_DELAY = 1.0  # seconds

def make_github_request(url: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """
    Make a request to the GitHub API with rate limit handling.

    Args:
        url: The API endpoint URL
        headers: Optional headers (for authentication)

    Returns:
        JSON response as dict, or None on failure
    """
    import urllib.request
    import urllib.error

    if headers is None:
        headers = {}
        # Add default user-agent (required by GitHub API)
        headers['User-Agent'] = 'llmXive-research-agent'

    retry_count = 0
    last_error = None

    while retry_count < MAX_RETRIES:
        try:
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)

        except urllib.error.HTTPError as e:
            last_error = e
            if e.code == 403 and 'rate limit' in str(e.reason).lower():
                # Rate limited - check for retry-after header
                retry_after = e.headers.get('Retry-After')
                if retry_after:
                    delay = int(retry_after)
                    logger.warning(f"Rate limit exceeded. Waiting {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    # Default exponential backoff
                    delay = BASE_DELAY * (2 ** retry_count)
                    logger.warning(f"Rate limit exceeded. Waiting {delay} seconds... (retry {retry_count + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                    retry_count += 1
            elif e.code == 404:
                # Resource not found - don't retry
                logger.error(f"Resource not found: {url}")
                return None
            else:
                # Other HTTP error - retry with backoff
                delay = BASE_DELAY * (2 ** retry_count)
                logger.warning(f"HTTP error {e.code}: {e.reason}. Retrying in {delay}s...")
                time.sleep(delay)
                retry_count += 1

        except urllib.error.URLError as e:
            last_error = e
            delay = BASE_DELAY * (2 ** retry_count)
            logger.warning(f"Network error: {e.reason}. Retrying in {delay}s...")
            time.sleep(delay)
            retry_count += 1

        except Exception as e:
            last_error = e
            delay = BASE_DELAY * (2 ** retry_count)
            logger.warning(f"Unexpected error: {str(e)}. Retrying in {delay}s...")
            time.sleep(delay)
            retry_count += 1

    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} retries. Last error: {last_error}")
    return None

def fetch_prs_for_repo(repo_name: str, max_prs: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch pull requests for a specific repository.

    Args:
        repo_name: Repository name in format 'owner/repo'
        max_prs: Maximum number of PRs to fetch

    Returns:
        List of PR data dictionaries
    """
    # GitHub API endpoint for PRs
    base_url = f"https://api.github.com/repos/{repo_name}/pulls"
    headers = {}
    headers['User-Agent'] = 'llmXive-research-agent'

    # Check for GitHub token in environment
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'

    all_prs = []
    page = 1
    per_page = 100  # GitHub API max per page

    logger.info(f"Fetching PRs for {repo_name}...")

    while len(all_prs) < max_prs:
        url = f"{base_url}?state=all&per_page={per_page}&page={page}"
        logger.debug(f"Fetching page {page} from {url}")

        response = make_github_request(url, headers)

        if response is None:
            logger.error(f"Failed to fetch page {page} for {repo_name}")
            break

        if len(response) == 0:
            # No more PRs
            break

        for pr in response:
            if len(all_prs) >= max_prs:
                break

            # Extract relevant PR data
            pr_data = {
                'pr_id': pr['number'],
                'title': pr['title'],
                'state': pr['state'],
                'created_at': pr['created_at'],
                'updated_at': pr['updated_at'],
                'merged_at': pr['merged_at'],
                'user': {
                    'login': pr['user']['login'],
                    'id': pr['user']['id']
                },
                'html_url': pr['html_url'],
                'diff_url': pr['diff_url'],
                'patch_url': pr['patch_url'],
                'body': pr['body'],
                'base': {
                    'ref': pr['base']['ref'],
                    'sha': pr['base']['sha'],
                    'repo': {
                        'full_name': pr['base']['repo']['full_name']
                    }
                },
                'head': {
                    'ref': pr['head']['ref'],
                    'sha': pr['head']['sha'],
                    'repo': {
                        'full_name': pr['head']['repo']['full_name']
                    }
                },
                'linked_issues': [],
                'comments_count': pr['comments'],
                'review_comments_count': pr['review_comments'],
                'commits_count': pr['commits'],
                'additions': pr['additions'],
                'deletions': pr['deletions'],
                'changed_files': pr['changed_files']
            }

            # Fetch linked issues (closes references)
            linked_issues = _fetch_linked_issues(repo_name, pr['number'], headers)
            pr_data['linked_issues'] = linked_issues

            # Fetch diff content
            diff_content = _fetch_diff_content(pr['diff_url'], headers)
            if diff_content:
                pr_data['diff_content'] = diff_content
            else:
                pr_data['diff_content'] = None
                logger.warning(f"Could not fetch diff for PR #{pr['number']} in {repo_name}")

            all_prs.append(pr_data)

        page += 1

        # Rate limit safety - add small delay between pages
        time.sleep(0.5)

    logger.info(f"Fetched {len(all_prs)} PRs for {repo_name}")
    return all_prs

def _fetch_linked_issues(repo_name: str, pr_number: int, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Fetch issues linked to a PR via 'closes' or 'fixes' keywords.

    Args:
        repo_name: Repository name
        pr_number: PR number
        headers: API headers

    Returns:
        List of linked issue dictionaries
    """
    # Fetch PR comments to find issue references
    issues_url = f"https://api.github.com/repos/{repo_name}/issues/{pr_number}/timeline"
    response = make_github_request(issues_url, headers)

    if response is None:
        logger.warning(f"Could not fetch timeline for PR #{pr_number}")
        return []

    linked_issues = []
    seen_issue_ids = set()

    for event in response:
        if event.get('event') in ['cross-referenced', 'closed', 'reopened']:
            # Check if this is an issue reference
            source = event.get('source', {})
            if source.get('issue'):
                issue = source['issue']
                issue_id = issue.get('number')

                if issue_id and issue_id not in seen_issue_ids:
                    seen_issue_ids.add(issue_id)
                    linked_issues.append({
                        'issue_id': issue_id,
                        'title': issue.get('title', ''),
                        'state': issue.get('state', ''),
                        'html_url': issue.get('html_url', ''),
                        'is_verified': False  # Mark as unverified initially
                    })
                    logger.info(f"Found linked issue #{issue_id} for PR #{pr_number}")

    return linked_issues

def _fetch_diff_content(diff_url: str, headers: Dict[str, str]) -> Optional[str]:
    """
    Fetch the raw diff content for a PR.

    Args:
        diff_url: URL to the diff
        headers: API headers

    Returns:
        Diff content as string, or None on failure
    """
    response = make_github_request(diff_url, headers)

    if response is None:
        return None

    # If response is already a string (diff format), return it
    if isinstance(response, str):
        return response

    # If response is dict, try to extract diff content
    if isinstance(response, dict):
        # Sometimes GitHub returns diff as text in raw response
        # But our make_github_request parses JSON, so this shouldn't happen
        return None

    return None

def main():
    """
    Main entry point for fetching PRs from target repositories.

    This function:
    1. Loads target repos from config
    2. Validates repo list (3-5 repos required)
    3. Fetches PRs for each repo
    4. Handles missing linked issues (empty list)
    5. Logs unverified issues
    6. Outputs raw JSON to data/raw/
    """
    logger.info("Starting PR fetch process...")

    # Get configuration
    try:
        target_repos = get_target_repos()
        paths = get_paths()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        increment_errors()
        return

    # Validate target repos (FR-001: 3-5 repos required)
    if not target_repos:
        logger.error("No target repositories found in config/settings.py")
        increment_errors()
        return

    if len(target_repos) < 3 or len(target_repos) > 5:
        logger.warning(f"Expected 3-5 target repos, found {len(target_repos)}. Proceeding with {len(target_repos)} repos.")

    logger.info(f"Target repositories: {target_repos}")

    # Ensure output directory exists
    ensure_directories()
    raw_data_path = Path(paths['data_raw'])

    # Process each repository
    all_prs = []
    repos_processed = 0
    repos_failed = 0

    for repo in target_repos:
        logger.info(f"Processing repository: {repo}")

        try:
            prs = fetch_prs_for_repo(repo)

            if prs:
                all_prs.extend(prs)
                repos_processed += 1

                # Log unverified issues
                for pr in prs:
                    unverified_count = sum(1 for issue in pr.get('linked_issues', []) if not issue.get('is_verified', False))
                    if unverified_count > 0:
                        logger.warning(f"PR #{pr['pr_id']} in {repo} has {unverified_count} unverified linked issues")

                logger.info(f"Successfully fetched {len(prs)} PRs from {repo}")
            else:
                logger.warning(f"No PRs fetched for {repo}")
                repos_failed += 1

        except Exception as e:
            logger.error(f"Failed to fetch PRs for {repo}: {e}")
            increment_errors()
            repos_failed += 1
            continue

    if not all_prs:
        logger.error("No PRs fetched from any repository")
        increment_errors()
        return

    # Add metadata to the output
    output_data = {
        'metadata': {
            'fetched_at': datetime.utcnow().isoformat(),
            'target_repos': target_repos,
            'repos_processed': repos_processed,
            'repos_failed': repos_failed,
            'total_prs': len(all_prs)
        },
        'pull_requests': all_prs
    }

    # Write raw JSON output
    output_file = raw_data_path / f"pr_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully wrote {len(all_prs)} PRs to {output_file}")
        increment_pr_processed(len(all_prs))

    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        increment_errors()
        return

    logger.info(f"PR fetch complete. Processed {repos_processed} repos, failed {repos_failed}. Total PRs: {len(all_prs)}")

if __name__ == '__main__':
    main()