"""
Fetch Pull Requests and associated data from GitHub for target repositories.

This module implements Task T007:
(a) Load target repositories from ``code/config/settings.py``.
(b) Fetch up to ``max_prs`` PRs per repository via the GitHub REST API.
(c) For each PR also fetch the diff, review comments and issue comments.
(d) Compute SHA‑256 checksums for each PR payload.
(e) Write the enriched raw PR payloads to ``data/raw/prs.json``.
(f) Write the checksum mapping to ``data/raw/checksums.json``.
(g) Provide a small CLI supporting ``--repos``, ``--max-prs`` and ``--test-set``.
"""

import argparse
import json
import logging
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Standard library HTTP utilities (avoid external ``requests``)
from urllib import request as urllib_request
from urllib import error as urllib_error

# Configuration utilities
from code.config.settings import (
    get_target_repos,
    get_paths,
    ensure_directories,
    HYPERPARAMS,
)

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
RATE_LIMIT_SLEEP = 60  # seconds to sleep when hitting a rate limit


# ----------------------------------------------------------------------
# Helper functions for HTTP interaction
# ----------------------------------------------------------------------
def _http_get(url: str, headers: Dict[str, str]) -> bytes:
    """Perform a GET request and return raw bytes using ``urllib``."""
    req = urllib_request.Request(url, headers=headers, method="GET")
    try:
        with urllib_request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib_error.HTTPError as e:
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

    Returns a flat list of items from all pages.
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
        query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
        full_url = f"{url}?{query_string}"

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
            break

        all_items.extend(data)
        page += 1

        # GitHub returns max 100 items per page; if fewer, we're done.
        if len(data) < 100:
            break

        # Polite delay between pages
        time.sleep(1)

    return all_items


# ----------------------------------------------------------------------
# Data‑fetching helpers specific to a PR
# ----------------------------------------------------------------------
def _fetch_diff(diff_url: str) -> str:
    """Download the raw diff text for a PR."""
    try:
        raw = _http_get(diff_url, {"Accept": "application/vnd.github.v3.diff"})
        return raw.decode(errors="replace")
    except Exception as e:
        logger.warning(f"Could not fetch diff from {diff_url}: {e}")
        return ""

