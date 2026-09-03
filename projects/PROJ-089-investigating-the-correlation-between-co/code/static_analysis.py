import os
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from radon.complexity import cc_visit
from radon.mi import mi_visit

from config import get_config_summary
from utils import get_logger

# Supported languages for Semgrep
SEMGREP_LANGUAGES = {
    '.java': 'java',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.go': 'go',
    '.rs': 'rust',
    '.py': 'python' # Radon handles Python, but Semgrep can too if needed
}

RADON_SUPPORTED = True
try:
    from radon.complexity import cc_visit
    from radon.mi import mi_visit
except ImportError:
    RADON_SUPPORTED = False

SEMGREP_SUPPORTED = True
try:
    subprocess.run(['semgrep', '--version'], capture_output=True, check=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    SEMGREP_SUPPORTED = False

logger = get_logger(__name__)

def get_file_language(file_path: str) -> Optional[str]:
    """Determine the programming language based on file extension."""
    ext = Path(file_path).suffix.lower()
    return SEMGREP_LANGUAGES.get(ext)

def run_radon_on_file(file_path: str) -> Dict[str, Any]:
    """
    Run Radon on a Python file to calculate Cyclomatic Complexity (CC)
    and Maintainability Index (MI).
    
    Returns:
        Dict with 'cc' (sum of block CC) and 'mi' (average MI).
    """
    if not RADON_SUPPORTED:
        raise RuntimeError("Radon is not installed or available.")
    
    if not Path(file_path).exists():
        return {'cc': 0.0, 'mi': 0.0}

    try:
        # Calculate CC
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        cc_results = cc_visit(source)
        total_cc = sum(block.cc for block in cc_results)
        
        # Calculate MI (0-100 scale)
        mi_results = mi_visit(source, multi=True)
        avg_mi = sum(mi_results) / len(mi_results) if mi_results else 0.0
        
        return {'cc': float(total_cc), 'mi': float(avg_mi)}
    except Exception as e:
        logger.error(f"Error running Radon on {file_path}: {e}")
        return {'cc': 0.0, 'mi': 0.0}

def run_semgrep_on_file(file_path: str) -> Dict[str, Any]:
    """
    Run Semgrep on a file to capture Code Smells and Cyclomatic Complexity.
    
    Returns:
        Dict with 'smells' (count of code smells) and 'cc' (if available from Semgrep).
        If Semgrep fails or returns no issues, returns 0 for smells.
    """
    if not SEMGREP_SUPPORTED:
        raise RuntimeError("Semgrep is not installed or available.")
    
    if not Path(file_path).exists():
        return {'smells': 0, 'cc': 0.0}

    lang = get_file_language(file_path)
    if not lang:
        return {'smells': 0, 'cc': 0.0}

    try:
        # Use a generic set of rules or a specific config if available.
        # For this implementation, we use a generic config to catch common smells.
        # We capture the output as JSON.
        # Note: '--autofix' is not used here as we only want to count.
        cmd = [
            'semgrep', 
            '--config', 'p/python', # Default to a broad set, or specific per lang if needed
            '--json', 
            '--quiet',
            file_path
        ]
        
        # Adjust config based on language if necessary, but 'p/python' is a safe fallback
        # for a generic run if specific rules aren't defined per-lang in this context.
        # A more robust implementation would map lang to specific semgrep configs.
        if lang == 'java':
            cmd[2] = 'p/java'
        elif lang == 'javascript':
            cmd[2] = 'p/javascript'
        elif lang == 'typescript':
            cmd[2] = 'p/typescript'
        elif lang == 'go':
            cmd[2] = 'p/go'
        elif lang == 'rust':
            cmd[2] = 'p/rust'
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300 # 5 min timeout per file
        )
        
        if result.returncode != 0 and result.returncode != 1:
            # Semgrep returns 1 if issues are found, 0 if clean, other for errors
            logger.warning(f"Semgrep returned code {result.returncode} for {file_path}: {result.stderr}")
            # If it's just finding issues (1), we proceed to parse. If error, log and return 0.
            if result.returncode != 1:
                return {'smells': 0, 'cc': 0.0}

        try:
            output = json.loads(result.stdout)
            results = output.get('results', [])
            smell_count = len(results)
            
            # Semgrep doesn't always provide CC directly in the generic output format
            # without specific rules. We assume 'smells' is the primary metric here.
            # If a rule explicitly captures CC, it would be in the message or extra data.
            # For this task, we sum Code Smells + CC. Since CC from Semgrep is not guaranteed
            # by the generic config, we rely on the smell count as the proxy for 'debt'
            # or assume the 'smells' count represents the complexity/debt issues found.
            # The task says: "debt_score = Sum(Code Smells + CC)".
            # If Semgrep doesn't provide CC, we treat CC from Semgrep as 0 and rely on Smells.
            # Alternatively, we could run radon on python files and semgrep on others.
            # The task says: "Run radon on Python... Run semgrep on Java, JS...".
            # So for non-Python, we only have Semgrep.
            # We will assume 'smells' is the metric.
            
            return {'smells': smell_count, 'cc': 0.0}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Semgrep JSON output for {file_path}")
            return {'smells': 0, 'cc': 0.0}

    except subprocess.TimeoutExpired:
        logger.error(f"Semgrep timed out for {file_path}")
        return {'smells': 0, 'cc': 0.0}
    except Exception as e:
        logger.error(f"Error running Semgrep on {file_path}: {e}")
        return {'smells': 0, 'cc': 0.0}

