from typing import Dict, Any, List, Optional
import math
import json
import re
from pathlib import Path

def calculate_iteration_count(commit_data: List[Dict[str, Any]]) -> int:
    """
    Calculate iteration count as total push events between PR open and merge.
    
    Args:
        commit_data: List of commit objects with push event timestamps
        
    Returns:
        Total count of push events (iterations)
    """
    if not commit_data:
        return 0
    
    # Count total push events (no exclusions per FR-002-UPDATED)
    return len(commit_data)

def calculate_avg_comment_length(review_data: List[Dict[str, Any]]) -> float:
    """
    Calculate average comment length in review threads.
    
    Args:
        review_data: List of review comment objects
        
    Returns:
        Average character length of comments
    """
    if not review_data:
        return 0.0
    
    total_length = sum(len(comment.get('body', '')) for comment in review_data)
    return total_length / len(review_data)

def calculate_review_thread_depth(review_data: List[Dict[str, Any]]) -> int:
    """
    Calculate maximum depth of review threads.
    
    Args:
        review_data: List of review comment objects
        
    Returns:
        Maximum thread depth observed
    """
    if not review_data:
        return 0
    
    max_depth = 0
    for comment in review_data:
        depth = comment.get('depth', 1)
        max_depth = max(max_depth, depth)
    
    return max_depth

def calculate_revert_frequency(commits: List[Dict[str, Any]]) -> float:
    """
    Calculate frequency of revert commits.
    
    Args:
        commits: List of commit objects
        
    Returns:
        Ratio of revert commits to total commits
    """
    if not commits:
        return 0.0
    
    revert_count = sum(
        1 for commit in commits 
        if 'revert' in commit.get('message', '').lower()
    )
    return revert_count / len(commits)

def calculate_diff_complexity_score(lines_added: int, lines_deleted: int, total_lines: int) -> float:
    """
    Calculate diff complexity score as per FR-008.
    
    Formula: (lines_added + lines_deleted) / total_lines if lines_deleted > 0 else 0
    
    Args:
        lines_added: Number of lines added in the diff
        lines_deleted: Number of lines deleted in the diff
        total_lines: Total lines in the file/commit
        
    Returns:
        Diff complexity score (0.0 if no deletions)
    """
    if lines_deleted <= 0 or total_lines == 0:
        return 0.0
    
    return (lines_added + lines_deleted) / total_lines

def is_ai_noise_flag(diff_complexity_score: float, commit_message: str) -> bool:
    """
    Flag if commit exhibits 'AI Noise' characteristics per FR-008.
    
    Flag 'AI Noise' if:
    - diff_complexity_score > 0.3 AND
    - commit message contains 'fix', 'hotfix', or 'patch'
    
    Args:
        diff_complexity_score: Calculated complexity score
        commit_message: The commit message string
        
    Returns:
        True if flagged as AI Noise, False otherwise
    """
    if diff_complexity_score <= 0.3:
        return False
    
    message_lower = commit_message.lower()
    noise_keywords = ['fix', 'hotfix', 'patch']
    
    return any(keyword in message_lower for keyword in noise_keywords)

def calculate_domain_complexity(languages: List[str], manifests: List[Dict[str, Any]]) -> int:
    """
    Calculate domain complexity as unique languages + dependency count from manifests.
    
    This metric combines:
    1. Number of unique programming languages used in the repository
    2. Total count of dependencies declared in manifest files
    
    Args:
        languages: List of programming languages detected in the repo
        manifests: List of manifest objects containing dependency information
        
    Returns:
        Domain complexity score (unique languages + dependency count)
    """
    # Count unique languages
    unique_languages = len(set(languages)) if languages else 0
    
    # Count dependencies from manifests
    # Manifests typically contain 'dependencies', 'packages', 'imports' lists
    dependency_count = 0
    for manifest in manifests:
        # Check common dependency keys in manifest files (package.json, requirements.txt, etc.)
        dep_keys = ['dependencies', 'devDependencies', 'packages', 'imports', 'modules']
        for key in dep_keys:
            if key in manifest:
                deps = manifest[key]
                if isinstance(deps, dict):
                    dependency_count += len(deps)
                elif isinstance(deps, list):
                    dependency_count += len(deps)
    
    return unique_languages + dependency_count

def process_review_metrics(review_data: List[Dict[str, Any]], commit_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process all review and commit metrics into a single result dictionary.
    
    Args:
        review_data: List of review comment objects
        commit_data: List of commit objects
        
    Returns:
        Dictionary containing all calculated metrics
    """
    return {
        'iteration_count': calculate_iteration_count(commit_data),
        'avg_comment_length': calculate_avg_comment_length(review_data),
        'review_thread_depth': calculate_review_thread_depth(review_data),
        'revert_frequency': calculate_revert_frequency(commit_data)
    }