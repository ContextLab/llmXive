import os
import json
import csv
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.github_client import GitHubClient
from utils.metrics import process_review_metrics

# Configure logging for the ingestion process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

# Generic config patterns that do NOT explicitly name an LLM tool
GENERIC_CONFIG_NAMES = {
    'config.json',
    'settings.json',
    'project.json',
    'appsettings.json',
    'config.yaml',
    'settings.yaml',
    'project.yaml',
    'config.yml',
    'settings.yml',
    'project.yml',
    'options.json',
    'options.yaml'
}

# Known LLM-specific config patterns
LLM_CONFIG_NAMES = {
    '.cursorrules',
    '.copilot',
    'copilot_config.json',
    'copilot_settings.json',
    'llm_config.json',
    '.aider.conf',
    '.githelp',
    'github-copilot.json'
}

def load_repo_list(repo_list_path: str) -> List[Dict[str, Any]]:
    """Load the list of repositories to analyze from a JSON file."""
    path = Path(repo_list_path)
    if not path.exists():
        raise FileNotFoundError(f"Repository list file not found: {repo_list_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'repositories' in data:
        return data['repositories']
    else:
        raise ValueError(f"Invalid format in {repo_list_path}: expected a list or dict with 'repositories' key")

def fetch_repository_details(client: GitHubClient, repo_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fetch detailed repository data from GitHub API."""
    owner = repo_info.get('owner')
    name = repo_info.get('name')
    if not owner or not name:
        logger.warning(f"Skipping repo with missing owner/name: {repo_info}")
        return None
    
    try:
        repo_data = client.get_repo(owner, name)
        if not repo_data:
            logger.warning(f"Repository not found or inaccessible: {owner}/{name}")
            return None
        
        # Fetch PRs and commits
        prs = client.get_pulls(owner, name, state='closed', per_page=100)
        commits = client.get_commits(owner, name, per_page=100)
        
        # Fetch config files
        config_files = {}
        for filename in GENERIC_CONFIG_NAMES.union(LLM_CONFIG_NAMES):
            try:
                content = client.get_file_content(owner, name, filename)
                if content:
                    config_files[filename] = content
            except Exception as e:
                logger.debug(f"Could not fetch {filename} for {owner}/{name}: {e}")
        
        return {
            'owner': owner,
            'name': name,
            'repo_data': repo_data,
            'prs': prs,
            'commits': commits,
            'config_files': config_files
        }
    except Exception as e:
        logger.error(f"Error fetching details for {owner}/{name}: {e}")
        return None

def calculate_llm_adoption_flag(repo_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine LLM adoption status and log warnings for ambiguous signals.
    
    Returns a dict with:
    - llm_adoption_flag: True/False/None
    - adoption_signals: list of detected signals
    - ambiguous_warning: bool (True if generic config detected without clear LLM signal)
    """
    config_files = repo_details.get('config_files', {})
    repo_name = f"{repo_details['owner']}/{repo_details['name']}"
    
    adoption_signals = []
    ambiguous_warning = False
    llm_adoption_flag = None
    
    # Check for explicit LLM config files
    for filename in config_files:
        if filename in LLM_CONFIG_NAMES:
            adoption_signals.append(f"Explicit LLM config: {filename}")
            llm_adoption_flag = True
            break
        elif filename in GENERIC_CONFIG_NAMES:
            # Check if the generic config file mentions LLM tools
            content = config_files[filename].get('content', '').lower()
            if any(keyword in content for keyword in ['copilot', 'cursor', 'aider', 'llm', 'codeium']):
                adoption_signals.append(f"Generic config with LLM mention: {filename}")
                llm_adoption_flag = True
            else:
                # Generic config without LLM mention - potential ambiguous signal
                if 'llm_adoption_flag' not in adoption_signals:
                    ambiguous_warning = True
    
    # Check README/CONTRIBUTING for mentions (already implemented in T022)
    # This is a simplified check - the full implementation would parse these files
    readme_content = config_files.get('README.md', {}).get('content', '').lower()
    contributing_content = config_files.get('CONTRIBUTING.md', {}).get('content', '').lower()
    
    for content, filename in [(readme_content, 'README.md'), (contributing_content, 'CONTRIBUTING.md')]:
        if any(keyword in content for keyword in ['copilot', 'cursor', 'aider', 'llm', 'codeium']):
            adoption_signals.append(f"LLM mention in {filename}")
            if llm_adoption_flag is None:
                llm_adoption_flag = True
    
    # Check commit messages for Copilot/LLM frequency (T022 implementation)
    commits = repo_details.get('commits', [])
    if commits:
        copilot_commits = sum(1 for c in commits if 'copilot' in c.get('message', '').lower() or 'llm' in c.get('message', '').lower())
        frequency = copilot_commits / len(commits) if commits else 0
        if frequency >= 0.05:
            adoption_signals.append(f"Commit message frequency: {frequency:.1%}")
            if llm_adoption_flag is None:
                llm_adoption_flag = True
    
    # If no clear signal but generic configs exist, log warning
    if ambiguous_warning and not adoption_signals:
        logger.warning(
            f"Ambiguous LLM signal detected for {repo_name}: "
            f"Generic config files found ({', '.join([f for f in config_files if f in GENERIC_CONFIG_NAMES])}) "
            f"without explicit LLM tool naming. This repository will be flagged for sensitivity analysis."
        )
        # Keep flag as None for ambiguous cases
        llm_adoption_flag = None
    
    return {
        'llm_adoption_flag': llm_adoption_flag,
        'adoption_signals': adoption_signals,
        'ambiguous_warning': ambiguous_warning and not adoption_signals
    }

def run_ingestion(repo_list_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main ingestion pipeline that processes repositories and generates the master dataset.
    
    This implementation includes T026: logging "ambiguous LLM signal" warnings for repos
    with generic configs (e.g., config.json without tool naming) to support sensitivity analysis.
    """
    logger.info(f"Starting ingestion pipeline from {repo_list_path}")
    
    # Load repository list
    repo_list = load_repo_list(repo_list_path)
    logger.info(f"Loaded {len(repo_list)} repositories to process")
    
    # Initialize GitHub client
    client = GitHubClient()
    
    # Process each repository
    results = []
    ambiguous_count = 0
    
    for repo_info in repo_list:
        repo_details = fetch_repository_details(client, repo_info)
        if not repo_details:
            continue
        
        # Calculate LLM adoption flag (includes T026 logic)
        adoption_data = calculate_llm_adoption_flag(repo_details)
        
        # Process review metrics (T024)
        prs = repo_details.get('prs', [])
        review_metrics = process_review_metrics(prs)
        
        # Build result row
        result_row = {
            'owner': repo_details['owner'],
            'name': repo_details['name'],
            'llm_adoption_flag': adoption_data['llm_adoption_flag'],
            'adoption_signals': json.dumps(adoption_data['adoption_signals']),
            'ambiguous_llm_signal': adoption_data['ambiguous_warning'],
            'total_prs': len(prs),
            'avg_comment_length': review_metrics.get('avg_comment_length', 0),
            'review_thread_depth': review_metrics.get('review_thread_depth', 0),
            'revert_frequency': review_metrics.get('revert_frequency', 0)
        }
        
        results.append(result_row)
        
        if adoption_data['ambiguous_warning']:
            ambiguous_count += 1
    
    # Write results to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'owner', 'name', 'llm_adoption_flag', 'adoption_signals', 
        'ambiguous_llm_signal', 'total_prs', 'avg_comment_length',
        'review_thread_depth', 'revert_frequency'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Ingestion complete. Processed {len(results)} repositories.")
    logger.info(f"Ambiguous LLM signals detected: {ambiguous_count} repositories")
    logger.info(f"Results written to {output_path}")
    
    return {
        'total_processed': len(results),
        'ambiguous_signals': ambiguous_count,
        'output_file': str(output_file)
    }

if __name__ == "__main__":
    # Example usage - in production, these would come from config/environment
    REPO_LIST_PATH = "data/raw/repo_list.json"
    OUTPUT_PATH = "data/derived/master_dataset.csv"
    
    if os.path.exists(REPO_LIST_PATH):
        result = run_ingestion(REPO_LIST_PATH, OUTPUT_PATH)
        print(f"Ingestion completed: {result}")
    else:
        print(f"Error: Repository list file not found at {REPO_LIST_PATH}")
        print("Please create data/raw/repo_list.json with repository data first.")