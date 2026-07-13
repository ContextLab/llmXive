import base64
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Iterator
from pathlib import Path

import requests
from tqdm import tqdm

from code.utils.models import PullRequest, CodeSnippet
from code.utils.validators import scan_pii
from code.utils.config import get_config

# Configuration constants
GITHUB_API_BASE = "https://api.github.com"
SEARCH_ENDPOINT = f"{GITHUB_API_BASE}/search/repositories"
PRS_ENDPOINT = f"{GITHUB_API_BASE}/repos"
RATE_LIMIT_SLEEP = 2.0  # Conservative backoff
MAX_RETRIES = 5

def parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 date string to datetime object."""
    if not date_str:
        return None
    try:
        # Handle 'Z' suffix and timezone offsets
        date_str = date_str.replace('Z', '+00:00')
        if '+' in date_str:
            date_str = date_str.split('+')[0]
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None

def parse_pr_response(pr_data: Dict[str, Any]) -> PullRequest:
    """Parse a GitHub PR JSON response into a PullRequest model."""
    repo_full_name = pr_data.get('head', {}).get('repo', {}).get('full_name') or pr_data.get('base', {}).get('repo', {}).get('full_name')
    repo_id = pr_data.get('base', {}).get('repo', {}).get('id')
    
    # Extract author type based on organization status if available, else infer
    author_login = pr_data.get('user', {}).get('login', '')
    # Simple heuristic: if login contains 'bot' or is a known bot pattern, mark as bot
    author_type = "bot" if 'bot' in author_login.lower() else "human"

    return PullRequest(
        pr_id=str(pr_data.get('number', '')),
        repo_id=str(repo_id) if repo_id else "",
        repo_full_name=repo_full_name,
        author_type=author_type,
        state=pr_data.get('state', 'unknown'),
        created_at=parse_iso_date(pr_data.get('created_at')),
        updated_at=parse_iso_date(pr_data.get('updated_at')),
        merged_at=parse_iso_date(pr_data.get('merged_at')),
        closed_at=parse_iso_date(pr_data.get('closed_at')),
        additions=pr_data.get('additions', 0),
        deletions=pr_data.get('deletions', 0),
        changed_files=pr_data.get('changed_files', 0),
        title=pr_data.get('title', ''),
        body=pr_data.get('body', ''),
        labels=[lbl.get('name') for lbl in pr_data.get('labels', [])]
    )

def parse_file_content(file_data: Dict[str, Any]) -> CodeSnippet:
    """Parse a GitHub file blob response into a CodeSnippet model."""
    # Decode content if it's base64 encoded (though API usually returns raw for small files)
    content = file_data.get('content', '')
    encoding = file_data.get('encoding', 'utf-8')
    
    if encoding == 'base64':
        try:
            content = base64.b64decode(content).decode('utf-8')
        except Exception:
            content = ""

    return CodeSnippet(
        snippet_id=f"{file_data.get('sha', 'unknown')}_{file_data.get('filename', 'unknown')}",
        source_commit=file_data.get('sha', ''),
        filename=file_data.get('filename', ''),
        filepath=file_data.get('filename', ''),
        generation_source="github_raw",
        content=content,
        size_bytes=len(content.encode('utf-8')),
        language=file_data.get('language', 'unknown'),
        raw_patch=file_data.get('patch', '')
    )

def _get_headers() -> Dict[str, str]:
    """Construct headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-Research-Scraper"
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def _rate_limited_request(method: str, url: str, params: Optional[Dict] = None, max_retries: int = MAX_RETRIES) -> Optional[Dict]:
    """Perform a rate-limited request with exponential backoff."""
    headers = _get_headers()
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.request(method, url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
                # Wait for rate limit reset or exponential backoff
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                if reset_time:
                    wait = max(reset_time - int(time.time()) + 1, RATE_LIMIT_SLEEP)
                    time.sleep(wait)
                else:
                    time.sleep(RATE_LIMIT_SLEEP * (2 ** attempt))
                attempt += 1
            elif response.status_code == 404:
                return None  # Resource not found
            elif response.status_code >= 500:
                time.sleep(RATE_LIMIT_SLEEP * (2 ** attempt))
                attempt += 1
            else:
                # Client error, no retry
                return None
        except requests.exceptions.RequestException:
            time.sleep(RATE_LIMIT_SLEEP * (2 ** attempt))
            attempt += 1
    
    return None

def fetch_repos_with_stars(min_stars: int = 1000, max_results: int = 100) -> List[Dict[str, Any]]:
    """Fetch a list of repositories with at least min_stars."""
    params = {
        "q": f"stars:>={min_stars}",
        "sort": "stars",
        "order": "desc",
        "per_page": min(100, max_results)
    }
    
    data = _rate_limited_request("GET", SEARCH_ENDPOINT, params)
    if not data or 'items' not in data:
        return []
    
    return data['items'][:max_results]

def fetch_pr_metadata(repo_full_name: str, state: str = "closed", per_page: int = 100) -> List[PullRequest]:
    """Fetch metadata for PRs in a specific repository."""
    prs = []
    page = 1
    
    while True:
        params = {
            "state": state,
            "per_page": per_page,
            "page": page
        }
        url = f"{PRS_ENDPOINT}/{repo_full_name}/pulls"
        
        data = _rate_limited_request("GET", url, params)
        if not data or len(data) == 0:
            break
        
        for pr_raw in data:
            pr_obj = parse_pr_response(pr_raw)
            if pr_obj.state == 'closed' or pr_obj.state == 'merged':
                prs.append(pr_obj)
        
        if len(data) < per_page:
            break
        page += 1
        
        # Safety break for very large repos
        if page > 10: 
            break
    
    return prs

def fetch_pr_files(repo_full_name: str, pr_number: int) -> List[Dict[str, Any]]:
    """Fetch the list of files changed in a specific PR."""
    url = f"{PRS_ENDPOINT}/{repo_full_name}/pulls/{pr_number}/files"
    data = _rate_limited_request("GET", url)
    return data if data else []

def fetch_pr_content_raw(repo_full_name: str, file_sha: str, ref: str = "HEAD") -> Optional[Dict[str, Any]]:
    """Fetch the raw content of a file given its SHA."""
    # Using the git blob API
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/git/blobs/{file_sha}"
    data = _rate_limited_request("GET", url)
    return data

def fetch_pr_metadata_and_files(repo_full_name: str, limit_prs: int = 50) -> Iterator[Tuple[PullRequest, List[CodeSnippet]]]:
    """
    Generator that yields PR metadata and their associated file contents.
    This is the main entry point for data acquisition.
    """
    prs = fetch_pr_metadata(repo_full_name, state="closed", per_page=50)
    
    # Limit the number of PRs processed to avoid rate limits during a single run
    for i, pr in enumerate(prs):
        if i >= limit_prs:
            break
        
        if pr.state not in ['closed', 'merged']:
            continue

        files = fetch_pr_files(repo_full_name, int(pr.pr_id))
        snippets = []
        
        for file_raw in files:
            # We need the content. The files endpoint gives patch and sha.
            # If patch is available and small, we can use it, but for full content we need the blob.
            # However, for diff analysis, the patch is often sufficient.
            # Let's try to get the full content if the patch is truncated or if we need full context.
            # For this implementation, we will use the patch if available, otherwise fetch blob.
            
            content_str = file_raw.get('patch', '')
            if not content_str:
                # Fallback to fetching blob content if patch is missing (rare)
                blob_data = fetch_pr_content_raw(repo_full_name, file_raw.get('sha', ''))
                if blob_data:
                    content_str = base64.b64decode(blob_data.get('content', '')).decode('utf-8')
            
            # Create a snippet object
            snippet = CodeSnippet(
                snippet_id=f"{pr.pr_id}_{file_raw.get('sha', 'unknown')}",
                source_commit=file_raw.get('sha', ''),
                filename=file_raw.get('filename', ''),
                filepath=file_raw.get('filename', ''),
                generation_source="github_raw",
                content=content_str,
                size_bytes=len(content_str.encode('utf-8')),
                language=file_raw.get('language', 'unknown'),
                raw_patch=content_str
            )
            snippets.append(snippet)
        
        yield pr, snippets

def run_acquisition_pipeline(output_dir: str = "data/raw", min_stars: int = 1000, repo_limit: int = 5, pr_limit_per_repo: int = 20):
    """
    Main pipeline function to fetch PRs from high-star repositories.
    
    Args:
        output_dir: Directory to save raw JSON data
        min_stars: Minimum star count for repositories
        repo_limit: Maximum number of repositories to process
        pr_limit_per_repo: Maximum PRs to process per repository
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Fetching repositories with >= {min_stars} stars...")
    repos = fetch_repos_with_stars(min_stars=min_stars, max_results=repo_limit)
    
    if not repos:
        print("No repositories found matching criteria.")
        return

    total_prs = 0
    total_snippets = 0
    
    for repo in repos:
        repo_name = repo.get('full_name')
        print(f"Processing repository: {repo_name} ({repo.get('stargazers_count', 0)} stars)")
        
        # Create repo-specific output path
        safe_repo_name = repo_name.replace('/', '_')
        repo_output_path = Path(output_dir) / f"{safe_repo_name}.json"
        
        repo_data = {
            "repo_info": repo,
            "pull_requests": []
        }
        
        # Use the generator to fetch PRs and files
        for pr, snippets in fetch_pr_metadata_and_files(repo_name, limit_prs=pr_limit_per_repo):
            pr_dict = {
                "pr_data": pr.to_dict(),
                "snippets": [s.to_dict() for s in snippets]
            }
            repo_data["pull_requests"].append(pr_dict)
            total_prs += 1
            total_snippets += len(snippets)
        
        # Write repo data to file
        with open(repo_output_path, 'w', encoding='utf-8') as f:
            json.dump(repo_data, f, indent=2, default=str)
        
        print(f"  Saved {len(repo_data['pull_requests'])} PRs to {repo_output_path}")
    
    print(f"Acquisition complete. Processed {total_prs} PRs and {total_snippets} snippets.")

if __name__ == "__main__":
    # Default execution for CLI
    run_acquisition_pipeline()
