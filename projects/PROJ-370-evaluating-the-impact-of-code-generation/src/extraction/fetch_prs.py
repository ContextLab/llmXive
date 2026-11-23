"""
Fetch Pull Requests and associated data from GitHub for target repositories.

This module implements Task T007:
(a) Load target repositories from ``code/config/settings.py``.
(b) Fetch up to ``max_prs`` PRs per repository via the GitHub REST API.
(c) Compute SHA‑256 checksums for each PR payload.
(d) Write the raw PR payloads to ``data/raw/prs.json``.
(e) Write the checksum mapping to ``data/raw/checksums.json``.
"""

import os
import json
import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib import request, error

# Import configuration utilities from the project's settings module
from code.config.settings import (
    get_target_repos,
    get_paths,
    ensure_directories,
    HYPERPARAMS,
)

# Configure logger for this module
logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
RATE_LIMIT_SLEEP = 60  # Seconds to sleep if rate limit hit


def _http_get(url: str, headers: Dict[str, str]) -> bytes:
    """Perform a GET request and return raw bytes."""
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except error.HTTPError as e:
        if e.code == 403:
            # GitHub rate limiting returns 403 with a message containing "rate limit"
            body = e.read().decode()
            if "rate limit" in body.lower():
                logger.warning(f"Rate limit hit for {url}.")
                raise RuntimeError("rate_limit")
            else:
                raise
        else:
            raise


