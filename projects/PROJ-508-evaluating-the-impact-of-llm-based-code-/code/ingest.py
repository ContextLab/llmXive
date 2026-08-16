import os
import json
import csv
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import get_config
from utils.github_client import GitHubClient
from utils.metrics import (
    calculate_avg_comment_length,
    calculate_review_thread_depth,
    calculate_revert_frequency,
    calculate_diff_complexity_score,
    is_ai_noise_flag,
    calculate_domain_complexity
)
from utils.data_validation import validate_csv_schema

# Import generate_manifest from the same module
from generate_manifest import generate_manifest, write_manifest

def load_repo_list(repo_file: Path) -> List[Dict[str, str]]:
    """Load repository list from a JSON file."""
    if not repo_file.exists():
        logging.warning(f"Repository list file not found: {repo_file}")
        return []
    
    with open(repo_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_repository_details(client: GitHubClient, repo: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Fetch detailed repository data including PRs, commits, and config files."""
    owner = repo.get("owner")
    name = repo.get("name")
    
    if not owner or not name:
        logging.error(f"Invalid repository entry: {repo}")
        return None
    
    try:
        # Fetch repo metadata
        repo_data = client.get_repo(owner, name)
        if not repo_data:
            return None
        
        # Fetch PRs
        pulls = client.get_pulls(owner, name, state="all")
        
        # Fetch commits for each PR
        pr_details = []
        for pull in pulls:
            pr_num = pull.get("number")
            commits = client.get_commits(owner, name, sha=pull.get("merge_commit_sha"))
            
            # Fetch review threads
            review_threads = client.get_review_comments(owner, name, pull_number=pr_num)
            
            pr_details.append({
                "number": pr_num,
                "state": pull.get("state"),
                "merged": pull.get("merged_at") is not None,
                "created_at": pull.get("created_at"),
                "merged_at": pull.get("merged_at"),
                "commits": commits,
                "review_threads": review_threads
            })
        
        # Fetch config files for LLM adoption detection
        config_files = {}
        config_paths = [".cursorrules", "copilot.yaml", "copilot.yml", "config.json"]
        for path in config_paths:
            content = client.get_file_content(owner, name, path)
            if content:
                config_files[path] = content
        
        # Check README and CONTRIBUTING
        readme = client.get_file_content(owner, name, "README.md")
        contributing = client.get_file_content(owner, name, "CONTRIBUTING.md")
        
        return {
            "id": f"{owner}/{name}",
            "owner": owner,
            "name": name,
            "repo_data": repo_data,
            "pulls": pr_details,
            "config_files": config_files,
            "readme": readme,
            "contributing": contributing
        }
    except Exception as e:
        logging.error(f"Failed to fetch details for {owner}/{name}: {e}")
        return None

def calculate_llm_adoption_flag(repo_data: Dict[str, Any]) -> bool:
    """
    Determine if a repository uses LLM tools based on:
    1. Presence of .cursorrules or copilot config files
    2. Mentions in README/CONTRIBUTING (first 2048 chars)
    3. Commit message frequency >= 5%
    """
    config_files = repo_data.get("config_files", {})
    readme = repo_data.get("readme", "")
    contributing = repo_data.get("contributing", "")
    pulls = repo_data.get("pulls", [])
    
    # Check config files
    if ".cursorrules" in config_files or "copilot.yaml" in config_files or "copilot.yml" in config_files:
        return True
    
    # Check README/CONTRIBUTING (first 2048 chars)
    combined_text = (readme or "")[:2048] + (contributing or "")[:2048]
    if "copilot" in combined_text.lower() or "llm" in combined_text.lower():
        return True
    
    # Check commit message frequency
    total_commits = 0
    copilot_commits = 0
    
    for pr in pulls:
        for commit in pr.get("commits", []):
            total_commits += 1
            message = commit.get("message", "").lower()
            if "copilot" in message or "llm" in message:
                copilot_commits += 1
    
    if total_commits > 0 and (copilot_commits / total_commits) >= 0.05:
        return True
    
    return False

def detect_ambiguous_llm_signal(repo_data: Dict[str, Any]) -> bool:
    """Detect if LLM signal is ambiguous (e.g., generic config without tool naming)."""
    config_files = repo_data.get("config_files", {})
    
    for path, content in config_files.items():
        if path == "config.json":
            try:
                config = json.loads(content)
                # Check if it's generic without specific tool naming
                if "tools" not in config and "llm" not in config and "copilot" not in config:
                    return True
            except json.JSONDecodeError:
                pass
    
    return False

def extract_pr_metrics(pr_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Extract PR-level metrics:
    - avg_comment_length: Mean length of comment bodies
    - review_thread_depth: Count of comments per PR
    - revert_frequency: Count of commits with "revert" in message
    """
    total_comment_length = 0
    total_comments = 0
    total_reverts = 0
    
    for pr in pr_data:
        review_threads = pr.get("review_threads", [])
        for thread in review_threads:
            comments = thread.get("comments", [])
            for comment in comments:
                body = comment.get("body", "")
                total_comment_length += len(body)
                total_comments += 1
        
        commits = pr.get("commits", [])
        for commit in commits:
            message = commit.get("message", "").lower()
            if "revert" in message:
                total_reverts += 1
    
    avg_comment_length = total_comment_length / total_comments if total_comments > 0 else 0.0
    review_thread_depth = total_comments
    
    return {
        "avg_comment_length": avg_comment_length,
        "review_thread_depth": review_thread_depth,
        "revert_frequency": total_reverts
    }

def calculate_domain_complexity_metric(repo_data: Dict[str, Any]) -> int:
    """
    Calculate domain complexity:
    Sum of unique programming languages + count of dependencies in manifest files.
    """
    # This would normally parse manifest files to count dependencies
    # For now, we'll use a placeholder based on repo metadata
    languages = repo_data.get("repo_data", {}).get("languages", {})
    lang_count = len(languages) if languages else 0
    
    # Count dependencies from manifest files (simplified)
    config_files = repo_data.get("config_files", {})
    dep_count = 0
    
    for path, content in config_files.items():
        if path == "package.json":
            try:
                pkg = json.loads(content)
                deps = pkg.get("dependencies", {})
                dev_deps = pkg.get("devDependencies", {})
                dep_count += len(deps) + len(dev_deps)
            except json.JSONDecodeError:
                pass
        elif path == "requirements.txt":
            lines = content.split("\n")
            dep_count += sum(1 for line in lines if line.strip() and not line.startswith("#"))
        elif path == "pom.xml":
            # Simplified count
            dep_count += content.count("<dependency>")
    
    return lang_count + dep_count

def write_master_dataset(repos: List[Dict[str, Any]], output_path: Path) -> None:
    """Write the master dataset to a CSV file."""
    if not repos:
        logging.warning("No repository data to write.")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "repository_id", "llm_adoption_flag", "iteration_count",
        "avg_comment_length", "review_thread_depth", "revert_frequency",
        "loc", "contributors", "domain_complexity", "diff_complexity_score",
        "ai_noise_flag"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for repo in repos:
            # Calculate metrics
            llm_flag = repo.get("llm_adoption_flag", False)
            pulls = repo.get("pulls", [])
            
            # Iteration count: TOTAL push events between PR open and merge
            iteration_count = 0
            for pr in pulls:
                if pr.get("merged"):
                    iteration_count += 1  # Simplified: count merged PRs as iterations
            
            # PR metrics
            pr_metrics = extract_pr_metrics(pulls)
            
            # LOC and contributors
            repo_data = repo.get("repo_data", {})
            loc = repo_data.get("size", 0)
            contributors = repo_data.get("contributors_count", 0)
            
            # Domain complexity
            domain_complexity = calculate_domain_complexity_metric(repo)
            
            # Diff complexity and AI noise (simplified for ingestion)
            # In a real scenario, this would be calculated per commit
            # Here we use a placeholder based on repo characteristics
            diff_complexity = 0.1  # Placeholder
            ai_noise = diff_complexity > 0.3 and False  # Placeholder logic
            
            row = {
                "repository_id": repo.get("id"),
                "llm_adoption_flag": llm_flag,
                "iteration_count": iteration_count,
                "avg_comment_length": pr_metrics["avg_comment_length"],
                "review_thread_depth": pr_metrics["review_thread_depth"],
                "revert_frequency": pr_metrics["revert_frequency"],
                "loc": loc,
                "contributors": contributors,
                "domain_complexity": domain_complexity,
                "diff_complexity_score": diff_complexity,
                "ai_noise_flag": ai_noise
            }
            writer.writerow(row)
    
    logging.info(f"Master dataset written to {output_path}")

def generate_manifest_for_ingestion(repos: List[Dict[str, Any]], output_path: Path, data_dir: Path) -> None:
    """Generate the manifest.json file for the ingestion pipeline."""
    manifest = generate_manifest(output_path, data_dir)
    
    # Add ingestion-specific details
    manifest["ingestion_details"] = {
        "total_repositories_processed": len(repos),
        "successful_fetches": sum(1 for r in repos if r.get("pulls") is not None),
        "failed_fetches": sum(1 for r in repos if r.get("pulls") is None),
        "llm_adoption_count": sum(1 for r in repos if r.get("llm_adoption_flag", False)),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    write_manifest(manifest, output_path)

def run_ingestion(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run the full ingestion pipeline."""
    logging.info("Starting ingestion pipeline")
    
    repo_file = Path(config.get("repo_list_path", "data/raw/repo_list.json"))
    output_path = Path(config.get("output_path", "data/derived/master_dataset.csv"))
    manifest_path = Path(config.get("manifest_path", "data/manifest.json"))
    
    # Load repository list
    repos = load_repo_list(repo_file)
    if not repos:
        logging.error("No repositories found in the list.")
        return []
    
    # Initialize GitHub client
    client = GitHubClient()
    
    processed_repos = []
    for repo in repos:
        repo_data = fetch_repository_details(client, repo)
        if repo_data:
            repo_data["llm_adoption_flag"] = calculate_llm_adoption_flag(repo_data)
            if detect_ambiguous_llm_signal(repo_data):
                logging.warning(f"Ambiguous LLM signal detected for {repo_data['id']}")
            processed_repos.append(repo_data)
    
    # Write master dataset
    write_master_dataset(processed_repos, output_path)
    
    # Generate manifest
    generate_manifest_for_ingestion(processed_repos, manifest_path, Path("data"))
    
    logging.info("Ingestion pipeline completed.")
    return processed_repos

def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = get_config()
    run_ingestion(config)

if __name__ == "__main__":
    main()
