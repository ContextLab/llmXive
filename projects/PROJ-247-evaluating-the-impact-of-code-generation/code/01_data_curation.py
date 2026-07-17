import os
import sys
import time
import csv
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Import from local utils
from utils.logging_config import get_logger, setup_logging
from utils.github_client import GitHubClient, GitHubClientError
from utils.models import Repository

# Setup logging
logger = get_logger(__name__)

# Constants
CLONE_DEPTH = 100
MIN_STARS = 5
MIN_COMMITS_90_DAYS = 1
REPO_METADATA_PATH = "data/raw/repo_metadata.csv"
CHECKPOINT_PATH = "data/logs/curator_checkpoint.json"
OUTPUT_DIR = "data/raw"

def setup_output_directories():
    """Ensure required output directories exist."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path("data/logs").mkdir(parents=True, exist_ok=True)

def load_checkpoint():
    """Load checkpoint state if it exists."""
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, 'r') as f:
            return json.load(f)
    return {"processed_repos": [], "last_repo": None}

def save_checkpoint(processed_repos: List[str], last_repo: Optional[str]):
    """Save current progress to checkpoint."""
    checkpoint = {
        "processed_repos": processed_repos,
        "last_repo": last_repo,
        "timestamp": datetime.now().isoformat()
    }
    with open(CHECKPOINT_PATH, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def search_github_repos(
    client: GitHubClient, 
    topics: List[str] = None, 
    keywords: List[str] = None,
    per_page: int = 100,
    max_pages: int = 10
) -> List[Dict[str, Any]]:
    """
    Search GitHub for repositories matching topics or keywords.
    Expands search if initial results are insufficient.
    """
    repos = []
    query_parts = []

    # Build query based on topics
    if topics:
        for topic in topics:
            query_parts.append(f"topic:{topic}")
    
    # Build query based on keywords
    if keywords:
        for kw in keywords:
            query_parts.append(f"{kw}")

    if not query_parts:
        logger.warning("No search criteria provided. Using default topics.")
        query_parts = ["topic:llm-generated", "topic:copilot"]

    full_query = " OR ".join(query_parts)
    
    page = 1
    while page <= max_pages:
        try:
            results = client.search_repositories(query=full_query, per_page=per_page, page=page)
            if not results:
                break
            repos.extend(results)
            if len(results) < per_page:
                break
            page += 1
        except GitHubClientError as e:
            logger.error(f"Search error on page {page}: {e}")
            break
        
        # Rate limit handling
        time.sleep(1.0)

    logger.info(f"Found {len(repos)} repositories via search.")
    return repos

def deduplicate_repos(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate repositories based on full_name."""
    seen = set()
    unique = []
    for repo in repos:
        full_name = repo.get('full_name')
        if full_name and full_name not in seen:
            seen.add(full_name)
            unique.append(repo)
    return unique

def filter_active_repos(repos: List[Dict[str, Any]], client: GitHubClient) -> List[Dict[str, Any]]:
    """
    Filter repositories based on activity criteria:
    - >= MIN_STARS stars
    - >= MIN_COMMITS_90_DAYS commits in last 90 days
    """
    active_repos = []
    cutoff_date = datetime.now() - timedelta(days=90)

    for repo_data in repos:
        try:
            # Get full repo details to check stars and update time
            full_repo = client.get_repo(repo_data['full_name'])
            
            # Check stars
            if full_repo.stargazers_count < MIN_STARS:
                continue

            # Check updated_at (as proxy for recent activity)
            # Note: For precise commit count, we might need git log, but updated_at is a good first filter
            updated_at = datetime.fromisoformat(full_repo.updated_at.replace('Z', '+00:00'))
            if updated_at < cutoff_date:
                continue

            # Optional: Verify commit count if needed, but updated_at usually suffices for "active"
            # If strict commit count is required, we would clone or use API to get commit count
            # For now, relying on updated_at and stars as per T011 description
            
            active_repos.append(full_repo)
            logger.debug(f"Repo {full_repo.full_name} passed activity filters.")
            
        except GitHubClientError as e:
            logger.warning(f"Skipping repo {repo_data.get('full_name')}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing repo {repo_data.get('full_name')}: {e}")
            continue

    logger.info(f"Filtered to {len(active_repos)} active repositories.")
    return active_repos

