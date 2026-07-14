from typing import Dict, Any, List, Optional
import math
import json
import re
from pathlib import Path

def calculate_iteration_count(pr_data: Dict[str, Any]) -> int:
    """
    Calculate the total number of push events (iterations) between PR open and merge.
    
    Per spec FR-002 (updated in T007): Count TOTAL push events.
    NO exclusions based on commit message content (e.g., 'Copilot').
    
    Args:
        pr_data: Dictionary containing PR metadata, including a list of commits.
    
    Returns:
        Integer count of commits/push events.
    """
    commits = pr_data.get("commits", [])
    return len(commits)

def calculate_avg_comment_length(pr_data: Dict[str, Any]) -> float:
    """
    Calculate the average length of comments in review threads.
    
    Args:
        pr_data: Dictionary containing PR metadata, including review comments.
    
    Returns:
        Float representing the average character length of comments.
    """
    comments = pr_data.get("review_comments", [])
    if not comments:
        return 0.0
    
    total_length = sum(len(c.get("body", "")) for c in comments)
    return total_length / len(comments)

def calculate_review_thread_depth(pr_data: Dict[str, Any]) -> float:
    """
    Calculate the average depth of review threads.
    
    Args:
        pr_data: Dictionary containing PR metadata.
    
    Returns:
        Float representing the average depth of review conversations.
    """
    threads = pr_data.get("review_threads", [])
    if not threads:
        return 0.0
    
    # Assuming 'depth' is a count of replies + 1 (original comment)
    depths = [t.get("reply_count", 0) + 1 for t in threads]
    return sum(depths) / len(depths)

def calculate_revert_frequency(repo_data: Dict[str, Any]) -> float:
    """
    Calculate the frequency of reverts in the repository history.
    
    Args:
        repo_data: Dictionary containing repository commit history.
    
    Returns:
        Float representing the ratio of revert commits to total commits.
    """
    commits = repo_data.get("commits", [])
    if not commits:
        return 0.0
    
    revert_count = 0
    revert_patterns = [
        r"revert\s+",
        r"reverted\s+",
        r"revert\s+commit"
    ]
    
    for commit in commits:
        msg = commit.get("message", "").lower()
        if any(re.search(pattern, msg) for pattern in revert_patterns):
            revert_count += 1
    
    return revert_count / len(commits)

def calculate_diff_complexity_score(commit_data: Dict[str, Any]) -> float:
    """
    Calculate the diff complexity score for a commit.
    
    Formula: (lines_added + lines_deleted) / total_lines if lines_deleted > 0 else 0.
    
    Args:
        commit_data: Dictionary containing commit diff statistics.
    
    Returns:
        Float representing the complexity score.
    """
    added = commit_data.get("lines_added", 0)
    deleted = commit_data.get("lines_deleted", 0)
    total = commit_data.get("total_lines", 0)
    
    if total == 0:
        return 0.0
    
    if deleted > 0:
        return (added + deleted) / total
    return 0.0

def is_ai_noise_flag(commit_data: Dict[str, Any]) -> bool:
    """
    Determine if a commit should be flagged as 'AI Noise'.
    
    Logic: Flag if `diff_complexity_score` > 0.3 AND commit message contains
    'fix', 'hotfix', or 'patch'.
    
    Args:
        commit_data: Dictionary containing commit diff stats and message.
    
    Returns:
        Boolean indicating if the AI Noise flag is set.
    """
    score = calculate_diff_complexity_score(commit_data)
    if score <= 0.3:
        return False
    
    message = commit_data.get("message", "").lower()
    noise_keywords = ["fix", "hotfix", "patch"]
    
    return any(keyword in message for keyword in noise_keywords)

def calculate_domain_complexity(repo_data: Dict[str, Any]) -> int:
    """
    Calculate domain complexity based on unique languages and dependency count.
    
    Args:
        repo_data: Dictionary containing repository metadata.
    
    Returns:
        Integer score representing domain complexity.
    """
    languages = repo_data.get("languages", [])
    dependencies = repo_data.get("dependencies", [])
    
    # Simple heuristic: unique languages + number of dependencies
    return len(set(languages)) + len(dependencies)

def process_review_metrics(pr_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Process all review-related metrics for a PR.
    
    Args:
        pr_data: Dictionary containing PR metadata.
    
    Returns:
        Dictionary with calculated metrics.
    """
    return {
        "avg_comment_length": calculate_avg_comment_length(pr_data),
        "review_thread_depth": calculate_review_thread_depth(pr_data),
        "iteration_count": calculate_iteration_count(pr_data)
    }