def _fetch_review_comments(owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    """Fetch inline review comments for a PR."""
    endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    return make_github_request(endpoint)

def _fetch_issue_comments(owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    """Fetch top‑level issue comments for a PR."""
    endpoint = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
    return make_github_request(endpoint)

def fetch_linked_issues(pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scan the PR body for ``Fixes #123`` / ``Closes #456`` patterns
    and retrieve minimal issue metadata.
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
                        "labels": [l.get("name") for l in issue_data.get("labels", [])],
                    }
                )
        except Exception as e:
            logger.warning(
                f"Failed to fetch issue #{issue_num} for PR #{pr_number}: {e}"
            )
    return linked_issues


def fetch_prs_for_repo(
    owner: str,
    repo: str,
    max_prs: Optional[int] = None,
    fetch_extra: bool = True,
) -> List[Dict[str, Any]]:
    """
    Fetch PRs for a repository, enrich each with diff, comments and linked issues.

    Parameters
    ----------
    owner, repo : str
        Repository owner and name.
    max_prs : int or None
        Upper bound on number of PRs to fetch.
    fetch_extra : bool
        If True (default), also fetch diff, review comments and issue comments.
    """
    logger.info(f"Fetching PRs for {owner}/{repo}...")

    endpoint = f"/repos/{owner}/{repo}/pulls"
    params = {"state": "all"}  # include open and closed PRs

    prs = make_github_request(endpoint, params)

    if max_prs is not None:
        prs = prs[:max_prs]

    enriched: List[Dict[str, Any]] = []
    for pr in prs:
        pr_number = pr.get("number")
        logger.debug(f"Processing PR #{pr_number}")

        linked_issues = fetch_linked_issues(pr)

        enriched_pr: Dict[str, Any] = {
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

        # --------------------------------------------------------------
        # Optional extra data (diff + comments) – required for the
        # ``--test-set`` verification mode.
        # --------------------------------------------------------------
        if fetch_extra:
            # Diff
            diff_text = _fetch_diff(pr.get("diff_url", ""))
            enriched_pr["diff"] = diff_text

            # Review comments (inline)
            review_comments = _fetch_review_comments(owner, repo, pr_number)
            enriched_pr["human_review_comments"] = [
                c.get("body", "") for c in review_comments
            ]

            # Issue comments (top‑level discussion)
            issue_comments = _fetch_issue_comments(owner, repo, pr_number)
            enriched_pr["human_review_comments"] += [
                c.get("body", "") for c in issue_comments
            ]

            # Linked issue IDs (just the numeric identifiers)
            enriched_pr["linked_issue_ids"] = [
                issue["issue_number"] for issue in linked_issues
            ]

        enriched.append(enriched_pr)

    logger.info(f"Fetched {len(enriched)} PRs for {owner}/{repo}.")
    return enriched


# ----------------------------------------------------------------------
# JSON writing helper
# ----------------------------------------------------------------------
def _write_json(path: Path, data: Any) -> None:
    """Write ``data`` as pretty‑printed JSON to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def run_fetch_prs(
    target_repos: Optional[List[str]] = None,
    max_prs: Optional[int] = None,
    test_set: Optional[int] = None,
) -> None:
    """
    Core function used by both the library API and the CLI.

    Parameters
    ----------
    target_repos : list of str, optional
        Override the repositories defined in the configuration.
    max_prs : int, optional
        Upper bound per repository (default from ``HYPERPARAMS``).
    test_set : int, optional
        Shortcut for ``max_prs`` when running the quick‑start test.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Resolve configuration
    repos = target_repos if target_repos is not None else get_target_repos()
    if not repos:
        logger.error("No target repositories found in configuration.")
        return

    logger.info(f"Target repositories: {repos}")

    # Determine PR limit
    if test_set is not None:
        effective_max = test_set
    else:
        effective_max = max_prs if max_prs is not None else HYPERPARAMS.get("max_prs", 500)

    # Ensure output directories exist
    paths = get_paths()
    raw_dir = Path(paths["data_raw"])
    ensure_directories()

    all_prs: List[Dict[str, Any]] = []
    fetch_errors: List[Dict[str, str]] = []

    for repo_str in repos:
        if "/" not in repo_str:
            logger.warning(f"Invalid repo format '{repo_str}', skipping.")
            continue
        owner, repo = repo_str.split("/", 1)
        try:
            prs = fetch_prs_for_repo(
                owner,
                repo,
                max_prs=effective_max,
                fetch_extra=True,
            )
            all_prs.extend(prs)
        except Exception as e:
            logger.error(f"Failed to fetch PRs for {repo_str}: {e}")
            fetch_errors.append({"repo": repo_str, "error": str(e)})

    # Write outputs (even if empty)
    prs_path = raw_dir / "prs.json"
    _write_json(prs_path, all_prs)
    logger.info(f"Saved {len(all_prs)} PRs to {prs_path}")

    # Checksums
    checksums: Dict[str, str] = {}
    for pr in all_prs:
        pr_key = str(pr.get("pr_id") or pr.get("pr_number"))
        pr_json = json.dumps(pr, sort_keys=True).encode("utf-8")
        checksums[pr_key] = hashlib.sha256(pr_json).hexdigest()
    checksums_path = raw_dir / "checksums.json"
    _write_json(checksums_path, checksums)
    logger.info(f"Wrote checksums for {len(checksums)} PRs to {checksums_path}")

    # Log any fetch errors
    if fetch_errors:
        error_path = raw_dir / "fetch_errors.json"
        _write_json(error_path, fetch_errors)
        logger.warning(
            f"Encountered errors for {len(fetch_errors)} repositories; details in {error_path}"
        )


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch PR data (with diffs & comments) from GitHub."
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        help="Override list of target repositories (e.g. microsoft/vscode).",
    )
    parser.add_argument(
        "--max-prs",
        type=int,
        help="Maximum number of PRs to fetch per repository.",
    )
    parser.add_argument(
        "--test-set",
        type=int,
        help="Convenient shortcut for a small test set (overrides --max-prs).",
    )
    args = parser.parse_args()

    run_fetch_prs(
        target_repos=args.repos,
        max_prs=args.max_prs,
        test_set=args.test_set,
    )


if __name__ == "__main__":
    main()