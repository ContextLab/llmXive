import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from utils.config import get_config

def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from a file for the manifest."""
    if not file_path.exists():
        return {
            "path": str(file_path),
            "exists": False,
            "size_bytes": 0,
            "modified": None,
            "type": "unknown"
        }
    
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "exists": True,
        "size_bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "type": file_path.suffix or "file"
    }

def generate_manifest(output_path: Path, data_dir: Path) -> Dict[str, Any]:
    """
    Generate a manifest.json file documenting the data collection process,
    API endpoints used, parameters, and timestamps to satisfy Constitution 
    Principle VI (Empirical Data Collection Transparency).
    
    Args:
        output_path: Path where the manifest.json will be written
        data_dir: Path to the data directory to scan for artifacts
    
    Returns:
        Dictionary containing the manifest data
    """
    config = get_config()
    timestamp = datetime.now(timezone.utc)
    
    manifest = {
        "version": "1.0.0",
        "generated_at": timestamp.isoformat(),
        "project_id": "PROJ-508-evaluating-the-impact-of-llm-based-code-",
        "constitution_principle": "VI - Empirical Data Collection Transparency",
        "data_collection": {
            "source": "GitHub API",
            "api_endpoints": [
                {
                    "endpoint": "https://api.github.com/repos/{owner}/{repo}",
                    "method": "GET",
                    "parameters": ["owner", "repo"],
                    "description": "Repository metadata"
                },
                {
                    "endpoint": "https://api.github.com/repos/{owner}/{repo}/pulls",
                    "method": "GET",
                    "parameters": ["owner", "repo", "state", "per_page", "page"],
                    "description": "Pull request list"
                },
                {
                    "endpoint": "https://api.github.com/repos/{owner}/{repo}/commits",
                    "method": "GET",
                    "parameters": ["owner", "repo", "sha", "per_page", "page"],
                    "description": "Commit history"
                },
                {
                    "endpoint": "https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                    "method": "GET",
                    "parameters": ["owner", "repo", "path", "ref"],
                    "description": "File content (for .cursorrules, README, etc.)"
                }
            ],
            "rate_limit_handling": {
                "retries": 3,
                "delay_seconds": 1,
                "retry_codes": [429, 500, 502, 503]
            },
            "filters_applied": [
                "Repositories with >= 10 PRs in last 12 months",
                "Excluded forks",
                "Excluded archived repositories"
            ]
        },
        "parameters": {
            "time_window": "12 months",
            "min_pr_count": 10,
            "llm_adoption_threshold": 0.05,  # 5% Copilot mention frequency
            "ai_noise_threshold": 0.3,  # diff_complexity_score threshold
            "vif_threshold": 5.0
        },
        "artifacts": {
            "input_files": [],
            "output_files": []
        },
        "environment": {
            "python_version": config.get("python_version", "3.11"),
            "timestamp_utc": timestamp.isoformat(),
            "hostname": os.uname().nodename if hasattr(os, 'uname') else "unknown"
        }
    }
    
    # Scan data directory for artifacts
    if data_dir.exists():
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(data_dir.parent)
                file_meta = get_file_metadata(file_path)
                file_meta["relative_path"] = str(rel_path)
                
                if "raw" in str(file_path):
                    manifest["artifacts"]["input_files"].append(file_meta)
                elif "derived" in str(file_path) or "results" in str(file_path):
                    manifest["artifacts"]["output_files"].append(file_meta)
    
    return manifest

def write_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Write the manifest dictionary to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Manifest written to {output_path}")

def main():
    """Main entry point for manifest generation."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = get_config()
    project_root = config.get("project_root", Path.cwd())
    data_dir = project_root / "data"
    output_path = project_root / "data" / "manifest.json"
    
    logging.info(f"Generating manifest for project at {project_root}")
    logging.info(f"Scanning data directory: {data_dir}")
    
    try:
        manifest = generate_manifest(output_path, data_dir)
        write_manifest(manifest, output_path)
        logging.info("Manifest generation completed successfully.")
    except Exception as e:
        logging.error(f"Manifest generation failed: {e}")
        raise

if __name__ == "__main__":
    main()
