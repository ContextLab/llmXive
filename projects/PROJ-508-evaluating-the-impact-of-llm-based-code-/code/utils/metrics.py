from typing import Dict, Any, List, Optional
import math
import json
import re
from pathlib import Path

def calculate_iteration_count(pr_data: List[Dict[str, Any]]) -> int:
    """
    Count TOTAL push events (commits) between PR open and merge.
    Per updated spec FR-002 (Task T007), NO exclusions for "Copilot" messages.
    """
    total_commits = 0
    for pr in pr_data:
        # Sum the 'commits' field from PR data which represents push events
        total_commits += pr.get("commits", 0)
    return total_commits

def calculate_avg_comment_length(pr_data: List[Dict[str, Any]]) -> float:
    """
    Calculate the average length of comments across all PRs.
    """
    if not pr_data:
        return 0.0
    
    total_chars = 0
    count = 0
    for pr in pr_data:
        # Assuming comment count is available, estimate length or use actual if available
        # If actual comment text is not in pr_data, we use a proxy or placeholder
        # For this implementation, we assume pr_data contains 'comments' count and we estimate length
        # In a real scenario, we would fetch comment bodies.
        # Here we simulate based on comment count * average length assumption or 0 if not available
        # To be robust, we return 0.0 if no comment data is structured
        if "comment_lengths" in pr:
            total_chars += sum(pr["comment_lengths"])
            count += len(pr["comment_lengths"])
        elif "comments" in pr:
            # Fallback: assume average comment length of 50 chars if only count is known
            # This is a limitation of the mock data structure
            total_chars += pr["comments"] * 50
            count += pr["comments"]
    
    return total_chars / count if count > 0 else 0.0

def calculate_review_thread_depth(pr_data: List[Dict[str, Any]]) -> float:
    """
    Calculate the average depth of review threads.
    """
    if not pr_data:
        return 0.0
    
    total_depth = 0
    count = 0
    for pr in pr_data:
        # Use review_comments as a proxy for thread depth if not explicitly provided
        # In a real implementation, we would traverse the thread tree
        if "review_comments" in pr:
            total_depth += pr["review_comments"]
            count += 1
    
    return total_depth / count if count > 0 else 0.0

def calculate_revert_frequency(commit_data: List[Dict[str, Any]]) -> float:
    """
    Calculate the frequency of revert commits.
    """
    if not commit_data:
        return 0.0
    
    revert_count = 0
    for commit in commit_data:
        msg = commit.get("message", "").lower()
        if "revert" in msg:
            revert_count += 1
    
    return revert_count / len(commit_data)

def calculate_diff_complexity_score(commit: Dict[str, Any]) -> float:
    """
    Calculate diff_complexity_score = (lines_added + lines_deleted) / total_lines
    if lines_deleted > 0 else 0.
    Per FR-008.
    """
    additions = commit.get("additions", 0)
    deletions = commit.get("deletions", 0)
    total = commit.get("total", 0)
    
    if total == 0:
        return 0.0
    
    if deletions > 0:
        return (additions + deletions) / total
    else:
        return 0.0

def is_ai_noise_flag(diff_complexity_score: float, commit_message: str) -> bool:
    """
    Flag 'AI Noise' if diff_complexity_score > 0.3 AND commit message contains
    'fix', 'hotfix', or 'patch'.
    Per FR-008.
    """
    if diff_complexity_score > 0.3:
        msg_lower = commit_message.lower()
        if "fix" in msg_lower or "hotfix" in msg_lower or "patch" in msg_lower:
            return True
    return False

def calculate_domain_complexity(languages: List[str], dependencies: List[str]) -> int:
    """
    Calculate domain complexity as unique languages + dependency count.
    """
    return len(set(languages)) + len(dependencies)

def process_review_metrics(
    iteration_count: int,
    avg_comment_length: float,
    review_thread_depth: float
) -> Dict[str, Any]:
    """
    Process and normalize review metrics.
    """
    # Apply any necessary normalization or validation here
    return {
        "iteration_count": iteration_count,
        "avg_comment_length": avg_comment_length,
        "review_thread_depth": review_thread_depth,
    }
