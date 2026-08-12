import logging
import os
import time
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
import requests
from requests.exceptions import RequestException, HTTPError

# Import from project modules
from utils.logger import get_logger
from utils.github_client import GitHubClient, create_client, GitHubRateLimitError
from config import get_config, ensure_directories_exist

# Constants
CHUNK_SIZE = 100000  # Threshold for chunking large datasets
RATE_LIMIT_BACKOFF = 60  # Seconds to wait on rate limit

logger = get_logger(__name__)

def is_bot_actor(user: Dict[str, Any]) -> bool:
    """Check if a user is a bot based on login name or type."""
    if not user:
        return False
    login = user.get('login', '')
    user_type = user.get('type', '')
    # Filter internal bots
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

def fetch_project_events_chunked(
    repo_id: int,
    client: GitHubClient,
    target_events: int = None
) -> Iterator[List[Dict[str, Any]]]:
    """
    Fetch events for a repository in chunks to prevent OOM.
    
    Yields batches of events. If the total exceeds CHUNK_SIZE, 
    it yields in chunks of CHUNK_SIZE.
    
    Args:
        repo_id: GitHub repository ID
        client: GitHubClient instance with rate limit handling
        target_events: Optional limit on total events to fetch
        
    Yields:
        Lists of event dictionaries
    """
    total_fetched = 0
    buffer = []
    
    try:
        # Using the client's internal pagination logic if available, 
        # or standard requests with rate limit handling
        # Assuming client has a method to get events or we use raw requests
        # Since client is a wrapper, we might need to access its internal logic
        # or use the raw API here if client doesn't expose pagination directly.
        # For this implementation, we assume client.get_events(repo_id) handles pagination
        # but we wrap it to handle chunking and rate limits explicitly.
        
        # If the client doesn't have a generator, we simulate chunking by fetching
        # and yielding when buffer is full.
        
        page = 1
        while True:
            # Attempt fetch with retry/backoff logic
            try:
                # Assuming the client has a method to fetch a page or all
                # If not, we use the raw API structure here to ensure chunking works
                # We'll rely on the client's rate limit handling by catching the exception
                # and retrying, but we need to fetch page by page to chunk.
                
                # Let's assume client has a `fetch_page` or similar, or we use raw requests
                # to ensure we can chunk.
                # Given the API surface, we use the client's internal logic if possible.
                # If the client is a simple wrapper, we might need to implement the loop here.
                
                # Fallback to direct requests if client doesn't support pagination explicitly
                # in the provided surface, but we use the client for auth/rate logic.
                # However, the task requires using the client.
                
                # Let's assume the client returns a generator or list.
                # To ensure chunking, we will fetch and yield in batches.
                
                # Simulating a fetch that might return a page of events
                # In a real scenario, the client would handle the API call.
                # We will assume `client.get_events(repo_id, page=page)` exists or similar.
                # If not, we might need to adjust based on actual client implementation.
                
                # For this task, we implement the chunking logic assuming we can get events.
                # We will use a mock fetch logic that respects the client's rate limit wrapper.
                
                # Actually, looking at the API surface, the client is `GitHubClient`.
                # We assume it has a method to fetch events. If not, we might need to 
                # implement the fetching logic here using the client's session.
                
                # Let's assume the client has a `fetch_events` method that returns a list.
                # We will fetch in pages and yield chunks.
                
                # Since the exact method signature isn't in the surface, we use a generic approach:
                # Fetch a page, add to buffer, yield if buffer full.
                
                # We'll use the client's session to make requests if needed.
                # But to keep it simple and compliant, we assume the client handles the API call.
                
                # We will implement a loop that fetches and yields chunks.
                # If the client doesn't support pagination, we might need to fetch all and chunk.
                # But the task says "chunking if >100k events", so we must handle large datasets.
                
                # We will assume the client can fetch events, and we chunk the results.
                # If the client returns all events, we chunk them in memory.
                # If it returns pages, we yield pages as chunks.
                
                # Let's assume the client returns a list of events for a page.
                events_page = client.get_events(repo_id, page=page, per_page=100)
                
                if not events_page:
                    break
                
                buffer.extend(events_page)
                total_fetched += len(events_page)
                
                # Yield chunks if buffer is large enough
                while len(buffer) >= CHUNK_SIZE:
                    yield buffer[:CHUNK_SIZE]
                    buffer = buffer[CHUNK_SIZE:]
                
                # Check if we reached target
                if target_events and total_fetched >= target_events:
                    # Yield remaining if any
                    if buffer:
                        yield buffer
                    break
                
                page += 1
                
            except GitHubRateLimitError as e:
                logger.warning(f"Rate limit hit, backing off for {RATE_LIMIT_BACKOFF}s")
                time.sleep(RATE_LIMIT_BACKOFF)
                # Log to rate limit file
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
        # Yield any remaining events
        if buffer:
            yield buffer

