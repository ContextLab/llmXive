"""
Fetch Pull Requests and associated data from GitHub for target repositories.

This module implements Task T012:
(a) Load and validate target repos from config/settings.py
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
import requests

from config.settings import get_target_repos, get_paths, ensure_directories

# Configure logger for this module
logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
RATE_LIMIT_SLEEP = 60  # Seconds to sleep if rate limit hit


def make_github_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Make a paginated request to the GitHub API.

    Args:
        endpoint: API endpoint (e.g., '/repos/owner/repo/pulls')
        params: Query parameters

    Returns:
        List of items from all pages of the response.

    Raises:
        requests.exceptions.RequestException: If the request fails after retries.
    """
    url = f"{GITHUB_API_BASE}{endpoint}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-research-pipeline"
    }

    # Add token if available
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    all_items = []
    page = 1

    while True:
        query_params = params.copy() if params else {}
        query_params["page"] = page
        query_params["per_page"] = 100

        try:
            response = requests.get(url, headers=headers, params=query_params, timeout=30)

            if response.status_code == 403:
                if "rate limit" in response.text.lower():
                    logger.warning(f"Rate limit hit. Sleeping for {RATE_LIMIT_SLEEP} seconds.")
                    time.sleep(RATE_LIMIT_SLEEP)
                    continue
                else:
                    logger.error(f"Forbidden access to {url}: {response.text}")
                    raise requests.exceptions.RequestException(f"Forbidden: {response.text}")

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                # Handle single item responses or non-list structures if necessary
                # For pagination endpoints, we expect lists
                logger.warning(f"Expected list from {url}, got {type(data)}")
                break

            if not data:
                # No more items
                break

            all_items.extend(data)
            page += 1

            # GitHub returns 100 items per page max. If we got less, we are done.
            if len(data) < 100:
                break

            # Small delay to be polite
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url} (page {page}): {e}")
            raise

    return all_items