def process_repository(repo_path: str, output_csv_path: str) -> None:
    """
    Process all source files in a repository, calculate metrics, and save to CSV.
    
    Args:
        repo_path: Path to the cloned repository.
        output_csv_path: Path to the output CSV file (will be created/appended).
    """
    repo_name = Path(repo_path).name
    results = []
    
    # Define extensions to process
    # Python handled by Radon, others by Semgrep
    python_ext = '.py'
    other_exts = ['.java', '.js', '.ts', '.go', '.rs']
    
    files_processed = 0
    errors = 0
    
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden or large directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', 'build']]
        
        for file in files:
            file_path = os.path.join(root, file)
            ext = Path(file).suffix.lower()
            
            if ext == python_ext:
                try:
                    metrics = run_radon_on_file(file_path)
                    # Radon returns CC and MI. We need CC for debt_score.
                    # The task says debt_score = Sum(Code Smells + CC).
                    # For Python, we have CC from Radon. We assume 0 smells from Radon for this metric
                    # unless we map Radon's output to 'smells' conceptually, but the task distinguishes them.
                    # However, the task says "Run radon... to calculate CC and MI".
                    # And "Run semgrep... to capture Code Smells and CC".
                    # And "debt_score = Sum(Code Smells + CC)".
                    # So for Python: debt_score = 0 (smells) + CC (from radon).
                    # For others: debt_score = Smells (from semgrep) + 0 (CC from semgrep if not available).
                    # We will strictly follow:
                    # Python: CC from Radon, Smells = 0.
                    # Others: Smells from Semgrep, CC = 0 (unless Semgrep provides it).
                    
                    debt_score = metrics['cc'] # Smells is 0 for Python in this logic
                    results.append({
                        'repo_name': repo_name,
                        'file_path': file_path,
                        'language': 'python',
                        'cc': metrics['cc'],
                        'mi': metrics['mi'],
                        'smells': 0,
                        'debt_score': debt_score
                    })
                    files_processed += 1
                except Exception as e:
                    logger.error(f"Error processing Python file {file_path}: {e}")
                    errors += 1
                    
            elif ext in other_exts:
                try:
                    metrics = run_semgrep_on_file(file_path)
                    debt_score = metrics['smells'] # CC is 0 for non-Python in this logic
                    results.append({
                        'repo_name': repo_name,
                        'file_path': file_path,
                        'language': get_file_language(file_path),
                        'cc': 0.0, # Radon not run, Semgrep CC not guaranteed
                        'mi': 0.0,
                        'smells': metrics['smells'],
                        'debt_score': debt_score
                    })
                    files_processed += 1
                except Exception as e:
                    logger.error(f"Error processing {ext} file {file_path}: {e}")
                    errors += 1
    
    # Save to CSV
    if results:
        df = pd.DataFrame(results)
        # If file exists, append; else create
        if os.path.exists(output_csv_path):
            df.to_csv(output_csv_path, mode='a', header=False, index=False)
        else:
            df.to_csv(output_csv_path, index=False)
        
        logger.info(f"Processed {files_processed} files in {repo_name}, {errors} errors. Saved to {output_csv_path}")
    else:
        logger.warning(f"No files processed for {repo_name}")

def run_static_analysis(repos_metadata_path: str, output_path: str) -> None:
    """
    Main entry point to run static analysis on a list of repositories.
    
    Args:
        repos_metadata_path: Path to the CSV containing repository metadata (cloned paths).
        output_path: Path to the output CSV for static analysis results.
    """
    if not os.path.exists(repos_metadata_path):
        raise FileNotFoundError(f"Repository metadata file not found: {repos_metadata_path}")
    
    df_repos = pd.read_csv(repos_metadata_path)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Clear output file if it exists to start fresh for this run
    if os.path.exists(output_path):
        os.remove(output_path)
        
    for _, row in df_repos.iterrows():
        repo_path = row['repo_path']
        if os.path.exists(repo_path):
            logger.info(f"Starting static analysis for {repo_path}")
            process_repository(repo_path, output_path)
        else:
            logger.warning(f"Repository path not found: {repo_path}")

def main():
    """CLI entry point for static analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run static analysis (Radon/Semgrep) on repositories.")
    parser.add_argument('--repos', type=str, required=True, help="Path to repos_metadata.csv")
    parser.add_argument('--output', type=str, required=True, help="Path to output CSV")
    
    args = parser.parse_args()
    
    setup_logging()
    run_static_analysis(args.repos, args.output)

if __name__ == "__main__":
    main()
