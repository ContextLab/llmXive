import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import subprocess
import json
import pandas as pd
import textstat
from textblob import TextBlob
import radon.complexity as cc
from radon.visitors import ComplexityVisitor
import ast

logger = logging.getLogger(__name__)

def calc_complexity_for_file(file_path: str) -> float:
    """
    Calculate cyclomatic complexity for a single Python file.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        Average cyclomatic complexity of functions in the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        visitor = ComplexityVisitor.from_code(source)
        if not visitor.functions:
            return 0.0
        complexities = [func.complexity for func in visitor.functions]
        return sum(complexities) / len(complexities)
    except Exception as e:
        logger.warning(f"Could not calculate complexity for {file_path}: {e}")
        return 0.0

def calc_complexity(repo_path: str) -> float:
    """
    Calculate average cyclomatic complexity for a repository.
    
    Args:
        repo_path: Path to the repository root.
        
    Returns:
        Average complexity across all Python files.
    """
    py_files = list(Path(repo_path).rglob("*.py"))
    if not py_files:
        return 0.0
        
    complexities = []
    for py_file in py_files:
        c = calc_complexity_for_file(str(py_file))
        if c > 0:
            complexities.append(c)
            
    return sum(complexities) / len(complexities) if complexities else 0.0

def get_complexity_breakdown(repo_path: str) -> Dict[str, float]:
    """
    Get a breakdown of complexity metrics for a repository.
    
    Args:
        repo_path: Path to the repository root.
        
    Returns:
        Dictionary with complexity statistics.
    """
    py_files = list(Path(repo_path).rglob("*.py"))
    if not py_files:
        return {"avg": 0.0, "max": 0.0, "count": 0}
        
    complexities = []
    for py_file in py_files:
        c = calc_complexity_for_file(str(py_file))
        if c > 0:
            complexities.append(c)
            
    if not complexities:
        return {"avg": 0.0, "max": 0.0, "count": 0}
        
    return {
        "avg": sum(complexities) / len(complexities),
        "max": max(complexities),
        "count": len(complexities)
    }

def calc_readability(comments: List[str]) -> float:
    """
    Calculate readability score of comments using Flesch-Kincaid Grade.
    
    Args:
        comments: List of comment strings.
        
    Returns:
        Average readability score. Returns 0.0 if empty.
    """
    if not comments:
        logger.warning("Empty comment set for readability calculation. Returning 0.0.")
        return 0.0
        
    scores = []
    for comment in comments:
        if comment.strip():
            try:
                # textstat expects a string
                score = textstat.flesch_reading_ease(comment)
                scores.append(score)
            except Exception as e:
                logger.warning(f"Error calculating readability for comment: {e}")
                
    return sum(scores) / len(scores) if scores else 0.0

def calc_sentiment(comments: List[str]) -> float:
    """
    Calculate sentiment polarity of comments using TextBlob.
    
    Args:
        comments: List of comment strings.
        
    Returns:
        Average sentiment polarity (-1 to 1). Returns 0.0 if empty.
    """
    if not comments:
        logger.warning("Empty comment set for sentiment calculation. Returning 0.0.")
        return 0.0
        
    polarities = []
    for comment in comments:
        if comment.strip():
            try:
                blob = TextBlob(comment)
                polarities.append(blob.sentiment.polarity)
            except Exception as e:
                logger.warning(f"Error calculating sentiment for comment: {e}")
                
    return sum(polarities) / len(polarities) if polarities else 0.0

def calc_churn(repo_path: str) -> float:
    """
    Calculate total lines changed per commit, aggregated to repository level.
    
    Args:
        repo_path: Path to the repository root.
        
    Returns:
        Average lines changed per commit.
    """
    try:
        # Run git log --numstat
        result = subprocess.run(
            ["git", "-C", repo_path, "log", "--numstat", "--pretty=format:"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            logger.warning(f"Git log failed for {repo_path}: {result.stderr}")
            return 0.0
            
        lines_changed = []
        for line in result.stdout.splitlines():
            parts = line.split('\t')
            if len(parts) >= 2:
                try:
                    added = int(parts[0]) if parts[0] != '-' else 0
                    removed = int(parts[1]) if parts[1] != '-' else 0
                    lines_changed.append(added + removed)
                except ValueError:
                    continue
                    
        if not lines_changed:
            return 0.0
            
        return sum(lines_changed) / len(lines_changed)
    except Exception as e:
        logger.warning(f"Error calculating churn for {repo_path}: {e}")
        return 0.0

def calc_quality_rate(repo_path: str, sample_commits: List[str]) -> float:
    """
    Calculate ratio of commits with error-level warnings using pylint.
    
    Args:
        repo_path: Path to the repository root.
        sample_commits: List of commit hashes to sample.
        
    Returns:
        Ratio of commits with errors.
    """
    if not sample_commits:
        return 0.0
        
    error_count = 0
    total_checked = 0
    
    for commit in sample_commits:
        try:
            # Checkout commit (temporary)
            subprocess.run(["git", "-C", repo_path, "checkout", commit], check=True, capture_output=True)
            
            # Run pylint
            result = subprocess.run(
                ["pylint", "--errors-only", "--output-format=json", "."],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse JSON output
            if result.stdout:
                try:
                    pylint_output = json.loads(result.stdout)
                    if pylint_output and any(item.get('type') == 'error' for item in pylint_output):
                        error_count += 1
                except json.JSONDecodeError:
                    # Fallback: check stderr or stdout for "error"
                    if "error" in result.stdout.lower() or "error" in result.stderr.lower():
                        error_count += 1
            else:
                # No output might mean no errors or failure
                pass
                
            total_checked += 1
            
        except Exception as e:
            logger.warning(f"Error checking commit {commit}: {e}")
        finally:
            # Restore to main/master
            subprocess.run(["git", "-C", repo_path, "checkout", "-"], check=True, capture_output=True)
            
    return error_count / total_checked if total_checked > 0 else 0.0