def fetch_linked_issues(pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch linked issues for a specific PR.

    Args:
        pr_data: PR data dictionary containing 'number' and 'repository_url' or owner/repo info.

    Returns:
        List of issue objects linked to the PR.
    """
    # GitHub API does not have a direct "linked issues" endpoint for a PR in the simple sense.
    # We look at the body and comments for mentions like "Fixes #123", "Closes #123", or "Related to #123".
    # However, the task asks to "fetch PRs ... handle missing linked issues".
    # A robust way is to query the issues/PRs comments for the repo and match references.
    # For simplicity and performance in this script, we will attempt to extract issue numbers from the PR body
    # and then fetch the details of those specific issues.
    # If no references are found, return empty list.

    pr_number = pr_data.get("number")
    repo_full_name = pr_data.get("base", {}).get("repo", {}).get("full_name")
    if not repo_full_name:
        # Fallback if structure is different
        repo_full_name = pr_data.get("repository_url", "").replace("https://api.github.com/repos/", "")

    if not repo_full_name:
        return []

    # Extract issue numbers from body
    import re
    body = pr_data.get("body", "") or ""
    # Pattern: Fixes #123, Closes #456, Resolves #789, #123 (loose)
    # We focus on explicit closing keywords to be sure it's a linked issue
    pattern = r'(?:Fixes|Closes|Resolves|Related to)\s*#(\d+)'
    matches = re.findall(pattern, body, re.IGNORECASE)

    linked_issues = []
    for issue_num in matches:
        try:
            # Fetch issue details
            issue_endpoint = f"/repos/{repo_full_name}/issues/{issue_num}"
            issue_data = make_github_request(issue_endpoint)
            if issue_data:
                linked_issues.append({
                    "issue_number": int(issue_num),
                    "title": issue_data.get("title"),
                    "state": issue_data.get("state"),
                    "url": issue_data.get("html_url"),
                    "labels": [l.get("name") for l in issue_data.get("labels", [])]
                })
        except Exception as e:
            logger.warning(f"Failed to fetch issue #{issue_num} for PR #{pr_number}: {e}")

    return linked_issues


def fetch_prs_for_repo(owner: str, repo: str, max_prs: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch PRs for a specific repository.

    Args:
        owner: Repository owner
        repo: Repository name
        max_prs: Maximum number of PRs to fetch (None for all)

    Returns:
        List of PR dictionaries enriched with linked issues.
    """
    logger.info(f"Fetching PRs for {owner}/{repo}...")

    endpoint = f"/repos/{owner}/{repo}/pulls"
    params = {"state": "all"}  # Fetch both open and closed

    prs = make_github_request(endpoint, params)

    if max_prs:
        prs = prs[:max_prs]

    enriched_prs = []
    for pr in prs:
        pr_id = pr.get("id")
        pr_number = pr.get("number")
        logger.debug(f"Processing PR #{pr_number}")

        # Fetch linked issues
        linked_issues = fetch_linked_issues(pr)

        # Check for unverified issues (issues that were mentioned but maybe not found or invalid)
        # In our logic above, we only add if we successfully fetched.
        # If the body mentions an issue but we couldn't fetch it, it's effectively missing/failed.
        # We log a warning for any attempt that failed in fetch_linked_issues.

        # Enrich PR data
        enriched_pr = {
            "pr_id": pr_id,
            "pr_number": pr_number,
            "owner": owner,
            "repo": repo,
            "title": pr.get("title"),
            "state": pr.get("state"),
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "merged_at": pr.get("merged_at"),
            "user": pr.get("user", {}).get("login"),
            "body": pr.get("body"),
            "html_url": pr.get("html_url"),
            "diff_url": pr.get("diff_url"),
            "patch_url": pr.get("patch_url"),
            "linked_issues": linked_issues,
            "fetched_at": datetime.utcnow().isoformat() + "Z"
        }

        # Log if no linked issues found (not an error, just info)
        if not linked_issues:
            logger.debug(f"PR #{pr_number} has no linked issues found.")

        enriched_prs.append(enriched_pr)

    logger.info(f"Fetched {len(enriched_prs)} PRs for {owner}/{repo}.")
    return enriched_prs


def main():
    """
    Main entry point for T012.
    1. Load target repos from config.
    2. Fetch PRs for each repo.
    3. Save raw JSON to data/raw/.
    """
    # Ensure logging is configured (if not already done by parent)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        # (a) Load and validate target repos
        target_repos = get_target_repos()
        if not target_repos:
            logger.error("No target repositories found in config/settings.py.")
            return

        logger.info(f"Target repositories: {target_repos}")

        # Ensure output directory exists
        paths = get_paths()
        raw_dir = paths.get("raw_data")
        ensure_directories()

        all_prs = []
        fetch_errors = []

        for repo_str in target_repos:
            # Parse owner/repo
            if "/" not in repo_str:
                logger.warning(f"Invalid repo format '{repo_str}', skipping.")
                continue

            owner, repo = repo_str.split("/", 1)
            try:
                prs = fetch_prs_for_repo(owner, repo)
                all_prs.extend(prs)
            except Exception as e:
                logger.error(f"Failed to fetch PRs for {repo_str}: {e}")
                fetch_errors.append({"repo": repo_str, "error": str(e)})

        if not all_prs:
            logger.warning("No PRs fetched. Check logs for errors.")
            # Still create an empty file to indicate run completion
            output_path = Path(raw_dir) / "pr_data_raw.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
            return

        # (e) Output raw JSON
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_filename = f"pr_data_raw_{timestamp}.json"
        output_path = Path(raw_dir) / output_filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_prs, f, indent=2, default=str)

        logger.info(f"Successfully saved {len(all_prs)} PRs to {output_path}")

        if fetch_errors:
            error_path = Path(raw_dir) / f"fetch_errors_{timestamp}.json"
            with open(error_path, "w", encoding="utf-8") as f:
                json.dump(fetch_errors, f, indent=2)
            logger.warning(f"Logged {len(fetch_errors)} fetch errors to {error_path}")

    except Exception as e:
        logger.critical(f"Fatal error in fetch_prs pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()