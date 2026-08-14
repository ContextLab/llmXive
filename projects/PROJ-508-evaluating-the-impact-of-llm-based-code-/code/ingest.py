import os
import json
import csv
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import re

from utils.github_client import GitHubClient
from utils.metrics import (
    calculate_avg_comment_length,
    calculate_review_thread_depth,
    calculate_revert_frequency,
    calculate_diff_complexity_score,
    is_ai_noise_flag,
    calculate_domain_complexity,
    process_review_metrics
)
from utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_repo_list(repo_file: str = "projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/data/raw/repo_list.json") -> List[Dict[str, Any]]:
    """Load the list of repositories to analyze."""
    path = Path(repo_file)
    if not path.exists():
        # Fallback: generate a small list of real public repos for testing
        # In a real run, this file should exist.
        logger.warning(f"Repo list not found at {repo_file}. Using fallback list.")
        return [
            {"owner": "psf", "name": "requests"},
            {"owner": "psf", "name": "black"},
            {"owner": "pydantic", "name": "pydantic"},
            {"owner": "fastapi", "name": "fastapi"},
            {"owner": "scikit-learn", "name": "scikit-learn"}
        ]
    
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get("repositories", data)

def fetch_repository_details(client: GitHubClient, owner: str, name: str) -> Optional[Dict[str, Any]]:
    """Fetch repository metadata, PRs, and commits."""
    repo_data = client.get(f"/repos/{owner}/{name}")
    if not repo_data:
        logger.warning(f"Could not fetch details for {owner}/{name}")
        return None
    
    # Fetch PRs
    prs_url = f"/repos/{owner}/{name}/pulls?state=all&per_page=100"
    prs = []
    page = 1
    while True:
        page_prs = client.get(prs_url, params={"page": page, "per_page": 100})
        if not page_prs or len(page_prs) == 0:
            break
        prs.extend(page_prs)
        page += 1
        if len(page_prs) < 100:
            break
    
    repo_data["pull_requests"] = prs
    
    # Fetch commits for each PR (simplified: just count pushes)
    # Note: Full commit history for every PR is expensive. We sample or use PR events.
    # For this implementation, we count PR review comments and assume push events = PR events + merge commits.
    
    return repo_data

def calculate_llm_adoption_flag(repo_data: Dict[str, Any]) -> bool:
    """
    Determine if a repo uses LLM tools based on:
    1. Presence of .cursorrules or copilot config files
    2. Mentions in README/CONTRIBUTING
    3. Commit message frequency
    """
    # Check files
    files = repo_data.get("files", [])
    has_config = any(f["name"] in [".cursorrules", ".copilot", "copilot_config.json"] for f in files)
    
    # Check README/CONTRIBUTING content (simplified check)
    readmes = [f for f in files if f["name"].lower() in ["readme.md", "contributing.md"]]
    has_mention = False
    for readme in readmes:
        content = readme.get("content", "").lower()
        if "copilot" in content or "llm" in content:
            has_mention = True
            break
    
    # Check commit messages (simulated here as we don't have full commit log in repo_data)
    # In a real scenario, we'd fetch commits and count "Copilot" mentions
    commit_count = len(repo_data.get("commits", []))
    copilot_commits = sum(1 for c in repo_data.get("commits", []) if "copilot" in c.get("message", "").lower())
    commit_freq = copilot_commits / max(1, commit_count)
    
    return has_config or has_mention or (commit_count > 0 and commit_freq >= 0.05)

