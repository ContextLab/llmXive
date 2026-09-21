import os
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_config_summary, ensure_directories
from utils import get_logger, validate_tools_and_log

logger = get_logger(__name__)

def get_file_language(file_path: str) -> Optional[str]:
    """
    Determine the programming language of a file based on its extension.
    Returns one of: 'python', 'java', 'javascript', 'typescript', 'go', 'rust', or None.
    """
    ext = Path(file_path).suffix.lower()
    language_map = {
        '.py': 'python',
        '.java': 'java',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.go': 'go',
        '.rs': 'rust',
    }
    return language_map.get(ext)

def run_radon_on_file(file_path: str) -> Tuple[Optional[int], Optional[float]]:
    """
    Run Radon on a Python file to get Cyclomatic Complexity (CC) sum and Maintainability Index (MI).
    Returns (total_cc, mi). If the file is not Python or Radon fails, returns (None, None).
    """
    if get_file_language(file_path) != 'python':
        return None, None

    try:
        # Run radon cc -s to get complexity sum and raw data
        # We need the sum of CC for all functions/classes in the file
        cc_process = subprocess.run(
            ['radon', 'cc', '-s', '-n', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Run radon mi to get maintainability index
        mi_process = subprocess.run(
            ['radon', 'mi', '-s', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if cc_process.returncode != 0:
            logger.warning(f"Radon CC failed for {file_path}: {cc_process.stderr}")
            return None, None
        
        if mi_process.returncode != 0:
            logger.warning(f"Radon MI failed for {file_path}: {mi_process.stderr}")
            return None, None

        # Parse CC sum from output (last line usually has the sum)
        # Output format: "A: 0.00, B: 0.00, C: 0.00, D: 0.00, E: 0.00, F: 0.00"
        # We need the total count of blocks, not the distribution
        # Actually, `radon cc -s` prints a summary. Let's parse the total.
        # Better approach: use radon cc -n (no summary) and count, but -s gives the distribution.
        # The sum of complexities is not directly in the summary line.
        # Let's parse the raw output lines to sum the CC values.
        total_cc = 0
        for line in cc_process.stdout.splitlines():
            # Lines look like: "    <function_name> <cc>" or "    <class> <cc>"
            parts = line.strip().split()
            if len(parts) >= 2 and parts[-1].isdigit():
                total_cc += int(parts[-1])
            elif len(parts) >= 2 and parts[-1].replace('.', '', 1).isdigit():
                # In case of float representation in some versions, though CC is int
                pass

        # Parse MI
        # Output: "File: <name> MI: <value>"
        mi_val = None
        for line in mi_process.stdout.splitlines():
            if "MI:" in line:
                try:
                    mi_val = float(line.split("MI:")[-1].strip())
                except ValueError:
                    pass
        
        return total_cc, mi_val

    except subprocess.TimeoutExpired:
        logger.error(f"Radon timed out for {file_path}")
        return None, None
    except Exception as e:
        logger.error(f"Error running Radon on {file_path}: {e}")
        return None, None

def run_semgrep_on_file(file_path: str) -> Tuple[Optional[int], List[Dict[str, Any]]]:
    """
    Run Semgrep on a file with security and auto configs.
    Returns (code_smell_count, list_of_findings).
    Only runs for Java, JS, TS, Go, Rust.
    """
    lang = get_file_language(file_path)
    if lang not in ['java', 'javascript', 'typescript', 'go', 'rust']:
        return None, []

    try:
        # Run semgrep with multiple configs
        # --config=p/security-audit and --config=auto
        # We output JSON to parse results
        cmd = [
            'semgrep',
            '--config=p/security-audit',
            '--config=auto',
            '--json',
            file_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode not in [0, 1]: # 0: no findings, 1: findings found
            # Semgrep returns 1 if findings are found, which is normal
            # We check if it's a real error (e.g., 2)
            if result.returncode == 2:
                logger.warning(f"Semgrep error for {file_path}: {result.stderr}")
                return None, []
        
        try:
            output = json.loads(result.stdout)
            results = output.get('results', [])
            # Count findings as code smells
            smell_count = len(results)
            return smell_count, results
        except json.JSONDecodeError:
            logger.warning(f"Semgrep JSON decode error for {file_path}: {result.stdout}")
            return 0, []

    except subprocess.TimeoutExpired:
        logger.error(f"Semgrep timed out for {file_path}")
        return None, []
    except Exception as e:
        logger.error(f"Error running Semgrep on {file_path}: {e}")
        return None, []

def process_repository(repo_id: str, repo_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Process a single repository:
    1. Find all source files.
    2. Run Radon on Python files.
    3. Run Semgrep on other supported languages.
    4. Calculate debt_score per file.
    5. Save results to output_dir/{repo_id}/semgrep_results.json
    
    Returns a summary dict.
    """
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    total_files = 0
    processed_files = 0
    
    # Walk the repo directory
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories and common non-source dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', 'dist', 'build', '__pycache__']]
        
        for file in files:
            file_path = Path(root) / file
            total_files += 1
            
            lang = get_file_language(file_path)
            if not lang:
                continue
            
            processed_files += 1
            file_result = {
                "file_path": str(file_path.relative_to(repo_path)),
                "language": lang,
                "cc": None,
                "mi": None,
                "code_smells": None,
                "debt_score": None,
                "raw_findings": []
            }
            
            if lang == 'python':
                cc, mi = run_radon_on_file(str(file_path))
                file_result["cc"] = cc
                file_result["mi"] = mi
                if cc is not None and mi is not None:
                    # Debt score = Sum(CC) + (100 - MI)
                    file_result["debt_score"] = cc + (100 - mi)
            else:
                smells, findings = run_semgrep_on_file(str(file_path))
                file_result["code_smells"] = smells
                file_result["raw_findings"] = findings
                if smells is not None:
                    # Debt score = Sum(Code Smells + CC)
                    # Since we don't run CC on non-python, we just use smells + 0
                    file_result["debt_score"] = smells
            
            results.append(file_result)
    
    output_file = output_dir / "semgrep_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    summary = {
        "repo_id": repo_id,
        "total_files_scanned": total_files,
        "source_files_processed": processed_files,
        "output_file": str(output_file),
        "debt_scores": [r["debt_score"] for r in results if r["debt_score"] is not None]
    }
    
    return summary

def run_static_analysis(repos_metadata_path: str, base_output_dir: str) -> List[Dict[str, Any]]:
    """
    Main entry point for static analysis phase.
    Reads repos_metadata.csv, processes each repo, and saves results.
    """
    from config import get_config_summary
    config = get_config_summary()
    
    if not os.path.exists(repos_metadata_path):
        raise FileNotFoundError(f"Repos metadata file not found: {repos_metadata_path}")
    
    import pandas as pd
    df = pd.read_csv(repos_metadata_path)
    
    results = []
    for _, row in df.iterrows():
        repo_id = row['repo_id']
        repo_path = Path(row['local_path']) # Assuming T011 added local_path
        
        if not repo_path.exists():
            logger.error(f"Repository path not found for {repo_id}: {repo_path}")
            continue
        
        output_dir = Path(base_output_dir) / 'static_analysis' / repo_id
        
        try:
            summary = process_repository(repo_id, repo_path, output_dir)
            results.append(summary)
            logger.info(f"Completed static analysis for {repo_id}")
        except Exception as e:
            logger.error(f"Failed to process {repo_id}: {e}")
            results.append({
                "repo_id": repo_id,
                "error": str(e)
            })
    
    return results

def main():
    """
    CLI entry point for static analysis.
    Usage: python code/static_analysis.py --repos <path> --output <path>
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run static analysis on repositories")
    parser.add_argument('--repos', type=str, required=True, help='Path to repos_metadata.csv')
    parser.add_argument('--output', type=str, default='data', help='Base output directory')
    args = parser.parse_args()
    
    setup_logging()
    logger.info("Starting static analysis phase")
    
    # Validate tools first
    validate_tools_and_log()
    
    results = run_static_analysis(args.repos, args.output)
    
    logger.info(f"Static analysis completed. Processed {len(results)} repositories.")
    return results

if __name__ == "__main__":
    main()
