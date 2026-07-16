import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import subprocess
import json
import textstat
from textblob import TextBlob
from radon.complexity import cc_visit
from radon.raw import analyze
import re

# Configure logging for this module
logger = logging.getLogger(__name__)

def calc_readability(comments: List[str]) -> float:
    """
    Calculate average Flesch-Kincaid readability grade for a list of comment strings.
    
    Args:
        comments: List of comment text strings extracted from code.
        
    Returns:
        Average readability grade (float), or 0.0 if comments list is empty.
    """
    if not comments:
        logger.warning("Empty comment set provided to calc_readability, returning 0.0")
        return 0.0
    
    scores = []
    for comment in comments:
        if not comment or not comment.strip():
            continue
        try:
            # textstat.flesch_kincaid_grade expects a string
            score = textstat.flesch_kincaid_grade(comment)
            scores.append(score)
        except Exception as e:
            logger.warning(f"Could not calculate readability for comment: {e}")
            continue
    
    if not scores:
        logger.warning("No valid scores calculated for readability, returning 0.0")
        return 0.0
        
    return sum(scores) / len(scores)

def calc_sentiment(comments: List[str]) -> float:
    """
    Calculate average polarity sentiment for a list of comment strings.
    
    Args:
        comments: List of comment text strings extracted from code.
        
    Returns:
        Average polarity score (float between -1.0 and 1.0), or 0.0 if empty.
    """
    if not comments:
        logger.warning("Empty comment set provided to calc_sentiment, returning 0.0")
        return 0.0
    
    scores = []
    for comment in comments:
        if not comment or not comment.strip():
            continue
        try:
            blob = TextBlob(comment)
            scores.append(blob.sentiment.polarity)
        except Exception as e:
            logger.warning(f"Could not calculate sentiment for comment: {e}")
            continue
    
    if not scores:
        logger.warning("No valid scores calculated for sentiment, returning 0.0")
        return 0.0
        
    return sum(scores) / len(scores)

def calc_complexity_for_file(file_path: str) -> float:
    """
    Calculate average cyclomatic complexity for functions in a single Python file.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        Average cyclomatic complexity (float), or 0.0 if file has no functions or errors.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        if not source.strip():
            return 0.0
            
        # radon.cc_visit returns a list of complexity objects for each function/class
        complexity_list = cc_visit(source)
        
        if not complexity_list:
            return 0.0
            
        total_complexity = sum(cc.complexity for cc in complexity_list)
        return total_complexity / len(complexity_list)
        
    except Exception as e:
        logger.warning(f"Could not calculate complexity for {file_path}: {e}")
        return 0.0

def get_complexity_breakdown(file_path: str) -> Dict[str, Any]:
    """
    Get detailed complexity breakdown for a file.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        Dictionary with 'average_complexity' and 'total_functions' keys.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        complexity_list = cc_visit(source)
        
        return {
            'average_complexity': sum(cc.complexity for cc in complexity_list) / len(complexity_list) if complexity_list else 0.0,
            'total_functions': len(complexity_list),
            'max_complexity': max((cc.complexity for cc in complexity_list), default=0)
        }
    except Exception as e:
        logger.warning(f"Could not get complexity breakdown for {file_path}: {e}")
        return {'average_complexity': 0.0, 'total_functions': 0, 'max_complexity': 0}

def calc_complexity(repo_path: str) -> float:
    """
    Calculate average cyclomatic complexity across all Python files in a repository.
    
    Args:
        repo_path: Path to the repository root.
        
    Returns:
        Average complexity across all files (float).
    """
    repo_path = Path(repo_path)
    if not repo_path.exists():
        logger.error(f"Repository path does not exist: {repo_path}")
        return 0.0
        
    python_files = list(repo_path.rglob("*.py"))
    
    if not python_files:
        logger.warning(f"No Python files found in {repo_path}")
        return 0.0
        
    total_complexity = 0.0
    valid_files = 0
    
    for py_file in python_files:
        # Skip common non-source directories
        if any(part.startswith('.') or part in ['venv', 'env', '__pycache__', 'node_modules'] for part in py_file.parts):
            continue
            
        avg_cc = calc_complexity_for_file(str(py_file))
        if avg_cc > 0:
            total_complexity += avg_cc
            valid_files += 1
            
    if valid_files == 0:
        logger.warning(f"No valid Python files with complexity found in {repo_path}")
        return 0.0
        
    return total_complexity / valid_files

