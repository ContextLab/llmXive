import os
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import local modules
from config import get_config_summary, ensure_directories
from utils import get_logger
from parallelism_config import get_max_concurrent_files, get_max_concurrent_repos

logger = get_logger(__name__)

def get_file_language(file_path: Path) -> str:
    """Determine file language based on extension."""
    ext = file_path.suffix.lower()
    mapping = {
        ".py": "python",
        ".java": "java",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust"
    }
    return mapping.get(ext, "unknown")

def run_radon_on_file(file_path: Path) -> Dict[str, Any]:
    """Run Radon on a Python file."""
    try:
        # Assuming radon is installed and available in PATH
        result = subprocess.run(
            ["radon", "cc", str(file_path), "-a", "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return {"error": result.stderr}
        
        # Parse JSON output (simplified)
        # Radon output is a list of dicts per function
        data = json.loads(result.stdout)
        cc_total = sum(item.get("complexity", 0) for item in data)
        return {
            "complexity": cc_total,
            "mi": 0 # MI calculation requires specific radon call, simplified here
        }
    except Exception as e:
        logger.warning(f"Radon failed on {file_path}: {e}")
        return {"error": str(e)}

def run_semgrep_on_file(file_path: Path) -> Dict[str, Any]:
    """Run Semgrep on a file."""
    try:
        # Simplified semgrep invocation
        result = subprocess.run(
            ["semgrep", "--metrics", "off", "--quiet", "--json", str(file_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0 and result.stdout.strip() == "":
            return {"smells": 0, "complexity": 0}
        
        data = json.loads(result.stdout)
        findings = data.get("results", [])
        smells = len(findings)
        # Semgrep doesn't directly output CC per file in simple mode, 
        # we might approximate or rely on Radon for Python.
        return {
            "smells": smells,
            "complexity": 0 
        }
    except Exception as e:
        logger.warning(f"Semgrep failed on {file_path}: {e}")
        return {"error": str(e)}

def process_repository(repo_path: Path) -> List[Dict[str, Any]]:
    """
    Process all files in a repository with parallelism constraints.
    
    This function respects the file-level concurrency limit.
    """
    max_workers = get_max_concurrent_files()
    results = []
    
    # Collect files
    files_to_process = []
    for ext in [".py", ".java", ".js", ".ts", ".go", ".rs"]:
        files_to_process.extend(repo_path.rglob(f"*{ext}"))
    
    logger.info(f"Found {len(files_to_process)} files to analyze in {repo_path.name}. Max workers: {max_workers}")
    
    def analyze_file(f_path: Path) -> Optional[Dict[str, Any]]:
        lang = get_file_language(f_path)
        if lang == "unknown":
            return None
        
        metrics = {"file": str(f_path), "language": lang}
        
        if lang == "python":
            radon_res = run_radon_on_file(f_path)
            metrics["complexity"] = radon_res.get("complexity", 0)
            metrics["smells"] = 0 # Radon doesn't do smells like Semgrep
        else:
            semgrep_res = run_semgrep_on_file(f_path)
            metrics["smells"] = semgrep_res.get("smells", 0)
            metrics["complexity"] = 0 # Semgrep CC not directly exposed here
        
        return metrics

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(analyze_file, f): f for f in files_to_process}
        for future in as_completed(future_to_file):
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception as e:
                logger.error(f"Error analyzing file: {e}")
    
    return results

def run_static_analysis(repos_dir: Path, output_path: Path) -> None:
    """Run static analysis on all cloned repositories."""
    ensure_directories(output_path.parent)
    
    repos = [d for d in repos_dir.iterdir() if d.is_dir()]
    logger.info(f"Running static analysis on {len(repos)} repositories.")
    
    all_results = []
    
    # We can also parallelize across repos, but the task specifically asks for 
    # limiting concurrent repo processes. We'll use a simple loop here 
    # assuming the repo-level parallelism is handled in data_extraction.py 
    # or we can wrap this in a ThreadPoolExecutor with get_max_concurrent_repos().
    
    max_repo_workers = get_max_concurrent_repos()
    with ThreadPoolExecutor(max_workers=max_repo_workers) as executor:
        future_to_repo = {executor.submit(process_repository, repo): repo for repo in repos}
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                results = future.result()
                all_results.extend(results)
                logger.info(f"Completed analysis for {repo.name}")
            except Exception as e:
                logger.error(f"Error processing repo {repo.name}: {e}")
    
    import pandas as pd
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved static analysis results to {output_path}")
    else:
        logger.warning("No static analysis results generated.")

def main():
    from config import get_config_summary
    config = get_config_summary()
    repos_dir = Path(config["paths"]["data_raw"]) / "clones" # Adjust path as needed
    output_path = Path(config["paths"]["data_processed"]) / "static_analysis_metrics.csv"
    run_static_analysis(repos_dir, output_path)

if __name__ == "__main__":
    main()