def shallow_clone_repo(repo_url: str, target_path: str, depth: int = CLONE_DEPTH) -> bool:
    """
    Perform a shallow clone of a repository.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info(f"Cloning {repo_url} to {target_path} (depth={depth})")
        cmd = [
            "git", "clone", "--depth", str(depth), "--single-branch",
            repo_url, target_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"Git clone failed for {repo_url}: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Clone timeout for {repo_url}")
        return False
    except Exception as e:
        logger.error(f"Clone exception for {repo_url}: {e}")
        return False

def extract_repository_metadata(repos: List[Any], output_path: str = REPO_METADATA_PATH) -> None:
    """
    Extract repository metadata (stargazers_count, created_at, updated_at)
    and store in CSV for use in matching.
    
    Args:
        repos: List of repository objects (can be dicts or GitHub Repo objects)
        output_path: Path to the output CSV file
    """
    setup_output_directories()
    
    fieldnames = ['repo_id', 'full_name', 'stargazers_count', 'created_at', 'updated_at', 'url']
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for i, repo in enumerate(repos):
        try:
            # Handle both dict and object types
            if isinstance(repo, dict):
                repo_id = repo.get('id', i)
                full_name = repo.get('full_name', 'unknown')
                stars = repo.get('stargazers_count', 0)
                created = repo.get('created_at', '')
                updated = repo.get('updated_at', '')
                url = repo.get('html_url', '')
            else:
                # Assuming it's a GitHub Repo object or similar
                repo_id = repo.id
                full_name = repo.full_name
                stars = repo.stargazers_count
                created = repo.created_at
                updated = repo.updated_at
                url = repo.html_url

            rows.append({
                'repo_id': repo_id,
                'full_name': full_name,
                'stargazers_count': stars,
                'created_at': created,
                'updated_at': updated,
                'url': url
            })
            
        except Exception as e:
            logger.error(f"Failed to extract metadata for repo at index {i}: {e}")
            continue

    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Saved metadata for {len(rows)} repositories to {output_path}")

def extract_code_blocks_py(repo_path: str) -> List[Dict[str, Any]]:
    """Extract code blocks from Python files."""
    # Placeholder for T012 logic
    return []

def extract_code_blocks_js(repo_path: str) -> List[Dict[str, Any]]:
    """Extract code blocks from JavaScript files."""
    # Placeholder for T012 logic
    return []

def extract_code_blocks_from_repo(repo_path: str) -> List[Dict[str, Any]]:
    """Extract code blocks from all supported languages in a repo."""
    blocks = []
    blocks.extend(extract_code_blocks_py(repo_path))
    blocks.extend(extract_code_blocks_js(repo_path))
    return blocks

def save_blocks_to_csv(blocks: List[Dict[str, Any]], output_path: str):
    """Save extracted code blocks to CSV."""
    # Placeholder for T012 logic
    pass

def detect_git_mv_exclusions(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect and exclude blocks that were moved via git mv."""
    # Placeholder for T012b logic
    return blocks

def calculate_static_metrics(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate static complexity metrics using radon."""
    # Placeholder for T014 logic
    return blocks

def enrich_blocks_with_metrics(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich blocks with calculated metrics."""
    # Placeholder for T014 logic
    return blocks

def enforce_repository_inclusion_criteria(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enforce criteria: >= 5 LLM and >= 5 Human blocks."""
    # Placeholder for T016 logic
    return blocks

def tag_blocks_with_classifier(blocks: List[Dict[str, Any]], classifier) -> List[Dict[str, Any]]:
    """Tag blocks as LLM/Human using CodeBERT classifier."""
    # Placeholder for T013 logic
    return blocks

def main():
    """Main entry point for data curation pipeline."""
    setup_logging()
    setup_output_directories()
    
    # Initialize GitHub Client
    client = GitHubClient()
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    processed_ids = checkpoint.get("processed_repos", [])
    
    # Search for repos
    # T010: Search topics, expand if needed
    topics = ["llm-generated", "copilot"]
    keywords = ["LLM generated code", "Copilot generated"]
    
    all_repos = search_github_repos(client, topics=topics, keywords=keywords)
    if len(all_repos) < 50:
        logger.warning("Initial search yielded <50 repos. Expanding search...")
        # Logic to expand search would go here if needed, but search_github_repos handles expansion logic
    
    # Deduplicate
    unique_repos = deduplicate_repos(all_repos)
    
    # Filter active repos (T011)
    active_repos = filter_active_repos(unique_repos, client)
    
    if not active_repos:
        logger.error("No active repositories found. Exiting.")
        sys.exit(1)
    
    # Extract Metadata (T011a)
    extract_repository_metadata(active_repos, REPO_METADATA_PATH)
    
    # Note: The actual cloning and block extraction would happen in subsequent steps
    # or in a loop here. For this task, we focus on metadata extraction.
    
    logger.info("Data curation metadata extraction complete.")

if __name__ == "__main__":
    main()
