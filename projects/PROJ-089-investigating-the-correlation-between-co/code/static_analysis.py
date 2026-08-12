import os
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys

# Add project root to path to allow imports if run directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils import get_logger, validate_tools_and_log

# Configuration constants
RADON_VERSION = "0"
SEMGREP_VERSION = "latest"
SUPPORTED_LANGUAGES = {
    "py": "python",
    "java": "java",
    "js": "javascript",
    "ts": "typescript",
    "go": "go",
    "rs": "rust"
}

logger = get_logger(__name__)

def get_file_language(file_path: Path) -> Optional[str]:
    """
    Determine the programming language of a file based on extension.
    Returns 'python', 'java', etc., or None if not supported.
    """
    ext = file_path.suffix.lower().lstrip('.')
    return SUPPORTED_LANGUAGES.get(ext)

def run_radon_on_file(file_path: Path) -> Dict[str, Any]:
    """
    Run Radon CC (Cyclomatic Complexity) and MI (Maintainability Index) on a Python file.
    Returns a dict with 'cc' (sum of complexities) and 'mi' (average MI).
    """
    if not file_path.exists():
        logger.warning(f"File not found for Radon analysis: {file_path}")
        return {'cc': 0, 'mi': 0.0, 'error': 'File not found'}

    try:
        # Run Radon CC
        # radon cc <file> -s --json
        cc_cmd = ["radon", "cc", str(file_path), "-s", "--json"]
        result_cc = subprocess.run(cc_cmd, capture_output=True, text=True, timeout=60)
        
        if result_cc.returncode != 0:
            logger.error(f"Radon CC failed for {file_path}: {result_cc.stderr}")
            cc_data = []
        else:
            cc_data = json.loads(result_cc.stdout) if result_cc.stdout.strip() else []

        # Calculate total CC (sum of all function/class complexities)
        total_cc = 0
        if isinstance(cc_data, list):
            for item in cc_data:
                # Item might be a function or a class
                if isinstance(item, dict):
                    total_cc += item.get('complexity', 0)
        
        # Run Radon MI
        # radon mi <file> --json
        mi_cmd = ["radon", "mi", str(file_path), "--json"]
        result_mi = subprocess.run(mi_cmd, capture_output=True, text=True, timeout=60)

        mi_value = 0.0
        if result_mi.returncode == 0 and result_mi.stdout.strip():
            mi_data = json.loads(result_mi.stdout)
            if isinstance(mi_data, list) and len(mi_data) > 0:
                # MI is often a list of values for different scopes, take average
                mi_values = [d.get('mi', 0) for d in mi_data if isinstance(d, dict)]
                if mi_values:
                    mi_value = sum(mi_values) / len(mi_values)

        return {
            'cc': total_cc,
            'mi': mi_value,
            'error': None
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Radon timed out for {file_path}")
        return {'cc': 0, 'mi': 0.0, 'error': 'Timeout'}
    except Exception as e:
        logger.error(f"Error running Radon on {file_path}: {e}")
        return {'cc': 0, 'mi': 0.0, 'error': str(e)}

def run_semgrep_on_file(file_path: Path) -> Dict[str, Any]:
    """
    Run Semgrep on a file to capture Code Smells and Cyclomatic Complexity (if available).
    Returns a dict with 'code_smells' (count) and 'cc' (approximate if available).
    Note: Semgrep is used here as a Plan-approved override for CPU feasibility.
    """
    if not file_path.exists():
        logger.warning(f"File not found for Semgrep analysis: {file_path}")
        return {'code_smells': 0, 'cc': 0, 'error': 'File not found'}

    lang = get_file_language(file_path)
    if not lang:
        return {'code_smells': 0, 'cc': 0, 'error': 'Unsupported language'}

    try:
        # Run Semgrep with a generic set of rules (e.g., default rules or a specific config)
        # We use 'p/python' for Python, 'p/javascript' for JS, etc.
        # To capture code smells, we rely on the default rule set which includes many smell patterns.
        # Command: semgrep scan <file> --config auto --json
        # Note: 'auto' config might be heavy; for performance, we might use a specific config file if defined.
        # For this implementation, we assume 'auto' or a default set of rules is sufficient for "Code Smells".
        
        # Using a specific rule set for code smells if 'auto' is too heavy, 
        # but the task says "latest stable version" and "capture Code Smells".
        # We will use the default configuration which includes security and best practices.
        
        config_arg = "auto"
        
        semgrep_cmd = [
            "semgrep", "scan", 
            str(file_path), 
            "--config", config_arg,
            "--json",
            "--quiet" # Reduce noise in output
        ]
        
        result = subprocess.run(
            semgrep_cmd, 
            capture_output=True, 
            text=True, 
            timeout=300 # 5 minute timeout per file
        )

        if result.returncode != 0 and result.returncode != 1: 
            # Return code 1 often means "findings found", which is success for us.
            # Return code 0 means no findings.
            # Other codes are errors.
            logger.error(f"Semgrep failed for {file_path}: {result.stderr}")
            return {'code_smells': 0, 'cc': 0, 'error': result.stderr}

        try:
            findings = json.loads(result.stdout)
            results_list = findings.get('results', [])
            
            code_smell_count = len(results_list)
            
            # Semgrep does not directly output CC in standard JSON format without specific rules.
            # We will estimate CC contribution or set to 0 if not available from rules.
            # For the purpose of debt_score = Sum(Code Smells + CC), if CC is not provided,
            # we treat it as 0 for this specific tool output, relying on Code Smells as the proxy.
            # Alternatively, if a specific rule outputs CC, we could parse it.
            # Given the constraints, we use code_smell_count as the primary metric.
            
            estimated_cc = 0 
            # If specific rules were used that output CC, we would parse them here.
            # For now, we assume Code Smells is the dominant factor for Semgrep in this context.

            return {
                'code_smells': code_smell_count,
                'cc': estimated_cc,
                'error': None
            }

        except json.JSONDecodeError:
            logger.error(f"Semgrep JSON decode error for {file_path}: {result.stdout}")
            return {'code_smells': 0, 'cc': 0, 'error': 'Invalid JSON output'}

    except subprocess.TimeoutExpired:
        logger.error(f"Semgrep timed out for {file_path}")
        return {'code_smells': 0, 'cc': 0, 'error': 'Timeout'}
    except Exception as e:
        logger.error(f"Error running Semgrep on {file_path}: {e}")
        return {'code_smells': 0, 'cc': 0, 'error': str(e)}

def process_repository(repo_path: Path, output_csv_path: Path) -> None:
    """
    Process a single repository directory:
    1. Iterate over source files.
    2. Run appropriate static analysis tool.
    3. Calculate debt_score = Sum(Code Smells + CC).
    4. Append results to the output CSV.
    """
    if not repo_path.exists():
        logger.error(f"Repository path does not exist: {repo_path}")
        return

    # Ensure output file exists with headers if it doesn't
    headers = ['file_path', 'repo_id', 'language', 'cc', 'mi', 'code_smells', 'debt_score']
    
    if not output_csv_path.exists():
        with open(output_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

    repo_id = repo_path.name
    
    # Walk through the repo
    for root, dirs, files in os.walk(repo_path):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv', 'env', 'dist', 'build']]
        
        for file_name in files:
            file_path = Path(root) / file_name
            lang = get_file_language(file_path)
            
            if not lang:
                continue

            logger.info(f"Analyzing {file_path} ({lang})")
            
            metrics = {}
            if lang == 'python':
                metrics = run_radon_on_file(file_path)
            else:
                metrics = run_semgrep_on_file(file_path)

            if metrics.get('error'):
                logger.warning(f"Skipping {file_path} due to error: {metrics['error']}")
                continue

            cc = metrics.get('cc', 0)
            mi = metrics.get('mi', 0)
            code_smells = metrics.get('code_smells', 0)
            
            # Calculate debt_score = Sum(Code Smells + CC)
            debt_score = code_smells + cc

            row = {
                'file_path': str(file_path.relative_to(repo_path)),
                'repo_id': repo_id,
                'language': lang,
                'cc': cc,
                'mi': mi,
                'code_smells': code_smells,
                'debt_score': debt_score
            }

            # Append to CSV
            with open(output_csv_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writerow(row)

def run_static_analysis(repos_metadata_path: Path, output_dir: Path) -> None:
    """
    Main entry point for static analysis.
    Reads repos_metadata.csv, processes each repo, and outputs results to a unified CSV.
    """
    if not repos_metadata_path.exists():
        raise FileNotFoundError(f"Repos metadata file not found: {repos_metadata_path}")

    # Validate tools first
    validate_tools_and_log()

    output_csv = output_dir / "static_analysis_metrics.csv"
    if output_csv.exists():
        output_csv.unlink() # Remove existing to start fresh

    import pandas as pd
    df_repos = pd.read_csv(repos_metadata_path)
    
    if 'repo_path' not in df_repos.columns:
        raise ValueError("repos_metadata.csv must contain a 'repo_path' column")

    logger.info(f"Starting static analysis on {len(df_repos)} repositories")

    for _, row in df_repos.iterrows():
        repo_path = Path(row['repo_path'])
        if repo_path.exists():
            process_repository(repo_path, output_csv)
        else:
            logger.warning(f"Skipping non-existent repo path: {repo_path}")

    logger.info(f"Static analysis complete. Results saved to {output_csv}")

def main():
    """
    CLI entry point for static analysis.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run static analysis on repositories")
    parser.add_argument("--repos-csv", type=str, required=True, help="Path to repos_metadata.csv")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to save results")
    args = parser.parse_args()

    run_static_analysis(Path(args.repos_csv), Path(args.output_dir))

if __name__ == "__main__":
    main()