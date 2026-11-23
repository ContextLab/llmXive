import os
import csv
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from github import Github, GithubException, RateLimitExceededException
from dotenv import load_dotenv
from llmxive_toolkit import paths, get_logger

load_dotenv()
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# Target number of repositories to collect
DEFAULT_TARGET_REPO_COUNT = 50
TARGET_REPO_COUNT = int(os.getenv("TARGET_REPO_COUNT", DEFAULT_TARGET_REPO_COUNT))

# Rate-limit handling
MIN_REMAINING_REQUESTS = 5
SLEEP_BUFFER_SECONDS = 10

# File Paths using llmxive_toolkit
REPO_LIST_CSV = paths.raw("repo_list.csv")
REPO_METADATA_CSV = paths.raw("repo_metadata.csv")
CLONES_DIR = paths.data("raw", "clones")

def setup_output_directories() -> None:
    """Ensure all required output directories exist."""
    CLONES_DIR.mkdir(parents=True, exist_ok=True)
    # Other directories are handled by llmxive_toolkit.paths

def calculate_total_loc(repo_path: Path) -> int:
    """Calculate total lines of code for .py and .js files."""
    total_loc = 0
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(('.py', '.js')):
                try:
                    with open(Path(root) / file, 'r', encoding='utf-8', errors='ignore') as f:
                        total_loc += sum(1 for _ in f)
                except Exception:
                    continue
    return total_loc

def _handle_rate_limit(github_client: Github) -> None:
    """Check rate limit and sleep if necessary."""
    try:
        core_limits = github_client.get_rate_limit().core
        remaining = core_limits.remaining
        reset_timestamp = core_limits.reset.timestamp()
        now_timestamp = datetime.now(timezone.utc).timestamp()
        seconds_to_reset = max(0, reset_timestamp - now_timestamp)

        if remaining <= MIN_REMAINING_REQUESTS:
            sleep_time = seconds_to_reset + SLEEP_BUFFER_SECONDS
            log.info(f"Rate limit low ({remaining}). Sleeping for {int(sleep_time)}s.")
            time.sleep(sleep_time)
    except Exception as e:
        log.warning(f"Could not fetch rate limit: {e}")

def curate_repositories() -> None:
    """
    FR-001: Identify and clone active Python/JS repositories.
    Filters: topic:llm-generated OR topic:copilot, stars >= 5, >= 1 commit in last 90 days.
    """
    token = os.getenv("GITHUB_TOKEN")
    if token:
        g = Github(token, per_page=50)
        log.info("Using authenticated GitHub client.")
    else:
        g = Github(per_page=30)
        log.warning("GITHUB_TOKEN not found; using unauthenticated client (highly rate-limited).")

    repos_found: List[Dict[str, Any]] = []
    ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)

    # Search strategies in order of priority
    queries = [
        'topic:llm-generated',
        'topic:copilot',
        '"LLM generated code"',
        '"Copilot generated"',
        'language:python stars:>100'  # Final fallback to ensure some data
    ]

    for query in queries:
        if len(repos_found) >= TARGET_REPO_COUNT:
            break

        log.info(f"Searching with query: {query}")
        try:
            _handle_rate_limit(g)
            results = g.search_repositories(query=query)
            for repo in results:
                if len(repos_found) >= TARGET_REPO_COUNT:
                    break

                # Activity and Popularity Filters
                if (
                    repo.stargazers_count >= 5
                    and repo.pushed_at
                    and repo.pushed_at.replace(tzinfo=timezone.utc) >= ninety_days_ago
                ):
                    if not any(r["repo_id"] == repo.id for r in repos_found):
                        repos_found.append({
                            "repo_id": repo.id,
                            "owner": repo.owner.login,
                            "name": repo.name,
                            "url": repo.clone_url,
                            "stargazers_count": repo.stargazers_count,
                            "created_at": repo.created_at.isoformat(),
                            "updated_at": repo.updated_at.isoformat(),
                        })
        except RateLimitExceededException:
            log.warning("Rate limit exceeded. Sleeping...")
            _handle_rate_limit(g)
        except GithubException as e:
            log.error(f"GitHub API error for '{query}': {e}")

    log.info(f"Identified {len(repos_found)} repositories (target {TARGET_REPO_COUNT}).")

    # Write repo_list.csv with required columns: repo_id,clone_path,clone_status
    with open(REPO_LIST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["repo_id", "clone_path", "clone_status"])
        writer.writeheader()
        for r in repos_found:
            clone_path = CLONES_DIR / f"{r['owner']}_{r['name']}"
            # We will fill clone_status after attempting the clone
            writer.writerow({
                "repo_id": r["repo_id"],
                "clone_path": str(clone_path),
                "clone_status": "pending"
            })

    # Clone repositories and collect metadata
    final_metadata = []
    # Re-open the CSV to update clone_status after cloning
    rows_to_update: List[Dict[str, Any]] = []

    with open(REPO_LIST_CSV, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows_to_update = [row for row in reader]

    for repo in repos_found:
        target_path = CLONES_DIR / f"{repo['owner']}_{repo['name']}"
        clone_status = "failed"
        loc = 0
        try:
            log.info(f"Cloning {repo['url']} into {target_path}...")
            subprocess.run(
                ["git", "clone", "--depth", "100", repo["url"], str(target_path)],
                check=True, capture_output=True, text=True, timeout=120
            )
            clone_status = "success"
            loc = calculate_total_loc(target_path)
        except Exception as e:
            log.error(f"Failed to clone {repo['url']}: {e}")
            clone_status = "failed"
            loc = 0

        # Update the corresponding row in rows_to_update
        for row in rows_to_update:
            if int(row["repo_id"]) == repo["repo_id"]:
                row["clone_status"] = clone_status
                break

        final_metadata.append({
            "repo_id": repo["repo_id"],
            "stars": repo["stargazers_count"],
            "created_at": repo["created_at"],
            "updated_at": repo["updated_at"],
            "total_loc": loc,
        })

    # Write back updated repo_list.csv
    with open(REPO_LIST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["repo_id", "clone_path", "clone_status"])
        writer.writeheader()
        for row in rows_to_update:
            writer.writerow(row)

    # Write repo_metadata.csv with required columns
    with open(REPO_METADATA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["repo_id", "stars", "created_at", "updated_at", "total_loc"])
        writer.writeheader()
        for meta in final_metadata:
            writer.writerow(meta)

    log.info(f"Curation complete. List: {REPO_LIST_CSV}, Metadata: {REPO_METADATA_CSV}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--curate", action="store_true", default=True,
                        help="Run the repository curation step")
    args = parser.parse_args()

    if args.curate:
        setup_output_directories()
        curate_repositories()

if __name__ == "__main__":
    main()
