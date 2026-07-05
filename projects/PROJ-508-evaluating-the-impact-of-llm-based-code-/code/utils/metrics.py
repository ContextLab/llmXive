from typing import Dict, Any, List, Optional
import math
import json
import re
from pathlib import Path

def calculate_iteration_count(pr_data: Dict[str, Any]) -> int:
    """
    Calculate iteration count based on total push events between PR open and merge.
    [FR-002-UPDATED]: Count TOTAL push events (no exclusions).
    
    Args:
        pr_data: Dictionary containing PR details including commits and events.
                
    Returns:
        Integer count of push events.
    """
    # Assuming pr_data contains a list of push events or commits
    # Logic depends on exact structure from GitHub API, but typically:
    # pr_data['commits'] or pr_data['push_events']
    if 'commits' in pr_data:
        return len(pr_data['commits'])
    elif 'push_events' in pr_data:
        return len(pr_data['push_events'])
    return 0

def calculate_avg_comment_length(review_threads: List[Dict[str, Any]]) -> float:
    """
    Calculate average comment length across all review threads.
    
    Args:
        review_threads: List of review thread dictionaries.
        
    Returns:
        Average comment length in characters.
    """
    if not review_threads:
        return 0.0
    
    total_length = 0
    count = 0
    
    for thread in review_threads:
        if 'comments' in thread:
            for comment in thread['comments']:
                if 'body' in comment:
                    total_length += len(comment['body'])
                    count += 1
    
    return total_length / count if count > 0 else 0.0

def calculate_review_thread_depth(review_threads: List[Dict[str, Any]]) -> float:
    """
    Calculate average depth of review threads (number of comments per thread).
    
    Args:
        review_threads: List of review thread dictionaries.
        
    Returns:
        Average number of comments per thread.
    """
    if not review_threads:
        return 0.0
    
    total_comments = sum(len(thread.get('comments', [])) for thread in review_threads)
    return total_comments / len(review_threads)

def calculate_revert_frequency(commits: List[Dict[str, Any]]) -> float:
    """
    Calculate the frequency of revert commits.
    
    Args:
        commits: List of commit dictionaries.
        
    Returns:
        Ratio of revert commits to total commits.
    """
    if not commits:
        return 0.0
    
    revert_count = 0
    for commit in commits:
        message = commit.get('message', '').lower()
        if 'revert' in message:
            revert_count += 1
    
    return revert_count / len(commits)

def calculate_diff_complexity_score(lines_added: int, lines_deleted: int, total_lines: int) -> float:
    """
    Calculate diff complexity score as per FR-008.
    Formula: (lines_added + lines_deleted) / total_lines if lines_deleted > 0 else 0.
    
    Args:
        lines_added: Number of lines added in the diff.
        lines_deleted: Number of lines deleted in the diff.
        total_lines: Total lines in the file or repository context.
        
    Returns:
        Float complexity score.
    """
    if total_lines == 0:
        return 0.0
    if lines_deleted > 0:
        return (lines_added + lines_deleted) / total_lines
    return 0.0

def is_ai_noise_flag(diff_complexity_score: float, commit_message: str) -> bool:
    """
    Flag 'AI Noise' if diff_complexity_score > 0.3 AND commit message contains 
    'fix', 'hotfix', or 'patch'.
    
    Args:
        diff_complexity_score: Calculated complexity score.
        commit_message: The commit message string.
        
    Returns:
        Boolean indicating if AI Noise flag should be set.
    """
    if diff_complexity_score > 0.3:
        message_lower = commit_message.lower()
        if any(keyword in message_lower for keyword in ['fix', 'hotfix', 'patch']):
            return True
    return False

def calculate_domain_complexity(languages: List[str], manifests: List[Dict[str, Any]]) -> int:
    """
    Calculate domain complexity as unique languages + dependency count from manifests.
    
    Args:
        languages: List of programming languages used in the repository.
        manifests: List of dependency manifest dictionaries (e.g., package.json, requirements.txt).
                
    Returns:
        Integer domain complexity score.
    """
    unique_languages = len(set(languages))
    
    dependency_count = 0
    for manifest in manifests:
        # Handle different manifest types
        if 'dependencies' in manifest:
            dependency_count += len(manifest['dependencies'])
        if 'devDependencies' in manifest:
            dependency_count += len(manifest['devDependencies'])
        if 'requires' in manifest:
            dependency_count += len(manifest['requires'])
        # Add other manifest keys as needed
        
    return unique_languages + dependency_count

def process_review_metrics(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process all review-related metrics for a PR.
    
    Args:
        pr_data: Dictionary containing PR details.
                
    Returns:
        Dictionary with calculated metrics.
    """
    review_threads = pr_data.get('review_threads', [])
    commits = pr_data.get('commits', [])
    
    return {
        'avg_comment_length': calculate_avg_comment_length(review_threads),
        'review_thread_depth': calculate_review_thread_depth(review_threads),
        'revert_frequency': calculate_revert_frequency(commits),
        'iteration_count': calculate_iteration_count(pr_data)
    }
