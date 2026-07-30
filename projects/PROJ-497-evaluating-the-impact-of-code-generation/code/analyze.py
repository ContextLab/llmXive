"""
Static analysis module for vulnerability scanning using Bandit.

Executes Bandit on generated code samples and human benchmarks,
parses results, and aggregates vulnerability counts per file.
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd

from config import get_config, get_paths, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_python_files(root_dir: Path) -> List[Path]:
    """
    Recursively find all Python files in the given directory.
    
    Args:
        root_dir: Root directory to search for .py files
        
    Returns:
        List of Path objects for all Python files found
    """
    python_files = []
    if not root_dir.exists():
        logger.warning(f"Directory does not exist: {root_dir}")
        return python_files
        
    for py_file in root_dir.rglob("*.py"):
        # Skip common non-code directories
        if any(part in py_file.parts for part in ["__pycache__", ".git", "venv", ".venv", "build", "dist"]):
            continue
        python_files.append(py_file)
        
    logger.info(f"Found {len(python_files)} Python files in {root_dir}")
    return python_files

def run_bandit_scan(file_paths: List[Path], output_path: Path, config_path: Path) -> bool:
    """
    Execute Bandit static analysis on the given files.
    
    Args:
        file_paths: List of Python file paths to scan
        output_path: Path where the JSON report will be written
        config_path: Path to the Bandit configuration file
        
    Returns:
        True if the scan completed successfully, False otherwise
    """
    if not file_paths:
        logger.warning("No files to scan")
        return True
        
    # Convert paths to strings for subprocess
    paths_str = [str(p) for p in file_paths]
    
    # Build the bandit command
    cmd = [
        "bandit",
        "-r",  # Recursive
        "-f", "json",  # JSON output format
        "-o", str(output_path),  # Output file
        "--ini", str(config_path)  # Config file
    ] + paths_str
    
    logger.info(f"Running Bandit: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit (Bandit returns 1 if vulns found)
        )
        
        if result.returncode > 1:
            logger.error(f"Bandit execution failed: {result.stderr}")
            return False
            
        logger.info(f"Bandit scan completed. Output written to {output_path}")
        return True
        
    except FileNotFoundError:
        logger.error("Bandit not found. Please install it: pip install bandit")
        return False
    except Exception as e:
        logger.error(f"Error running Bandit: {e}")
        return False

def parse_bandit_report(report_path: Path) -> List[Dict[str, Any]]:
    """
    Parse the Bandit JSON report file.
    
    Args:
        report_path: Path to the JSON report file
        
    Returns:
        List of dictionaries containing vulnerability details
    """
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        return []
        
    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
            
        results = data.get("results", [])
        logger.info(f"Parsed {len(results)} vulnerability findings from Bandit report")
        return results
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON report: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading report file: {e}")
        return []

def extract_task_id_and_source_type(file_path: Path, base_dirs: Dict[str, Path]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract task_id and source_type from a file path.
    
    Expected directory structures:
    - data/generated/{model}/{benchmark}/{task_id}/samples/{filename}.py
    - data/human/{benchmark}/{task_id}/{filename}.py
    
    Args:
        file_path: Path to the code file
        base_dirs: Dictionary mapping source types to their base directories
        
    Returns:
        Tuple of (task_id, source_type) or (None, None) if not found
    """
    try:
        relative_path = file_path.relative_to(Path.cwd())
        parts = relative_path.parts
        
        # Check if it's in data/generated
        if len(parts) >= 2 and parts[0] == "data" and parts[1] == "generated":
            # Structure: data/generated/{model}/{benchmark}/{task_id}/samples/{filename}.py
            if len(parts) >= 6:
                model = parts[2]
                benchmark = parts[3]
                task_id = parts[4]
                source_type = f"generated_{model}"
                return task_id, source_type
                
        # Check if it's in data/human
        elif len(parts) >= 2 and parts[0] == "data" and parts[1] == "human":
            # Structure: data/human/{benchmark}/{task_id}/{filename}.py
            if len(parts) >= 4:
                benchmark = parts[2]
                task_id = parts[3].replace(".py", "").split("/")[-1] if "/" in parts[3] else parts[3]
                # Handle case where task_id might be in a subdirectory
                if task_id.endswith(".py"):
                    task_id = task_id[:-3]
                source_type = "human"
                return task_id, source_type
                
        # Fallback: try to extract from filename patterns
        # e.g., HumanEval_0.py, MBPP_123.py
        filename = file_path.name
        if "HumanEval" in filename:
            task_id = filename.replace("HumanEval_", "").replace(".py", "")
            return task_id, "human"
        elif "MBPP" in filename:
            task_id = filename.replace("MBPP_", "").replace(".py", "")
            return task_id, "human"
            
    except ValueError:
        # File is not relative to current working directory
        pass
        
    logger.debug(f"Could not extract task_id/source_type from: {file_path}")
    return None, None

