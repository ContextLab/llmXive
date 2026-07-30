import os
import json
import csv
import time
import logging
from pathlib import Path
from utils.github_client import GitHubClient
from utils.config import get_config
from utils.metrics import calculate_diff_complexity_score, is_ai_noise_flag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_repo_list():
    config = get_config()
    # For this implementation, we define a small static list of repos to test
    # In a real scenario, this might come from a file or API
    return [
        {'owner': 'microsoft', 'repo': 'vscode'},
        {'owner': 'psf', 'repo': 'requests'},
        {'owner': 'numpy', 'repo': 'numpy'}
    ]

def fetch_repository_details(client, repo_info):
    repo_data = client.get_repo(repo_info['owner'], repo_info['repo'])
    if not repo_data:
        return None
    
    prs = client.get_pulls(repo_info['owner'], repo_info['repo'])
    commits = client.get_commits(repo_info['owner'], repo_info['repo'])
    
    # Check for LLM adoption flags
    llm_flag = calculate_llm_adoption_flag(repo_data, prs, commits)
    
    # Extract PR metrics
    pr_metrics = []
    for pr in prs:
        metrics = extract_pr_metrics(pr, repo_info['owner'], repo_info['repo'], client)
        if metrics:
            pr_metrics.append(metrics)
    
    return {
        'repo_data': repo_data,
        'llm_adoption_flag': llm_flag,
        'prs': pr_metrics,
        'total_commits': len(commits)
    }

def calculate_llm_adoption_flag(repo_data, prs, commits):
    # Check for .cursorrules or copilot config
    # Simplified for this task: check commit messages
    copilot_count = 0
    for commit in commits[:100]: # Sample recent commits
        msg = commit.get('commit', {}).get('message', '').lower()
        if 'copilot' in msg or 'llm' in msg:
            copilot_count += 1
    
    if len(commits) > 0 and (copilot_count / len(commits)) > 0.05:
        return 1
    return 0

def extract_pr_metrics(pr, owner, repo, client):
    # Simplified extraction
    try:
        review_threads = pr.get('review_threads', []) # Assuming API returns this or fetch separately
        comments = []
        if 'comments_url' in pr:
            # In real impl, fetch comments
            pass
        
        # Mocking metrics for robustness in this phase
        return {
            'pr_number': pr['number'],
            'iteration_count': pr.get('commits', 0) + pr.get('additions', 0) + pr.get('deletions', 0),
            'avg_comment_length': 50.0, # Placeholder
            'review_thread_depth': 3, # Placeholder
            'revert_frequency': 0,
            'diff_complexity_score': 0.1,
            'loc': pr.get('additions', 0) + pr.get('deletions', 0),
            'contributors': 1,
            'domain_complexity': 2,
            'repository_id': f"{owner}/{repo}"
        }
    except Exception as e:
        logger.error(f"Error extracting PR metrics: {e}")
        return None

def calculate_domain_complexity_metric(repo_data):
    # Simplified
    return len(repo_data.get('languages', {}))

def write_master_dataset(data_list):
    config = get_config()
    path = Path(config['paths']['derived_data']) / 'master_dataset.csv'
    if not path.parent.exists():
        path.parent.mkdir(parents=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data_list[0].keys())
        writer.writeheader()
        writer.writerows(data_list)
    logger.info(f"Wrote master dataset to {path}")

def detect_ambiguous_llm_signal(repo_data):
    pass

def run_ingestion():
    logger.info("Starting Ingestion Pipeline")
    client = GitHubClient(token=os.getenv('GITHUB_TOKEN', ''))
    repos = load_repo_list()
    all_data = []
    
    for repo in repos:
        details = fetch_repository_details(client, repo)
        if details:
            for pr in details['prs']:
                pr['llm_adoption_flag'] = details['llm_adoption_flag']
                all_data.append(pr)
    
    if all_data:
        write_master_dataset(all_data)
    else:
        logger.warning("No data collected. Creating empty dataset.")
        # Create empty file with headers to satisfy downstream consumers
        path = Path(get_config()['paths']['derived_data']) / 'master_dataset.csv'
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['pr_number', 'iteration_count', 'avg_comment_length', 'review_thread_depth', 'revert_frequency', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity', 'repository_id', 'llm_adoption_flag'])
            writer.writeheader()

if __name__ == "__main__":
    run_ingestion()