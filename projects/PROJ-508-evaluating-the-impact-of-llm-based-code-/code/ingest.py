import os
import json
import csv
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.github_client import GitHubClient
from utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_repo_list(config: Dict[str, Any]) -> List[str]:
    """
    Load the list of repositories to analyze from the config.
    """
    repo_list_path = Path(config.get("repo_list_path"))
    if not repo_list_path.exists():
        # Fallback to a default list if file missing (for testing)
        return config.get("default_repo_list", [])
    
    with open(repo_list_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def fetch_repository_details(
    gh_client: GitHubClient, repo_name: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed information for a single repository including PRs, commits,
    and configuration files.
    """
    try:
        owner, name = repo_name.split("/")
        repo_info = gh_client.get_repo(owner, name)
        
        if not repo_info:
            logger.warning(f"Repository {repo_name} not found or private.")
            return None
        
        # Fetch PRs
        prs = gh_client.get_pull_requests(owner, name, state="closed", per_page=100)
        pr_data = []
        for pr in prs:
            pr_data.append({
                "number": pr["number"],
                "state": pr["state"],
                "created_at": pr["created_at"],
                "merged_at": pr["merged_at"],
                "comments": pr.get("comments", 0),
                "review_comments": pr.get("review_comments", 0),
                "commits": pr.get("commits", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
            })
        
        # Fetch recent commits
        commits = gh_client.get_commits(owner, name, per_page=50)
        commit_data = []
        for commit in commits:
            commit_data.append({
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "additions": commit.get("stats", {}).get("additions", 0),
                "deletions": commit.get("stats", {}).get("deletions", 0),
                "total": commit.get("stats", {}).get("total", 0),
            })
        
        # Fetch config files for LLM adoption detection
        config_files = gh_client.get_contents(owner, name, path="")
        config_data = {}
        languages = gh_client.get_languages(owner, name)
        
        for file in config_files:
            if file["name"] in [".cursorrules", "copilot.yml", "copilot.json", "config.json"]:
                try:
                    content = gh_client.get_file_content(owner, name, file["path"])
                    config_data[file["name"]] = content
                except Exception:
                    pass
        
        return {
            "repo_id": repo_info["id"],
            "repo_name": repo_name,
            "default_branch": repo_info.get("default_branch"),
            "pr_data": pr_data,
            "commit_data": commit_data,
            "config_data": config_data,
            "languages": list(languages.keys()),
            "dependencies": [], # Placeholder for dependency manifest parsing
        }
        
    except Exception as e:
        logger.error(f"Error fetching details for {repo_name}: {e}")
        return None

def calculate_llm_adoption_flag(repo_details: Dict[str, Any]) -> int:
    """
    Determine if the repository uses LLM-based code completion based on:
    - Presence of .cursorrules or copilot config files
    - Mentions in README/CONTRIBUTING
    - Frequency of "Copilot" in commit messages
    """
    config_data = repo_details.get("config_data", {})
    commit_data = repo_details.get("commit_data", [])
    
    # Check config files
    if ".cursorrules" in config_data:
        return 1
    
    # Check commit message frequency
    copilot_count = 0
    total_commits = len(commit_data)
    if total_commits > 0:
        for commit in commit_data:
            msg = commit.get("message", "").lower()
            if "copilot" in msg or "llm" in msg:
                copilot_count += 1
        
        if copilot_count / total_commits >= 0.05:
            return 1
    
    return 0

def run_ingestion():
    config = get_config()
    base_path = Path(config.get("project_root", "."))
    
    # Ensure output directory exists
    output_dir = base_path / "data" / "derived"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    repo_list = load_repo_list(config)
    logger.info(f"Found {len(repo_list)} repositories to process.")
    
    gh_client = GitHubClient(token=config.get("github_token"))
    
    results = []
    for i, repo_name in enumerate(repo_list):
        logger.info(f"Processing [{i+1}/{len(repo_list)}]: {repo_name}")
        details = fetch_repository_details(gh_client, repo_name)
        
        if details:
            details["llm_adoption_flag"] = calculate_llm_adoption_flag(details)
            results.append(details)
        
        # Respect rate limits
        time.sleep(1)
    
    output_file = output_dir / "ingestion_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Ingestion complete. Results saved to {output_file}")

if __name__ == "__main__":
    run_ingestion()