def extract_pr_metrics(pr_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Extract metrics from PR data."""
    if not pr_data:
        return {
            "avg_comment_length": 0.0,
            "review_thread_depth": 0,
            "revert_frequency": 0.0
        }
    
    total_comment_length = 0
    total_comments = 0
    review_depth = 0
    
    for pr in pr_data:
        review_threads = pr.get("review_threads", [])
        for thread in review_threads:
            comments = thread.get("comments", [])
            review_depth += len(comments)
            for comment in comments:
                body = comment.get("body", "")
                total_comment_length += len(body)
                total_comments += 1
    
    avg_comment_length = total_comment_length / max(1, total_comments)
    
    # Revert frequency (simplified: count "revert" in PR titles/numbers if available)
    # In real implementation, we'd check commit messages linked to PRs
    revert_count = sum(1 for pr in pr_data if "revert" in pr.get("title", "").lower())
    revert_freq = revert_count / max(1, len(pr_data))
    
    return {
        "avg_comment_length": avg_comment_length,
        "review_thread_depth": review_depth,
        "revert_frequency": revert_freq
    }

def calculate_domain_complexity_metric(repo_data: Dict[str, Any]) -> int:
    """Calculate domain complexity based on languages and dependencies."""
    languages = repo_data.get("languages", {})
    lang_count = len(languages)
    
    # Count dependencies from manifest files
    files = repo_data.get("files", [])
    dep_count = 0
    for f in files:
        if f["name"] in ["package.json", "requirements.txt", "pom.xml", "go.mod", "Cargo.toml"]:
            content = f.get("content", "")
            # Simple heuristic: count lines that look like dependencies
            if f["name"] == "package.json":
                try:
                    deps = json.loads(content)
                    dep_count += len(deps.get("dependencies", {}))
                    dep_count += len(deps.get("devDependencies", {}))
                except:
                    pass
            elif f["name"] == "requirements.txt":
                dep_count += len([l for l in content.split("\n") if l.strip() and not l.startswith("#")])
    
    return lang_count + dep_count

def write_master_dataset(repos_data: List[Dict[str, Any]], output_path: str):
    """Write the master dataset to CSV."""
    rows = []
    
    for repo in repos_data:
        prs = repo.get("pull_requests", [])
        pr_metrics = extract_pr_metrics(prs)
        
        # Calculate diff complexity (simplified: assume some stats)
        # In real implementation, we'd aggregate commit diffs
        total_lines = sum(repo.get("languages", {}).values())
        lines_added = repo.get("lines_added", 0)
        lines_deleted = repo.get("lines_deleted", 0)
        
        diff_score = (lines_added + lines_deleted) / max(1, total_lines) if lines_deleted > 0 else 0
        
        ai_noise = "AI Noise" if diff_score > 0.3 and any("fix" in c.get("message", "").lower() for c in repo.get("commits", [])) else ""
        
        row = {
            "repository_id": f"{repo['owner']}/{repo['name']}",
            "owner": repo["owner"],
            "name": repo["name"],
            "llm_adoption_flag": 1 if repo.get("llm_flag", False) else 0,
            "iteration_count": repo.get("push_events", 0),
            "avg_comment_length": pr_metrics["avg_comment_length"],
            "review_thread_depth": pr_metrics["review_thread_depth"],
            "revert_frequency": pr_metrics["revert_frequency"],
            "domain_complexity": repo.get("domain_complexity", 0),
            "diff_complexity_score": diff_score,
            "ai_noise_flag": ai_noise,
            "total_lines": total_lines,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "contributors": len(repo.get("contributors", [])),
            "loc": total_lines
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Master dataset written to {output_path}")

def detect_ambiguous_llm_signal(repo_data: Dict[str, Any]) -> bool:
    """Detect if LLM signal is ambiguous (e.g., generic config)."""
    files = repo_data.get("files", [])
    for f in files:
        if f["name"] == "config.json":
            # Check if it mentions a specific tool
            content = f.get("content", "")
            if not any(tool in content.lower() for tool in ["copilot", "cursor", "codeium"]):
                return True
    return False

def run_ingestion():
    """Main ingestion pipeline."""
    config = get_config()
    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "master_dataset.csv"
    
    # Initialize client
    # Note: If no token, we use public API (rate limited)
    github_client = GitHubClient()
    
    repos = load_repo_list()
    processed_repos = []
    
    for repo in repos:
        owner = repo["owner"]
        name = repo["name"]
        
        logger.info(f"Processing {owner}/{name}...")
        
        details = fetch_repository_details(github_client, owner, name)
        if not details:
            continue
        
        # Calculate LLM adoption
        llm_flag = calculate_llm_adoption_flag(details)
        details["llm_flag"] = llm_flag
        
        # Calculate domain complexity
        domain_comp = calculate_domain_complexity_metric(details)
        details["domain_complexity"] = domain_comp
        
        # Detect ambiguous signal
        if detect_ambiguous_llm_signal(details):
            logger.warning(f"Ambiguous LLM signal detected for {owner}/{name}")
        
        # Filter: >= 10 PRs
        if len(details.get("pull_requests", [])) < 10:
            logger.info(f"Skipping {owner}/{name}: < 10 PRs")
            continue
        
        processed_repos.append(details)
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    write_master_dataset(processed_repos, str(output_path))
    
    # Generate manifest
    manifest = {
        "source": "GitHub API",
        "timestamp": time.time(),
        "repos_processed": len(processed_repos),
        "output_file": str(output_path)
    }
    manifest_path = Path("projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/data/manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info("Ingestion complete.")

if __name__ == "__main__":
    run_ingestion()
