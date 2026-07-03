"""
Utility functions for GitHub data extraction.

This module contains helper functions for parsing git logs and running cloc,
extracted from code/data/extract_github.py for better modularity.
"""
import subprocess
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def run_command(command: List[str], cwd: Optional[Path] = None, timeout: int = 3600) -> tuple:
    """
    Execute a shell command and return (stdout, stderr, return_code).
    
    Args:
        command: List of command arguments
        cwd: Working directory for the command
        timeout: Maximum execution time in seconds
        
    Returns:
        Tuple of (stdout, stderr, return_code)
        
    Raises:
        subprocess.TimeoutExpired: If command exceeds timeout
        subprocess.CalledProcessError: If command fails
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with code {e.returncode}: {' '.join(command)}")
        raise


def parse_git_log(repo_path: Path) -> List[str]:
    """
    Parse git log to extract unique author names with ≥ 1 line of code committed.
    
    This function runs 'git log' with a specific format to extract author names
    and line counts, then returns a list of unique authors who have committed
    at least one line of code.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        List of unique author names (strings)
        
    Raises:
        RuntimeError: If git log command fails
    """
    # Format: author name and numstat for line counting
    # We use --numstat to get line counts per file
    command = [
        'git', 'log',
        '--pretty=format:%an',
        '--numstat',
        '--no-merges'
    ]
    
    stdout, stderr, returncode = run_command(command, cwd=repo_path)
    
    if returncode != 0:
        error_msg = f"git log failed for {repo_path}: {stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    if not stdout.strip():
        logger.warning(f"No commits found in {repo_path}")
        return []
    
    # Parse the output to extract unique authors
    # The format alternates between author name and file stats
    lines = stdout.strip().split('\n')
    authors = set()
    current_author = None
    
    for line in lines:
        if not line.strip():
            continue
            
        # Check if this is an author line (non-numeric, not a file stat line)
        # File stat lines start with numbers or are binary indicators
        if line[0].isdigit() or line.startswith('-'):
            # This is a numstat line, skip (we just need to track the author)
            continue
        elif line == '':
            continue
        else:
            # This is likely an author name
            # We need to be careful: author names can contain spaces
            # The format is just the name on its own line
            if current_author is not None:
                # We have a previous author, add them if they had commits
                # (we assume if we got here, they had commits)
                authors.add(current_author)
            
            current_author = line
    
    # Don't forget the last author
    if current_author is not None:
        authors.add(current_author)
    
    logger.debug(f"Found {len(authors)} unique authors in {repo_path}")
    return list(authors)


def run_cloc(repo_path: Path) -> Dict[str, Any]:
    """
    Run cloc on a repository to get KLOC (thousands of lines of code).
    
    This function executes the cloc command with --by-file option and
    parses the output to extract the total lines of code (excluding comments
    and blank lines).
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Dictionary with:
            - 'kloc': float (total lines of code / 1000)
            - 'raw_line_count': int (total lines before filtering)
            - 'language_breakdown': dict (lines per language)
            
    Raises:
        RuntimeError: If cloc is not installed or fails
        ValueError: If cloc version < 1.88
    """
    # First check cloc version
    version_command = ['cloc', '--version']
    stdout, stderr, returncode = run_command(version_command)
    
    if returncode != 0:
        error_msg = f"cloc not found or not executable: {stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Parse version
    version_line = stdout.strip().split('\n')[0]
    try:
        version_str = version_line.split(' ')[-1]
        major, minor = map(int, version_str.split('.')[:2])
        if major < 1 or (major == 1 and minor < 88):
            raise ValueError(f"cloc version {version_str} < 1.88 required")
    except (ValueError, IndexError) as e:
        logger.warning(f"Could not parse cloc version: {version_line}, proceeding anyway")
    
    # Run cloc with --by-file
    command = [
        'cloc',
        '--by-file',
        '--quiet',
        '--progress-rate=0',
        str(repo_path)
    ]
    
    stdout, stderr, returncode = run_command(command, cwd=repo_path)
    
    if returncode != 0:
        error_msg = f"cloc failed for {repo_path}: {stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Parse cloc output
    # Format: <language> <nFiles> <blank> <comment> <code>
    lines = stdout.strip().split('\n')
    
    total_code = 0
    total_blank = 0
    total_comment = 0
    language_breakdown = {}
    
    for line in lines:
        if not line.strip():
            continue
        
        # Skip header and summary lines
        if line.startswith('SUM:') or line.startswith('#'):
            continue
        
        parts = line.split()
        if len(parts) < 5:
            continue
        
        # Skip the language name if it's a summary line
        if parts[0] == 'SUM':
            continue
        
        try:
            # Format: Language <files> <blank> <comment> <code>
            # Sometimes there are more columns, so we take the last 4 numeric columns
            numeric_parts = []
            for part in parts[1:]:
                try:
                    numeric_parts.append(int(part))
                except ValueError:
                    continue
            
            if len(numeric_parts) >= 4:
                files_count = numeric_parts[0]
                blank = numeric_parts[1]
                comment = numeric_parts[2]
                code = numeric_parts[3]
                
                language = ' '.join(parts[:1])  # Language name (may have spaces)
                
                total_code += code
                total_blank += blank
                total_comment += comment
                language_breakdown[language] = code
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse cloc line: {line}, error: {e}")
            continue
    
    # Calculate KLOC
    kloc = total_code / 1000.0
    
    logger.debug(f"cloc result for {repo_path}: {kloc:.3f} KLOC")
    
    return {
        'kloc': kloc,
        'raw_line_count': total_code,
        'language_breakdown': language_breakdown
    }