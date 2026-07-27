import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_config, get_paths, ensure_directories

logger = logging.getLogger(__name__)

def find_python_files(directory: Path) -> List[Path]:
    """Recursively find all .py files in directory."""
    if not directory.exists():
        logger.warning(f"Directory {directory} does not exist.")
        return []
    return list(directory.rglob("*.py"))

def run_bandit_scan(file_path: Path, config_path: Path) -> Optional[Dict[str, Any]]:
    """
    Run Bandit static analysis on a single file.
    Returns parsed result or None if scan fails (e.g., syntax error).
    """
    try:
        # Construct command
        cmd = [
            sys.executable, "-m", "bandit",
            "-r", str(file_path),
            "-f", "json",
            "-c", str(config_path),
            "-o", "-" # Output to stdout
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60 # Timeout to prevent hanging on large files
        )
        
        # Bandit returns 0 if no issues, 1 if issues found, 2 if error
        if result.returncode in (0, 1): 
            if result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Sometimes bandit outputs partial JSON or text on error
                    logger.warning(f"Failed to parse JSON output for {file_path}: {result.stdout[:200]}")
                    return {"errors": [], "results": [], "file": str(file_path)}
            return {"errors": [], "results": [], "file": str(file_path)}
        else:
            # Check if it's a syntax error or other issue
            if "SyntaxError" in result.stderr or "IndentationError" in result.stderr:
                logger.warning(f"Syntax error in {file_path}, skipping: {result.stderr.strip()}")
            else:
                logger.warning(f"Bandit failed for {file_path}: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error(f"Bandit timeout for {file_path}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running Bandit on {file_path}: {e}")
        return None

def parse_bandit_report(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse raw Bandit JSON report into a structured list of vulnerabilities.
    """
    vulnerabilities = []
    if "results" in report and report["results"]:
        for item in report["results"]:
            vuln = {
                "file_path": item.get("filename", "unknown"),
                "cwe_id": item.get("issue_cwe", {}).get("id", "unknown"),
                "severity": item.get("issue_severity", "unknown"),
                "line_number": item.get("line_number", 0),
                "issue_text": item.get("issue_text", ""),
                "test_id": item.get("test_id", "unknown"),
                "test_name": item.get("test_name", "unknown")
            }
            vulnerabilities.append(vuln)
    return vulnerabilities

def main():
    """Main entry point for analysis script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    paths = get_paths()
    config = get_config()
    
    # Ensure output directories
    ensure_directories()
    
    generated_dir = paths['data'] / 'generated'
    human_dir = paths['data'] / 'human'
    bandit_config = paths['code'] / 'config' / 'bandit_config.yaml'
    
    raw_reports_path = paths['data'] / 'processed' / 'bandit_raw_reports.json'
    vuln_reports_path = paths['data'] / 'processed' / 'vulnerability_reports.json'
    
    # Check if bandit is installed
    try:
        subprocess.run([sys.executable, "-m", "bandit", "--version"], 
                     capture_output=True, check=True)
    except subprocess.CalledProcessError:
        logger.error("Bandit is not installed or not working. Run: pip install bandit")
        sys.exit(1)
    
    all_files = []
    if generated_dir.exists():
        all_files.extend(find_python_files(generated_dir))
    if human_dir.exists():
        all_files.extend(find_python_files(human_dir))
    
    logger.info(f"Found {len(all_files)} Python files to analyze.")
    
    if not all_files:
        logger.warning("No Python files found to analyze. Creating empty output files.")
        with open(raw_reports_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        with open(vuln_reports_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return
    
    raw_results = []
    structured_results = []
    
    for file_path in all_files:
        logger.info(f"Scanning {file_path}...")
        
        # Run Bandit
        report = run_bandit_scan(file_path, bandit_config)
        
        if report is None:
            # LOGGING FOR PARSE ERRORS / SCAN FAILURES
            logger.error(f"Skipping {file_path} due to scan or parse failure (likely syntax error).")
            continue
            
        # Add file path to raw report if missing
        if "file" not in report:
            report["file"] = str(file_path)
            
        raw_results.append({"file": str(file_path), "report": report})
        
        # Parse
        parsed = parse_bandit_report(report)
        for v in parsed:
            structured_results.append(v)
    
    # Save raw reports
    with open(raw_reports_path, 'w', encoding='utf-8') as f:
        json.dump(raw_results, f, indent=2)
    logger.info(f"Saved raw reports to {raw_reports_path}")
    
    # Save structured reports
    with open(vuln_reports_path, 'w', encoding='utf-8') as f:
        json.dump(structured_results, f, indent=2)
    logger.info(f"Saved vulnerability reports to {vuln_reports_path}")
    
    logger.info(f"Analysis complete. Found {len(structured_results)} total vulnerabilities.")

if __name__ == "__main__":
    main()