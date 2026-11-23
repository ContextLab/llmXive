import json
import logging
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import shutil

# Import existing utilities from the project's API surface
from utils.config import get_config, get_github_token, get_data_raw_dir, get_data_processed_dir
from utils.github_client import GitHubClient, create_client
from utils.hasher import hash_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_versions_config() -> Dict[str, Any]:
    """Load versions.yaml configuration."""
    config_path = Path(__file__).parent / "versions.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"versions.yaml not found at {config_path}")
    
    # Simple YAML parser for basic key-value pairs
    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip()
    return config

def build_search_query(language: str, min_stars: int = 1000) -> str:
    """Build GitHub search query for repositories."""
    return f"language:{language} stars:>{min_stars} pushed:>=2023-01-01"

def fetch_repos_for_language(client: GitHubClient, language: str, min_stars: int = 1000, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch repositories for a specific language."""
    query = build_search_query(language, min_stars)
    repos = []
    
    try:
        for repo in client.search_repositories(query, per_page=limit):
            repos.append({
                'owner': repo['owner']['login'],
                'name': repo['name'],
                'language': repo['language'],
                'stars': repo['stargazers_count'],
                'license': repo.get('license', {}).get('key', 'unknown')
            })
    except Exception as e:
        logger.error(f"Failed to fetch repos for {language}: {e}")
    
    return repos

def filter_repos(repos: List[Dict[str, Any]], allowed_licenses: List[str] = None) -> List[Dict[str, Any]]:
    """Filter repositories based on criteria."""
    if allowed_licenses is None:
        allowed_licenses = ['mit', 'apache-2.0', 'bsd-3-clause', 'bsd-2-clause']
    
    filtered = []
    for repo in repos:
        if repo.get('license') in allowed_licenses:
            filtered.append(repo)
        else:
            logger.info(f"Filtered out {repo['owner']}/{repo['name']} due to license: {repo.get('license')}")
    
    return filtered

def clone_repository(repo: Dict[str, Any], raw_dir: Path, retry_count: int = 2) -> Optional[Path]:
    """
    Clone a repository to the raw data directory with error handling and retry logic.
    
    Args:
        repo: Repository metadata dictionary
        raw_dir: Directory to clone into
        retry_count: Number of retry attempts on failure
    
    Returns:
        Path to cloned repository directory if successful, None if failed
    """
    owner = repo['owner']
    name = repo['name']
    repo_id = f"{owner}_{name}"
    clone_path = raw_dir / repo_id
    
    # Check if already cloned
    if clone_path.exists():
        logger.info(f"Repository {repo_id} already exists at {clone_path}, skipping clone")
        return clone_path
    
    # Construct GitHub URL
    token = get_github_token()
    if token:
        url = f"https://{token}@github.com/{owner}/{name}.git"
    else:
        url = f"https://github.com/{owner}/{name}.git"
    
    for attempt in range(retry_count + 1):
        try:
            logger.info(f"Cloning {repo_id} (attempt {attempt + 1}/{retry_count + 1})...")
            
            # Create parent directory if needed
            clone_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Run git clone
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', url, str(clone_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully cloned {repo_id} to {clone_path}")
                return clone_path
            else:
                logger.warning(f"Git clone failed for {repo_id}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout cloning {repo_id} (attempt {attempt + 1})")
        except Exception as e:
            logger.warning(f"Error cloning {repo_id}: {e}")
        
        if attempt < retry_count:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    # All retries failed - log exclusion
    exclusion_path = raw_dir / "exclusion_log.json"
    exclusion_data = []
    
    if exclusion_path.exists():
        with open(exclusion_path, 'r') as f:
            exclusion_data = json.load(f)
    
    exclusion_entry = {
        'repo_id': repo_id,
        'owner': owner,
        'name': name,
        'reason': 'clone_failed',
        'attempts': retry_count + 1
    }
    exclusion_data.append(exclusion_entry)
    
    with open(exclusion_path, 'w') as f:
        json.dump(exclusion_data, f, indent=2)
    
    logger.error(f"Failed to clone {repo_id} after {retry_count + 1} attempts - logged to exclusion_log.json")
    return None

def run_sonarqube_scan(repo_path: Path, output_dir: Path) -> Optional[Path]:
    """Run SonarQube Scanner on a repository."""
    # Implementation would invoke SonarQube Docker container
    # Placeholder for actual implementation
    logger.info(f"SonarQube scan not yet implemented for {repo_path}")
    return None

def run_deepsource_scan(repo_path: Path, output_dir: Path) -> Optional[Path]:
    """Run DeepSource CLI on a repository."""
    # Implementation would invoke DeepSource Docker container
    logger.info(f"DeepSource scan not yet implemented for {repo_path}")
    return None

def run_codeclimate_scan(repo_path: Path, output_dir: Path) -> Optional[Path]:
    """Run CodeClimate Engine on a repository."""
    # Implementation would invoke CodeClimate Docker container
    logger.info(f"CodeClimate scan not yet implemented for {repo_path}")
    return None

def normalize_sonarqube_report(report_path: Path) -> List[Dict[str, Any]]:
    """Normalize SonarQube JSON report to unified schema."""
    # Placeholder implementation
    return []

def normalize_deepsource_report(report_path: Path) -> List[Dict[str, Any]]:
    """Normalize DeepSource JSON report to unified schema."""
    # Placeholder implementation
    return []

def normalize_codeclimate_report(report_path: Path) -> List[Dict[str, Any]]:
    """Normalize CodeClimate JSON report to unified schema."""
    # Placeholder implementation
    return []

def parse_and_normalize_all_reports(raw_dir: Path) -> List[Dict[str, Any]]:
    """Parse and normalize all tool reports."""
    all_issues = []
    # Implementation would iterate through reports and normalize them
    return all_issues

def execute_tool_pipeline(repo_path: Path, output_dir: Path) -> bool:
    """Execute all tool scans on a repository."""
    # Implementation would run all tools
    return True

def main():
    """Main entry point for data acquisition pipeline."""
    config = get_config()
    raw_dir = get_data_raw_dir()
    
    # Ensure raw directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize GitHub client
    client = create_client()
    
    # Fetch repositories for multiple languages
    languages = ['Python', 'Java', 'JavaScript', 'Go']
    all_repos = []
    
    for lang in languages:
        repos = fetch_repos_for_language(client, lang, min_stars=1000, limit=10)
        all_repos.extend(repos)
        logger.info(f"Fetched {len(repos)} repos for {lang}")
    
    # Filter by license
    filtered_repos = filter_repos(all_repos)
    logger.info(f"Filtered to {len(filtered_repos)} repos with valid licenses")
    
    # Save filtered repo list
    repo_list_path = raw_dir / "repo_list.json"
    with open(repo_list_path, 'w') as f:
        json.dump(filtered_repos, f, indent=2)
    logger.info(f"Saved repo list to {repo_list_path}")
    
    # Clone repositories with retry logic
    cloned_count = 0
    for repo in filtered_repos:
        clone_path = clone_repository(repo, raw_dir)
        if clone_path:
            cloned_count += 1
    
    logger.info(f"Successfully cloned {cloned_count}/{len(filtered_repos)} repositories")
    
    # Generate checksums for cloned repos
    logger.info("Generating checksums for cloned repositories...")
    # This would call utils.hasher to generate hashes

if __name__ == "__main__":
    main()
