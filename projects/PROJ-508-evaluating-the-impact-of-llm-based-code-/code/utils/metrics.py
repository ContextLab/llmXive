from typing import Dict, Any, List, Optional
import math
import json
import re
from pathlib import Path

def calculate_avg_comment_length(pr_data: Dict[str, Any]) -> float:
    """
    Calculates the average length of comment bodies in PR review threads.
    Source: pr_data['review_threads']['comments']['body']
    """
    comments = pr_data.get('review_threads', {}).get('comments', [])
    if not comments:
        return 0.0
    
    total_length = sum(len(c.get('body', '')) for c in comments)
    return total_length / len(comments)

def calculate_review_thread_depth(pr_data: Dict[str, Any]) -> int:
    """
    Count of comments per PR (source: review_threads count).
    """
    return len(pr_data.get('review_threads', {}).get('comments', []))

def calculate_revert_frequency(pr_data: Dict[str, Any]) -> int:
    """
    Count of commits with "revert" in message (case-insensitive).
    Source: pr_data['commits'] or pr_data['reverts']
    """
    commits = pr_data.get('commits', [])
    if not commits:
        # Fallback if commits are at root level of repo_data (handled in caller)
        # This function expects pr_data, so we assume commits are inside.
        return 0
    
    count = 0
    for commit in commits:
        msg = commit.get('message', '')
        if re.search(r'\brevert\b', msg, re.IGNORECASE):
            count += 1
    return count

def calculate_diff_complexity_score(commit_data: Dict[str, Any]) -> float:
    """
    Formula: (lines_added + lines_deleted) / total_lines if lines_deleted > 0 else 0.
    """
    added = commit_data.get('lines_added', 0)
    deleted = commit_data.get('lines_deleted', 0)
    total_lines = commit_data.get('total_lines', added + deleted)
    
    if total_lines == 0:
        total_lines = 1 # Avoid division by zero
    
    if deleted > 0:
        return (added + deleted) / total_lines
    return 0.0

def is_ai_noise_flag(commit_data: Dict[str, Any]) -> bool:
    """
    Flag 'AI Noise' if diff_complexity_score > 0.3 AND commit message contains 'fix', 'hotfix', or 'patch'.
    """
    score = calculate_diff_complexity_score(commit_data)
    msg = commit_data.get('message', '').lower()
    return score > 0.3 and any(kw in msg for kw in ['fix', 'hotfix', 'patch'])

def calculate_domain_complexity(repo_data: Dict[str, Any]) -> int:
    """
    Sum of unique programming languages + count of dependencies found in manifest files.
    """
    languages = set(repo_data.get('languages', {}).keys())
    lang_count = len(languages)
    
    # Count dependencies from manifests
    dep_count = 0
    manifests = repo_data.get('manifests', [])
    for manifest in manifests:
        if isinstance(manifest, dict):
            # Example: {'package.json': {'dependencies': {...}}}
            for key, val in manifest.items():
                if isinstance(val, dict):
                    dep_count += len(val)
        elif isinstance(manifest, list):
            dep_count += len(manifest)
    
    return lang_count + dep_count

def process_review_metrics(pr_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Processes a list of PR data to calculate aggregate metrics.
    """
    if not pr_data:
        return {
            'avg_comment_length': 0.0,
            'review_thread_depth': 0,
            'revert_frequency': 0
        }
    
    total_comment_len = 0
    total_comments = 0
    total_reverts = 0
    
    for pr in pr_data:
        comments = pr.get('review_threads', {}).get('comments', [])
        total_comments += len(comments)
        total_comment_len += sum(len(c.get('body', '')) for c in comments)
        
        commits = pr.get('commits', [])
        for c in commits:
            if re.search(r'\brevert\b', c.get('message', ''), re.IGNORECASE):
                total_reverts += 1
    
    avg_len = total_comment_len / total_comments if total_comments > 0 else 0.0
    
    return {
        'avg_comment_length': avg_len,
        'review_thread_depth': total_comments,
        'revert_frequency': total_reverts
    }
