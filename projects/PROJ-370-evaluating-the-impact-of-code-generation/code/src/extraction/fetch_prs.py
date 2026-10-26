"""
Fetch Pull Requests and associated data from GitHub for target repositories.

This module implements Task T007:
(a) Load target repositories from ``code/src/config/settings.py``.
(b) Fetch up to ``max_prs`` PRs per repository via the GitHub REST API.
(c) For each PR also fetch the diff, review comments and issue comments.
(d) Compute SHA-256 checksums for each PR payload file.
(e) Write the enriched raw PR payloads as individual JSON files to ``data/raw/``.
(f) Write the checksum mapping to ``data/raw/checksums.json``.
(g) Provide a small CLI supporting ``--repos``, ``--max-prs`` and ``--test-set``.
"""

import argparse
import json
import logging
import time
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Standard library HTTP utilities
from urllib import request as urllib_request
from urllib import error as urllib_error

# Configuration and toolkit utilities
from llmxive_toolkit import paths, get_logger
from code.src.config.settings import (
    get_target_repos,
    ensure_directories,
    HYPERPARAMS,
)

log = get_logger(__name__)
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
            body = e.read().decode()
            if "rate limit" in body.lower():
                logger.warning(f"Rate limit hit for {url}.")
                raise RuntimeError("rate_limit")
            else:
                raise
        elif e.code == 429:
            logger.warning(f"Too Many Requests (429) for {url}.")
            raise RuntimeError("rate_limit")
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

        query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
        full_url = f"{url}?{query_string}"

        try:
            raw = _http_get(full_url, headers)
            data = json.loads(raw.decode())
        except RuntimeError as rl:
            if str(rl) == "rate_limit":
                logger.warning(f"Rate limit hit. Sleeping for {RATE_LIMIT_SLEEP}s.")
                time.sleep(RATE_LIMIT_SLEEP)
                continue
            else:
                raise
        except Exception as e:
            logger.error(f"Request failed for {full_url}: {e}")
            break

        if not isinstance(data, list):
            break
        if not data:
            break

        all_items.extend(data)
        page += 1
        if len(data) < 100:
            break
        time.sleep(0.5)

    return all_items

