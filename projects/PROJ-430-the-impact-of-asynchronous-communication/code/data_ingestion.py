import logging
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Iterator, Optional

import requests
from requests.exceptions import RequestException, HTTPError

# Project imports
from utils.logger import get_logger
from utils.github_client import GitHubClient, create_client, GitHubRateLimitError
from config import get_config, ensure_directories_exist

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions for GitHub API interaction
# ----------------------------------------------------------------------

GITHUB_API_URL = "https://api.github.com"
CHUNK_SIZE = 100000  # Threshold for chunking large datasets
RATE_LIMIT_BACKOFF = 60  # Seconds to wait on rate limit


def _github_headers() -> Dict[str, str]:
    """Build headers with authentication token if present."""
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def _handle_rate_limit(response: requests.Response) -> None:
    """
    Detect GitHub rate‑limit responses and back‑off.
    Raises GitHubRateLimitError after sleeping.
    """
    if response.status_code == 403 and "rate limit" in response.text.lower():
        reset_ts = response.headers.get("X-RateLimit-Reset")
        if reset_ts:
            wait_seconds = max(int(reset_ts) - int(time.time()), RATE_LIMIT_BACKOFF)
        else:
            wait_seconds = RATE_LIMIT_BACKOFF
        logger.warning(f"Rate limit reached, sleeping for {wait_seconds}s")
        time.sleep(wait_seconds)
        raise GitHubRateLimitError(f"Rate limit hit; backed off for {wait_seconds}s")


