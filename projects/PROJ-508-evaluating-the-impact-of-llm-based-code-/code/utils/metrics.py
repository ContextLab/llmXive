from typing import Dict, Any, List, Optional
import math
import json
import re
from pathlib import Path

def calculate_avg_comment_length(comments: List[Dict[str, Any]]) -> float:
    """Calculate the average length of comment bodies."""
    if not comments:
        return 0.0
    total_length = sum(len(c.get('body', '')) for c in comments)
    return total_length / len(comments)

def calculate_review_thread_depth(comments: List[Dict[str, Any]]) -> int:
    """Calculate the number of comments in a thread."""
    return len(comments)

def calculate_revert_frequency(commits: List[Dict[str, Any]]) -> float:
    """Calculate the frequency of revert commits."""
    if not commits:
        return 0.0
    revert_pattern = re.compile(r'\brevert\b', re.IGNORECASE)
    revert_count = sum(1 for c in commits if revert_pattern.search(c.get('commit', {}).get('message', '')))
    return revert_count / len(commits)

def calculate_diff_complexity_score(lines_added: int, lines_deleted: int, total_lines: int) -> float:
    """
    Calculate diff complexity score.
    Formula: (lines_added + lines_deleted) / max(1, total_lines) if lines_deleted > 0 else 0.
    """
    if lines_deleted <= 0:
        return 0.0
    return (lines_added + lines_deleted) / max(1, total_lines)

def is_ai_noise_flag(diff_complexity_score: float, commit_message: str) -> bool:
    """
    Flag 'AI Noise' if diff_complexity_score > 0.3 AND commit message contains 'fix', 'hotfix', or 'patch'.
    """
    if diff_complexity_score <= 0.3:
        return False
    pattern = re.compile(r'\b(fix|hotfix|patch)\b', re.IGNORECASE)
    return bool(pattern.search(commit_message))

def calculate_domain_complexity(languages: List[str], dependencies: int) -> int:
    """Calculate domain complexity as sum of unique languages and dependencies."""
    return len(languages) + dependencies

def process_review_metrics(reviews: List[Dict[str, Any]], comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process review and comment data into metrics."""
    all_comments = reviews + comments
    return {
        "avg_comment_length": calculate_avg_comment_length(all_comments),
        "review_thread_depth": calculate_review_thread_depth(all_comments)
    }
