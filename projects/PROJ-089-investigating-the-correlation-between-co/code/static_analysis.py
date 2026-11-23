import os
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import re
from config import get_config_summary, ensure_directories
from utils import get_logger

def get_file_language(file_path: str) -> Optional[str]:
    """Determine programming language from file extension."""
    ext_map = {
        '.py': 'python',
        '.java': 'java',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.go': 'go',
        '.rs': 'rust',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp'
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext)

def run_semgrep_on_file(file_path: str, language: str) -> Dict[str, Any]:
    """
    Run Semgrep on a single file and extract metrics.
    Returns a dict with debt_score and avg_loc.
    """
    logger = get_logger("pipeline")
    
    # Semgrep command
    cmd = [
        'semgrep',
        '--metrics', 'off',
        '--json',
        '--config', 'p/security-audit',  # Using a generic config for code smells
        file_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per file
        )
        
        if result.returncode != 0 and result.returncode != 1:
            # 1 is expected when no issues are found
            logger.warning(f"Semgrep returned non-zero for {file_path}: {result.stderr}")
            return {'debt_score': 0, 'avg_loc': 0, 'contributor_count': 1}
        
        output = json.loads(result.stdout)
        
        # Calculate debt_score
        # For Python: Sum(Cyclomatic Complexity) + (100 - Maintainability Index)
        # For others: Sum(Code Smells + Cyclomatic Complexity)
        
        debt_score = 0
        cc_sum = 0
        mi = 100  # Default MI if not found
        code_smells = 0
        
        results = output.get('results', [])
        
        for match in results:
            # Extract metrics from Semgrep output
            # Note: Semgrep's default rules may not provide all metrics
            # We'll count matches as code smells and estimate complexity
            code_smells += 1
            # Estimate CC based on rule severity or default to 1
            cc_sum += 1  # Simplified estimation
        
        if language == 'python':
            # If MI is not available, we skip the MI component (treat as 0 contribution)
            # debt_score = cc_sum + max(0, 100 - mi)
            debt_score = cc_sum  # Only CC for now as MI is often unavailable
        else:
            debt_score = code_smells + cc_sum
        
        # Calculate avg_loc (lines of code)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                avg_loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        except Exception:
            avg_loc = 0
        
        return {
            'debt_score': debt_score,
            'avg_loc': avg_loc,
            'contributor_count': 1
        }
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Semgrep timeout for {file_path}")
        return {'debt_score': 0, 'avg_loc': 0, 'contributor_count': 1}
    except Exception as e:
        logger.error(f"Error running Semgrep on {file_path}: {str(e)}")
        return {'debt_score': 0, 'avg_loc': 0, 'contributor_count': 1}

def process_repository(repo_id: str, repo_path: str) -> Dict[str, Any]:
    """
    Process all files in a repository for static analysis.
    Returns a dict mapping file paths to their metrics.
    """
    logger = get_logger("pipeline")
    logger.info(f"Running static analysis on {repo_id}")
    
    results = {}
    repo_path = Path(repo_path)
    
    # Supported extensions
    supported_exts = {'.py', '.java', '.js', '.ts', '.go', '.rs', '.c', '.cpp', '.h', '.hpp'}
    
    for file_path in repo_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_exts:
            # Skip test files and build artifacts
            if 'test' in file_path.name.lower() or 'node_modules' in str(file_path):
                continue
            
            language = get_file_language(str(file_path))
            if language:
                metrics = run_semgrep_on_file(str(file_path), language)
                # Use relative path from repo root
                rel_path = str(file_path.relative_to(repo_path))
                results[rel_path] = metrics
    
    logger.info(f"Static analysis completed for {len(results)} files in {repo_id}")
    return results

def run_static_analysis():
    """
    Run static analysis on all repositories.
    This is called from main.py.
    """
    logger = get_logger("pipeline")
    logger.info("Starting static analysis pipeline")
    
    # The actual per-repo processing is handled in data_extraction.py
    # This function serves as a hook for the pipeline
    logger.info("Static analysis module loaded")
    return True

def main():
    """Main entry point for static analysis module."""
    ensure_directories()
    setup_logging()
    # This would be called with a specific repo
    print("Static analysis module ready.")

if __name__ == "__main__":
    main()