def count_lines_of_code(file_path: Path) -> int:
    """
    Count the number of lines of code in a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Number of non-empty, non-comment lines
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        loc = 0
        in_multiline_string = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
                
            # Handle multiline strings (simple heuristic)
            if '"""' in stripped or "'''" in stripped:
                count = stripped.count('"""') + stripped.count("'''")
                if count % 2 == 1:
                    in_multiline_string = not in_multiline_string
                if in_multiline_string:
                    continue
                    
            # Skip single-line comments
            if stripped.startswith('#'):
                continue
                
            loc += 1
            
        return loc
        
    except Exception as e:
        logger.warning(f"Could not count LOC for {file_path}: {e}")
        return 0

def aggregate_vulnerability_counts(
    report_items: List[Dict[str, Any]],
    base_dirs: Dict[str, Path]
) -> pd.DataFrame:
    """
    Aggregate Bandit results into a DataFrame with vulnerability counts per file.
    
    Args:
        report_items: List of vulnerability findings from Bandit
        base_dirs: Dictionary mapping source types to base directories
        
    Returns:
        DataFrame with columns: task_id, source_type, file_path, lines_of_code, vulnerability_count
    """
    # Group findings by file_path
    file_findings = {}
    
    for item in report_items:
        file_path = item.get("filename", "")
        if not file_path:
            continue
            
        if file_path not in file_findings:
            file_findings[file_path] = []
        file_findings[file_path].append(item)
        
    # Build the results list
    results = []
    
    for file_path_str, findings in file_findings.items():
        file_path = Path(file_path_str)
        task_id, source_type = extract_task_id_and_source_type(file_path, base_dirs)
        
        if task_id is None:
            logger.warning(f"Skipping file with unknown task_id: {file_path}")
            continue
            
        loc = count_lines_of_code(file_path)
        vuln_count = len(findings)
        
        results.append({
            "task_id": task_id,
            "source_type": source_type,
            "file_path": file_path_str,
            "lines_of_code": loc,
            "vulnerability_count": vuln_count
        })
        
    df = pd.DataFrame(results)
    logger.info(f"Aggregated vulnerability counts for {len(df)} files")
    return df

def main():
    """
    Main entry point for the analysis module.
    
    Executes Bandit on all Python files in data/generated/ and data/human/,
    parses the results, and writes two output files:
    1. data/processed/raw_vulnerability_reports.json (full Bandit details)
    2. data/processed/raw_vulnerability_counts.csv (aggregated counts)
    """
    config = get_config()
    paths = get_paths()
    
    # Ensure output directories exist
    ensure_directories([paths["processed"]])
    
    # Define directories to scan
    generated_dir = paths["generated"]
    human_dir = paths["human"]
    
    # Find all Python files
    logger.info(f"Scanning {generated_dir} and {human_dir} for Python files...")
    python_files = []
    
    if generated_dir.exists():
        python_files.extend(find_python_files(generated_dir))
    if human_dir.exists():
        python_files.extend(find_python_files(human_dir))
        
    if not python_files:
        logger.error("No Python files found to scan. Ensure data has been generated.")
        # Create empty output files to indicate completion
        empty_report = {"results": [], "errors": []}
        with open(paths["raw_reports"], 'w') as f:
            json.dump(empty_report, f, indent=2)
        pd.DataFrame(columns=["task_id", "source_type", "file_path", "lines_of_code", "vulnerability_count"]).to_csv(
            paths["raw_counts"], index=False
        )
        return
        
    # Run Bandit
    bandit_config = paths["bandit_config"]
    if not bandit_config.exists():
        logger.error(f"Bandit config not found: {bandit_config}")
        return
        
    success = run_bandit_scan(python_files, paths["raw_reports"], bandit_config)
    
    if not success:
        logger.error("Bandit scan failed.")
        return
        
    # Parse the report
    report_items = parse_bandit_report(paths["raw_reports"])
    
    # Save the raw report (already saved by Bandit, but we ensure it's in the right place)
    # The raw report is already written by run_bandit_scan to paths["raw_reports"]
    logger.info(f"Raw vulnerability report saved to {paths['raw_reports']}")
    
    # Aggregate counts
    base_dirs = {
        "generated": generated_dir,
        "human": human_dir
    }
    counts_df = aggregate_vulnerability_counts(report_items, base_dirs)
    
    # Save the counts CSV
    counts_df.to_csv(paths["raw_counts"], index=False)
    logger.info(f"Vulnerability counts saved to {paths['raw_counts']}")
    
    # Log summary
    total_files = len(counts_df)
    total_vulns = counts_df["vulnerability_count"].sum()
    logger.info(f"Analysis complete: {total_files} files scanned, {total_vulns} vulnerabilities found.")

if __name__ == "__main__":
    main()
