import subprocess
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def run_command(cmd: List[str], timeout: int = 120, cwd: Optional[Path] = None) -> tuple:
    """
    Run a shell command and return stdout, stderr, and return code.
    
    Args:
        cmd: Command as a list of strings
        timeout: Timeout in seconds
        cwd: Working directory for the command
        
    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    try:
        logger.debug(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd=cwd,
            check=False
        )
        return (
            result.stdout.decode('utf-8', errors='ignore'),
            result.stderr.decode('utf-8', errors='ignore'),
            result.returncode
        )
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {' '.join(cmd)}")
        return ("", "Command timed out", -1)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return ("", str(e), -1)

def parse_git_log(repo_path: Path, format_str: str = "%ae") -> List[str]:
    """
    Parse git log with a custom format string to extract author information.
    
    This function executes `git log` on the specified repository path using
    the provided format string (defaulting to "%ae" for author email).
    It returns a list of extracted values (e.g., unique author emails).
    
    Args:
        repo_path: Path to the git repository
        format_str: Git log format string (e.g., "%ae" for author email, 
                   "%an" for author name, "%H" for commit hash)
        
    Returns:
        List of extracted values (strings). Returns an empty list if the
        command fails or no output is produced.
    """
    cmd = ["git", "-C", str(repo_path), "log", "--format=" + format_str]
    stdout, stderr, code = run_command(cmd, timeout=120)
    
    if code != 0:
        logger.warning(f"Git log failed for {repo_path}: {stderr}")
        return []
    
    lines = stdout.strip().split('\n')
    return [line.strip() for line in lines if line.strip()]

def run_cloc(repo_path: Path) -> Dict[str, Any]:
    """
    Run cloc (Count Lines of Code) on a repository and parse the results.
    
    This function executes the `cloc` tool on the specified repository path
    to calculate the total lines of code. It parses the output to extract
    the total line count and converts it to KLOC (thousands of lines of code).
    
    Args:
        repo_path: Path to the repository directory
        
    Returns:
        Dictionary containing:
            - "total_lines" (int): Total number of lines of code
            - "kloc" (float): Total lines divided by 1000
            - "success" (bool): True if cloc ran successfully, False otherwise
    """
    cmd = ["cloc", "--by-file", "--quiet", str(repo_path)]
    stdout, stderr, code = run_command(cmd, timeout=120)
    
    if code != 0:
        logger.warning(f"cloc failed for {repo_path}: {stderr}")
        return {"total_lines": 0, "kloc": 0.0, "success": False}
    
    total_lines = 0
    lines = stdout.strip().split('\n')
    
    # Look for the SUM line which cloc typically outputs
    for line in lines:
        if line.startswith("SUM") or line.startswith("sum"):
            parts = line.split()
            if len(parts) >= 4:
                try:
                    total_lines = int(parts[3])
                except ValueError:
                    pass
            break
    
    # Fallback: manually sum lines if no SUM line found
    if total_lines == 0:
        for line in lines:
            if line.strip() and not line.startswith('#') and not line.startswith('URL') and not line.startswith('Language'):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        total_lines += int(parts[3])
                    except ValueError:
                        pass
    
    kloc = total_lines / 1000.0
    return {
        "total_lines": total_lines,
        "kloc": kloc,
        "success": True
    }