def make_github_request(
    endpoint: str, params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Make a paginated request to the GitHub API.

    Args:
        endpoint: API endpoint (e.g., '/repos/owner/repo/pulls')
        params: Query parameters

    Returns:
        List of items from all pages of the response.

    Raises:
        RuntimeError: If rate limiting is encountered.
        urllib.error.URLError / HTTPError for other failures.
    """
    url = f"{GITHUB_API_BASE}{endpoint}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-research-pipeline",
    }

    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    all_items: List[Dict[str, Any]] = []
    page = 1

    while True:
        query_params = params.copy() if params else {}
        query_params["page"] = page
        query_params["per_page"] = 100

        # Build query string
        if query_params:
            query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
            full_url = f"{url}?{query_string}"
        else:
            full_url = url

        try:
            raw = _http_get(full_url, headers)
            data = json.loads(raw.decode())
        except RuntimeError as rl:
            if str(rl) == "rate_limit":
                logger.warning(
                    f"Rate limit hit. Sleeping for {RATE_LIMIT_SLEEP} seconds."
                )
                time.sleep(RATE_LIMIT_SLEEP)
                continue
            else:
                raise
        except Exception as e:
            logger.error(f"Request failed for {full_url}: {e}")
            raise

        if not isinstance(data, list):
            logger.warning(f"Expected list from {full_url}, got {type(data)}")
            break

        if not data:
            # No more items
            break

        all_items.extend(data)
        page += 1

        # GitHub returns max 100 items per page; if fewer, we are done.
        if len(data) < 100:
            break

        # Polite delay
        time.sleep(1)

    return all_items


def fetch_linked_issues(pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch linked issues for a specific PR by scanning the PR body for
    ``Fixes #123`` / ``Closes #456`` patterns.

    Args:
        pr_data: PR data dictionary containing ``number`` and repository info.

    Returns:
        List of issue objects linked to the PR.
    """
    pr_number = pr_data.get("number")
    repo_full_name = pr_data.get("base", {}).get("repo", {}).get("full_name")
    if not repo_full_name:
        repo_full_name = pr_data.get("repository_url", "").replace(
            "https://api.github.com/repos/", ""
        )
    if not repo_full_name:
        return []

    body = pr_data.get("body", "") or ""
    import re

    # Look for explicit closing keywords followed by an issue number
    pattern = r"(?:Fixes|Closes|Resolves|Related to)\s*#(\d+)"
    matches = re.findall(pattern, body, re.IGNORECASE)

    linked_issues: List[Dict[str, Any]] = []
    for issue_num in matches:
        try:
            issue_endpoint = f"/repos/{repo_full_name}/issues/{issue_num}"
            issue_data = make_github_request(issue_endpoint)
            if issue_data:
                linked_issues.append(
                    {
                        "issue_number": int(issue_num),
                        "title": issue_data.get("title"),
                        "state": issue_data.get("state"),
                        "url": issue_data.get("html_url"),
                        "labels": [
                            l.get("name") for l in issue_data.get("labels", [])
                        ],
                    }
                )
        except Exception as e:
            logger.warning(
                f"Failed to fetch issue #{issue_num} for PR #{pr_number}: {e}"
            )
    return linked_issues


def fetch_prs_for_repo(
    owner: str, repo: str, max_prs: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch PRs for a specific repository and enrich each with linked issues.

    Args:
        owner: Repository owner.
        repo: Repository name.
        max_prs: Maximum number of PRs to fetch (None means all).

    Returns:
        List of enriched PR dictionaries.
    """
    logger.info(f"Fetching PRs for {owner}/{repo}...")

    endpoint = f"/repos/{owner}/{repo}/pulls"
    params = {"state": "all"}  # Fetch both open and closed PRs

    prs = make_github_request(endpoint, params)

    if max_prs is not None:
        prs = prs[:max_prs]

    enriched_prs: List[Dict[str, Any]] = []
    for pr in prs:
        pr_number = pr.get("number")
        logger.debug(f"Processing PR #{pr_number}")

        linked_issues = fetch_linked_issues(pr)

        enriched_pr = {
            "pr_id": pr.get("id"),
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
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        }

        if not linked_issues:
            logger.debug(f"PR #{pr_number} has no linked issues found.")

        enriched_prs.append(enriched_pr)

    logger.info(f"Fetched {len(enriched_prs)} PRs for {owner}/{repo}.")
    return enriched_prs


def _write_json(path: Path, data: Any) -> None:
    """Helper to write JSON data with UTF‑8 encoding and pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def main() -> None:
    """
    Main entry point for Task T007.
    1. Load target repositories from ``code/config/settings.py``.
    2. Fetch up to ``max_prs`` PRs per repository.
    3. Write the raw PR payloads to ``data/raw/prs.json``.
    4. Compute SHA‑256 checksums for each PR and write them to ``data/raw/checksums.json``.
    """
    # Configure basic logging (if not already configured by a parent script)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # (a) Load and validate target repositories
        target_repos = get_target_repos()
        if not target_repos:
            logger.error("No target repositories found in configuration.")
            return

        logger.info(f"Target repositories: {target_repos}")

        # (b) Determine maximum PRs per repository from hyper‑parameters
        max_prs = HYPERPARAMS.get("max_prs", 500)

        # Ensure output directories exist
        paths = get_paths()
        raw_dir = Path(paths["data_raw"])
        ensure_directories()

        all_prs: List[Dict[str, Any]] = []
        fetch_errors: List[Dict[str, str]] = []

        for repo_str in target_repos:
            if "/" not in repo_str:
                logger.warning(f"Invalid repo format '{repo_str}', skipping.")
                continue

            owner, repo = repo_str.split("/", 1)
            try:
                prs = fetch_prs_for_repo(owner, repo, max_prs=max_prs)
                all_prs.extend(prs)
            except Exception as e:
                logger.error(f"Failed to fetch PRs for {repo_str}: {e}")
                fetch_errors.append({"repo": repo_str, "error": str(e)})

        if not all_prs:
            logger.warning("No PRs fetched. Creating empty output files.")
            _write_json(raw_dir / "prs.json", [])
            _write_json(raw_dir / "checksums.json", {})
            return

        # (c) Write raw PR data to a deterministic filename
        prs_path = raw_dir / "prs.json"
        _write_json(prs_path, all_prs)
        logger.info(f"Saved {len(all_prs)} PRs to {prs_path}")

        # (d) Compute SHA‑256 checksums for each PR
        checksums: Dict[str, str] = {}
        for pr in all_prs:
            # Use ``pr_id`` if present, otherwise fall back to ``pr_number``
            pr_key = str(pr.get("pr_id") or pr.get("pr_number"))
            pr_json = json.dumps(pr, sort_keys=True).encode("utf-8")
            checksum = hashlib.sha256(pr_json).hexdigest()
            checksums[pr_key] = checksum

        checksums_path = raw_dir / "checksums.json"
        _write_json(checksums_path, checksums)
        logger.info(f"Wrote checksums for {len(checksums)} PRs to {checksums_path}")

        # (e) Log any fetch errors
        if fetch_errors:
            error_path = raw_dir / "fetch_errors.json"
            _write_json(error_path, fetch_errors)
            logger.warning(
                f"Encountered errors for {len(fetch_errors)} repositories; details in {error_path}"
            )

    except Exception as e:
        logger.critical(f"Fatal error in fetch_prs pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