def calc_churn(repo_path: str) -> float:
    """
    Calculate total lines changed (churn) for a repository by aggregating
    git log --numstat output across all commits.
    
    This function runs 'git log --numstat' to get added/deleted lines per commit,
    parses the output, and sums all changes to produce a total churn metric.
    
    Args:
        repo_path: Path to the repository root directory.
        
    Returns:
        Total churn (sum of added + deleted lines) as a float.
        
    Raises:
        RuntimeError: If git command fails or repository is not a valid git repo.
        FileNotFoundError: If the repo_path does not exist.
    """
    repo_path = Path(repo_path)
    
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
        
    if not (repo_path / ".git").exists():
        raise RuntimeError(f"Path is not a valid git repository: {repo_path}")
        
    try:
        # Run git log --numstat to get line changes per commit
        # Format: <added>\t<deleted>\t<filename>
        # The --numstat uses tabs and numbers, easier to parse
        result = subprocess.run(
            ["git", "log", "--numstat", "--pretty=format:"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for large repos
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or "Unknown git error"
            raise RuntimeError(f"Git log command failed: {error_msg}")
        
        output = result.stdout
        
        if not output.strip():
            logger.warning(f"No git history found in {repo_path}")
            return 0.0
            
        total_added = 0
        total_deleted = 0
        
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
                
            # Skip binary files (marked with '-' instead of numbers)
            if line.startswith('-'):
                continue
                
            parts = line.split('\t')
            if len(parts) < 2:
                continue
                
            added_str, deleted_str = parts[0], parts[1]
            
            # Skip binary files indicated by '-'
            if added_str == '-' or deleted_str == '-':
                continue
                
            try:
                added = int(added_str)
                deleted = int(deleted_str)
                total_added += added
                total_deleted += deleted
            except ValueError:
                # Skip lines that don't parse as integers
                continue
                
        total_churn = total_added + total_deleted
        logger.info(f"Calculated churn for {repo_path}: {total_churn} lines (added: {total_added}, deleted: {total_deleted})")
        return float(total_churn)
        
    except subprocess.TimeoutExpired:
        logger.error(f"Git log timed out for {repo_path}")
        raise RuntimeError(f"Git log command timed out for {repo_path}")
    except Exception as e:
        logger.error(f"Error calculating churn for {repo_path}: {e}")
        raise

def calc_density(comments: List[str], total_lines: int) -> float:
    """
    Calculate comment density as ratio of comment lines to total lines.
    
    Args:
        comments: List of comment strings (not used directly, but kept for API consistency).
        total_lines: Total lines of code in the file/repo.
        
    Returns:
        Comment density (float), 0.0 if total_lines is 0.
    """
    if total_lines <= 0:
        logger.warning(f"Invalid total_lines {total_lines} for density calculation")
        return 0.0
    
    # Count lines in comments (simplified: count non-empty lines in comment strings)
    comment_lines = 0
    for comment in comments:
        if comment:
            comment_lines += len([l for l in comment.split('\n') if l.strip()])
    
    return round(comment_lines / total_lines, 4)

def calc_quality_rate(repo_path: str) -> float:
    """
    Placeholder for quality rate calculation using pylint.
    TODO: Implement actual pylint analysis.
    """
    logger.warning("calc_quality_rate is not fully implemented yet")
    return 0.0

def main():
    """Main entry point for metrics module testing."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python metrics.py <command> [args]")
        print("Commands: churn <repo_path>, readability <comment1> [comment2...], sentiment <comment1> [comment2...]")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "churn":
        if len(sys.argv) < 3:
            print("Usage: python metrics.py churn <repo_path>")
            sys.exit(1)
        repo_path = sys.argv[2]
        try:
            churn = calc_churn(repo_path)
            print(f"Total churn: {churn}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
            
    elif command == "readability":
        if len(sys.argv) < 3:
            print("Usage: python metrics.py readability <comment1> [comment2...]")
            sys.exit(1)
        comments = sys.argv[2:]
        score = calc_readability(comments)
        print(f"Average readability: {score}")
        
    elif command == "sentiment":
        if len(sys.argv) < 3:
            print("Usage: python metrics.py sentiment <comment1> [comment2...]")
            sys.exit(1)
        comments = sys.argv[2:]
        score = calc_sentiment(comments)
        print(f"Average sentiment: {score}")
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()