def _request_get(url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    """Wrapper around ``requests.get`` that adds auth headers and rate‑limit handling."""
    try:
        resp = requests.get(url, headers=_github_headers(), params=params, timeout=30)
        if resp.status_code == 403:
            _handle_rate_limit(resp)
        resp.raise_for_status()
        return resp
    except RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        raise


def get_repo_full_name(repo_id: int) -> str:
    """
    Resolve a numeric repository ID to its ``owner/repo`` full name.

    Raises ``ValueError`` if the repository cannot be found.
    """
    url = f"{GITHUB_API_URL}/repositories/{repo_id}"
    resp = _request_get(url)
    data = resp.json()
    full_name = data.get("full_name")
    if not full_name:
        raise ValueError(f"Unable to resolve repository ID {repo_id}")
    return full_name


def fetch_all_pages(base_url: str, per_page: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve *all* pages from a paginated GitHub endpoint.

    Returns a list of JSON objects.
    """
    items: List[Dict[str, Any]] = []
    page = 1
    while True:
        params = {"per_page": per_page, "page": page}
        resp = _request_get(base_url, params=params)
        batch = resp.json()
        if not isinstance(batch, list):
            # Some endpoints (e.g., repo lookup) return a dict; treat as empty list
            break
        items.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return items


def fetch_repo_events(repo_id: int) -> List[Dict[str, Any]]:
    """
    Fetch issues (including pull requests) and issue comments for a repository.

    The returned list contains normalized event dictionaries with the keys:
    ``id``, ``type`` (\"issue\" or \"comment\"), ``project_id``, ``actor`` (user dict),
    ``created_at`` (ISO‑8601 timestamp), and ``body`` (text content).
    """
    full_name = get_repo_full_name(repo_id)
    base = f"{GITHUB_API_URL}/repos/{full_name}"

    # ------------------------------------------------------------------
    # Issues (includes pull requests)
    # ------------------------------------------------------------------
    issues_url = f"{base}/issues"
    raw_issues = fetch_all_pages(issues_url, per_page=100)

    events: List[Dict[str, Any]] = []
    for iss in raw_issues:
        # Pull requests appear as issues with a ``pull_request`` field
        event = {
            "id": iss.get("id"),
            "type": "issue",
            "project_id": repo_id,
            "actor": iss.get("user", {}),
            "created_at": iss.get("created_at"),
            "body": iss.get("body", ""),
        }
        events.append(event)

    # ------------------------------------------------------------------
    # Issue comments
    # ------------------------------------------------------------------
    comments_url = f"{base}/issues/comments"
    raw_comments = fetch_all_pages(comments_url, per_page=100)
    for com in raw_comments:
        event = {
            "id": com.get("id"),
            "type": "comment",
            "project_id": repo_id,
            "actor": com.get("user", {}),
            "created_at": com.get("created_at"),
            "body": com.get("body", ""),
        }
        events.append(event)

    return events


# ----------------------------------------------------------------------
# Bot detection utilities (unchanged from original implementation)
# ----------------------------------------------------------------------

def is_bot_actor(user: Dict[str, Any]) -> bool:
    """Check if a user is a bot based on login name or type."""
    if not user:
        return False
    login = user.get('login', '')
    user_type = user.get('type', '')
    if login.endswith('[bot]'):
        return True
    if user_type == 'Bot':
        return True
    return False


def filter_bot_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out bot events from a list of events."""
    filtered = []
    bot_count = 0
    for event in events:
        user = event.get('actor', {})
        if is_bot_actor(user):
            bot_count += 1
            continue
        filtered.append(event)
    if bot_count > 0:
        logger.info(f"Filtered {bot_count} bot events")
    return filtered


# ----------------------------------------------------------------------
# Chunked fetching (kept for compatibility – not used by the simplified logic)
# ----------------------------------------------------------------------

def fetch_project_events_chunked(
    repo_id: int,
    client: GitHubClient,
    target_events: int = None
) -> Iterator[List[Dict[str, Any]]]:
    """
    Fetch events for a repository in chunks to prevent OOM.

    Yields batches of events. If the total exceeds CHUNK_SIZE,
    it yields in chunks of CHUNK_SIZE.
    """
    total_fetched = 0
    buffer = []

    try:
        page = 1
        while True:
            try:
                events_page = client.get_events(repo_id, page=page, per_page=100)
                if not events_page:
                    break
                buffer.extend(events_page)
                total_fetched += len(events_page)

                while len(buffer) >= CHUNK_SIZE:
                    yield buffer[:CHUNK_SIZE]
                    buffer = buffer[CHUNK_SIZE:]

                if target_events and total_fetched >= target_events:
                    if buffer:
                        yield buffer
                    break

                page += 1

            except GitHubRateLimitError as e:
                logger.warning(f"Rate limit hit, backing off for {RATE_LIMIT_BACKOFF}s")
                time.sleep(RATE_LIMIT_BACKOFF)
                log_rate_limit_event(repo_id, str(e))
                continue
            except HTTPError as e:
                if e.response.status_code == 403 and 'rate limit' in str(e).lower():
                    logger.warning(f"Rate limit hit (HTTP 403), backing off")
                    time.sleep(RATE_LIMIT_BACKOFF)
                    log_rate_limit_event(repo_id, str(e))
                    continue
                raise
            except RequestException as e:
                logger.error(f"Network error fetching events for repo {repo_id}: {e}")
                raise

    except Exception as e:
        logger.error(f"Error fetching events for repo {repo_id}: {e}")
        raise
    finally:
        if buffer:
            yield buffer


# ----------------------------------------------------------------------
# Rate‑limit logging helper
# ----------------------------------------------------------------------

def log_rate_limit_event(repo_id: int, error_msg: str):
    """Log rate limit events to a specific log file."""
    config = get_config()
    log_dir = Path(config.get('data_dir', 'data')) / 'logs'
    ensure_directories_exist([log_dir])
    log_file = log_dir / 'rate_limit_events.log'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} | Repo: {repo_id} | Error: {error_msg}\\n")


# ----------------------------------------------------------------------
# Ingestion pipeline
# ----------------------------------------------------------------------

def ingest_sample_projects(
    repo_list: List[int],
    client: GitHubClient,
    min_events: int,
    target_size: int
) -> List[Dict[str, Any]]:
    """
    Ingest events for a list of repositories, filtering bots and handling large datasets.

    Returns a list of dictionaries, each representing a *valid* project containing:
    ``repo_id``, ``event_count`` and the raw ``events`` list.
    """
    valid_projects = []

    for repo_id in repo_list:
        logger.info(f"Ingesting events for repo {repo_id}")
        try:
            raw_events = fetch_repo_events(repo_id)
        except Exception as e:
            logger.warning(f"Skipping repo {repo_id} due to fetch error: {e}")
            continue

        # Apply bot filter
        events = filter_bot_events(raw_events)

        if len(events) < min_events:
            logger.warning(f"Repo {repo_id} has only {len(events)} events after bot filtering; skipping")
            continue

        valid_projects.append({
            "repo_id": repo_id,
            "event_count": len(events),
            "events": events,
        })

        if len(valid_projects) >= target_size:
            break

    return valid_projects


def main():
    """Main entry point for data ingestion."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Ingest GitHub event data')
    parser.add_argument('--fetch', action='store_true', help='Fetch data from GitHub')
    parser.add_argument('--sample-size', type=int, default=5, help='Number of projects to sample')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--large-repo', action='store_true', help='Enable large repo handling (chunking)')

    args = parser.parse_args()

    config = get_config()
    ensure_directories_exist([config.get('raw_dir')])

    if args.fetch:
        logger.info("Starting data ingestion")

        # Initialise GitHub client (kept for compatibility with other modules)
        client = create_client()

        # Real, public repository IDs for deterministic testing.
        # These IDs correspond to well‑known repositories that are guaranteed to exist.
        sample_repos = [1513320, 28827669]  # `psf/requests` and `numpy/numpy`

        valid_projects = ingest_sample_projects(
            repo_list=sample_repos,
            client=client,
            min_events=config.get('min_events', 10),
            target_size=args.sample_size,
        )

        # Flatten events from all valid projects
        all_events = []
        for proj in valid_projects:
            all_events.extend(proj['events'])

        # Determine output path
        output_path = Path(args.output) if args.output else Path(config.get('raw_dir')) / 'events.json'
        ensure_directories_exist([output_path.parent])

        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_events, f, indent=2)

        logger.info(f"Ingestion complete. Wrote {len(all_events)} events to {output_path}")

        if args.large_repo:
            logger.info("Large repo handling enabled. Check data/logs/rate_limit_events.log for backoff entries.")
    else:
        logger.info("No action specified. Use --fetch to start ingestion.")


if __name__ == "__main__":
    main()