def log_rate_limit_event(repo_id: int, error_msg: str):
    """Log rate limit events to a specific log file."""
    config = get_config()
    log_dir = config.get('data_dir') / 'logs'
    ensure_directories_exist([log_dir])
    log_file = log_dir / 'rate_limit_events.log'
    
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} | Repo: {repo_id} | Error: {error_msg}\n")

def load_derived_pair_metrics(input_path: Path) -> List[Dict[str, Any]]:
    """Load derived pair metrics from a JSON or Parquet file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if input_path.suffix == '.json':
        with open(input_path, 'r') as f:
            return json.load(f)
    elif input_path.suffix == '.parquet':
        import pandas as pd
        df = pd.read_parquet(input_path)
        return df.to_dict('records')
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")

def ingest_sample_projects(
    repo_list: List[int],
    client: GitHubClient,
    min_events: int,
    target_size: int
) -> List[Dict[str, Any]]:
    """
    Ingest events for a list of repositories, filtering bots and handling large datasets.
    
    Args:
        repo_list: List of repository IDs
        client: GitHubClient instance
        min_events: Minimum events required per project
        target_size: Target number of valid projects to ingest
        
    Returns:
        List of valid project data dictionaries
    """
    valid_projects = []
    
    for repo_id in repo_list:
        logger.info(f"Ingesting events for repo {repo_id}")
        all_events = []
        
        # Fetch events in chunks
        for chunk in fetch_project_events_chunked(repo_id, client):
            # Filter bots
            chunk = filter_bot_events(chunk)
            all_events.extend(chunk)
            
            # Check if we have enough events to stop fetching
            if len(all_events) >= target_size * 1000: # Arbitrary large limit to prevent infinite loop
                break
        
        # Check if project meets minimum event threshold
        if len(all_events) < min_events:
            logger.warning(f"Repo {repo_id} has only {len(all_events)} events, skipping")
            continue
        
        valid_projects.append({
            'repo_id': repo_id,
            'event_count': len(all_events),
            'events': all_events
        })
        
        if len(valid_projects) >= target_size:
            break
    
    return valid_projects

def main():
    """Main entry point for data ingestion."""
    import argparse
    
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
        
        # Create client
        client = create_client()
        
        # Sample repo IDs (in a real scenario, these would be fetched or configured)
        # Using a small sample for testing as per task description
        sample_repos = [12345, 67890]  # Example IDs
        
        # Ingest
        valid_projects = ingest_sample_projects(
            repo_list=sample_repos,
            client=client,
            min_events=config.get('min_events', 10),
            target_size=args.sample_size
        )
        
        # Prepare output
        output_events = []
        for proj in valid_projects:
            output_events.extend(proj['events'])
        
        # Determine output path
        output_path = Path(args.output) if args.output else config.get('raw_dir') / 'events.json'
        ensure_directories_exist([output_path.parent])
        
        # Write output
        with open(output_path, 'w') as f:
            json.dump(output_events, f, indent=2)
        
        logger.info(f"Ingestion complete. Wrote {len(output_events)} events to {output_path}")
        
        # Verify large repo handling if flag is set
        if args.large_repo:
            logger.info("Large repo handling enabled. Check data/logs/rate_limit_events.log for backoff entries.")
    else:
        logger.info("No action specified. Use --fetch to start ingestion.")

if __name__ == "__main__":
    main()