# ----------------------------------------------------------------------
# Data-fetching helpers specific to a PR
# ----------------------------------------------------------------------
def _fetch_diff(diff_url: str) -> str:
    """Download the raw diff text for a PR."""
    try:
        # Use specific header for diffs
        headers = {"Accept": "application/vnd.github.v3.diff", "User-Agent": "llmXive-research-pipeline"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        
        req = urllib_request.Request(diff_url, headers=headers, method="GET")
        with urllib_request.urlopen(req, timeout=30) as resp:
            return resp.read().decode(errors="replace")
    except Exception as e:
        logger.warning(f"Could not fetch diff from {diff_url}: {e}")
        return ""

def _fetch_review_comments(owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    """Fetch inline review comments for a PR."""
    endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    return make_github_request(endpoint)

def _fetch_issue_comments(owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    """Fetch top-level issue comments for a PR."""
    endpoint = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
    return make_github_request(endpoint)

def fetch_linked_issues(pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scan PR body for linked issues and retrieve minimal metadata."""
    body = pr_data.get("body") or ""
    pattern = r"(?:Fixes|Closes|Resolves|Related to)\s*#(\d+)"
    matches = re.findall(pattern, body, re.IGNORECASE)
    
    repo_full_name = pr_data.get("repo_full_name")
    if not repo_full_name:
        return []

    linked_issues: List[Dict[str, Any]] = []
    for issue_num in matches[:5]: # Limit to 5 to avoid timeout
        try:
            issue_endpoint = f"/repos/{repo_full_name}/issues/{issue_num}"
            # make_github_request returns a list, but this endpoint returns a dict
            # We need a custom call for single items
            headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "llmXive-research-pipeline"}
            token = os.getenv("GITHUB_TOKEN")
            if token: headers["Authorization"] = f"token {token}"
            
            req = urllib_request.Request(f"{GITHUB_API_BASE}{issue_endpoint}", headers=headers)
            with urllib_request.urlopen(req, timeout=10) as resp:
                issue_data = json.loads(resp.read().decode())
                linked_issues.append({
                    "issue_number": int(issue_num),
                    "title": issue_data.get("title"),
                    "state": issue_data.get("state"),
                    "url": issue_data.get("html_url"),
                    "labels": [l.get("name") for l in issue_data.get("labels", [])],
                })
        except Exception as e:
            logger.warning(f"Failed to fetch issue #{issue_num}: {e}")
    return linked_issues

def fetch_prs_for_repo(
    owner: str,
    repo: str,
    max_prs: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Fetch PRs for a repository and enrich them."""
    logger.info(f"Fetching PRs for {owner}/{repo}...")
    endpoint = f"/repos/{owner}/{repo}/pulls"
    params = {"state": "all"}
    prs = make_github_request(endpoint, params)

    if max_prs is not None:
        prs = prs[:max_prs]

    enriched: List[Dict[str, Any]] = []
    for pr in prs:
        pr_number = pr.get("number")
        repo_full_name = f"{owner}/{repo}"
        
        linked_issues = fetch_linked_issues(pr)
        
        enriched_pr: Dict[str, Any] = {
            "pr_id": pr.get("id"),
            "pr_number": pr_number,
            "owner": owner,
            "repo": repo,
            "repo_full_name": repo_full_name,
            "title": pr.get("title"),
            "state": pr.get("state"),
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "merged_at": pr.get("merged_at"),
            "user": pr.get("user", {}).get("login"),
            "body": pr.get("body"),
            "html_url": pr.get("html_url"),
            "diff_url": pr.get("diff_url"),
            "linked_issues": linked_issues,
            "linked_issue_ids": [i["issue_number"] for i in linked_issues],
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        }

        # Enrich with diff and comments
        enriched_pr["diff"] = _fetch_diff(pr.get("diff_url", ""))
        
        review_comments = _fetch_review_comments(owner, repo, pr_number)
        issue_comments = _fetch_issue_comments(owner, repo, pr_number)
        enriched_pr["human_review_comments"] = [c.get("body", "") for c in review_comments]
        enriched_pr["human_review_comments"] += [c.get("body", "") for c in issue_comments]

        enriched.append(enriched_pr)
        time.sleep(0.2) # Polite delay

    return enriched

# ----------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------
def run_fetch_prs(
    target_repos: Optional[List[str]] = None,
    max_prs: Optional[int] = None,
    test_set: Optional[int] = None,
) -> None:
    """Core orchestration for fetching PRs and writing artifacts."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    repos = target_repos if target_repos is not None else get_target_repos()
    if not repos:
        log.error("No target repositories found.")
        return

    effective_max = test_set if test_set is not None else (max_prs or HYPERPARAMS.get("max_prs", 500))
    ensure_directories()
    raw_dir = paths.data("raw")

    all_prs_count = 0
    for repo_str in repos:
        if "/" not in repo_str: continue
        owner, repo = repo_str.split("/", 1)
        try:
            prs = fetch_prs_for_repo(owner, repo, max_prs=effective_max)
            for pr in prs:
                pr_id = pr.get("pr_id") or pr.get("pr_number")
                file_path = raw_dir / f"pr_{pr_id}.json"
                with file_path.open("w", encoding="utf-8") as f:
                    json.dump(pr, f, indent=2, ensure_ascii=False)
                all_prs_count += 1
        except Exception as e:
            logger.error(f"Failed to fetch {repo_str}: {e}")

    # Generate Checksums
    checksums = {}
    for file in raw_dir.glob("*.json"):
        if file.name == "checksums.json": continue
        checksums[file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
    
    checksums_path = raw_dir / "checksums.json"
    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, ensure_ascii=False)
    
    log.info(f"Successfully fetched {all_prs_count} PRs. Checksums written to {checksums_path}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch PR data from GitHub.")
    parser.add_argument("--repos", nargs="+", help="Override target repos.")
    parser.add_argument("--max-prs", type=int, help="Max PRs per repo.")
    parser.add_argument("--test-set", type=int, help="Small test set size.")
    args = parser.parse_args()
    run_fetch_prs(target_repos=args.repos, max_prs=args.max_prs, test_set=args.test_set)

if __name__ == "__main__":
    main()