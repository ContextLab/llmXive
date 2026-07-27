"""
Manifest Generation Module

Generates a JSON manifest file documenting the data pipeline's API endpoints,
parameters, and execution timestamps for reproducibility and auditing.
"""
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from utils.config import get_config

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"
MANIFEST_PATH = DERIVED_DIR / "manifest.json"


def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata for a specific file (size, modification time, line count).

    Args:
        file_path: Path to the file to analyze.

    Returns:
        Dictionary containing file metadata.
    """
    if not file_path.exists():
        return {
            "exists": False,
            "path": str(file_path)
        }

    stats = file_path.stat()
    line_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
    except Exception:
        pass

    return {
        "exists": True,
        "path": str(file_path.relative_to(PROJECT_ROOT)),
        "size_bytes": stats.st_size,
        "modified_timestamp": datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(),
        "line_count": line_count
    }


def generate_manifest() -> Dict[str, Any]:
    """
    Generate the complete manifest structure containing pipeline metadata,
    input/output artifacts, and execution context.

    Returns:
        Dictionary representing the full manifest.
    """
    config = get_config()
    timestamp = datetime.now(timezone.utc)

    # Collect input artifacts
    inputs = []
    raw_file = DATA_DIR / "raw" / "repo_list.csv"
    if raw_file.exists():
        inputs.append(get_file_metadata(raw_file))

    # Collect output artifacts
    outputs = []
    master_dataset = DERIVED_DIR / "master_dataset.csv"
    if master_dataset.exists():
        outputs.append(get_file_metadata(master_dataset))

    analysis_results = DERIVED_DIR / "analysis_results.json"
    if analysis_results.exists():
        outputs.append(get_file_metadata(analysis_results))

    # Define API endpoints documented in the pipeline
    # These represent the logical entry points for data access
    endpoints = [
        {
            "name": "ingest_repositories",
            "module": "code.ingest",
            "function": "run_ingestion",
            "description": "Fetches repository metadata and PR data from GitHub API",
            "parameters": {
                "repo_list_path": "Path to CSV containing repository list",
                "output_dir": "Directory for raw ingestion data"
            }
        },
        {
            "name": "calculate_metrics",
            "module": "code.utils.metrics",
            "function": "process_review_metrics",
            "description": "Calculates cognitive load proxy metrics (iteration_count, avg_comment_length, etc.)",
            "parameters": {
                "pr_data": "PR event data structure",
                "commit_data": "Commit event data structure"
            }
        },
        {
            "name": "run_analysis",
            "module": "code.analyze",
            "function": "run_analysis",
            "description": "Executes GLMM/ZINB models and sensitivity analysis",
            "parameters": {
                "dataset_path": "Path to master_dataset.csv",
                "model_type": "glmm or zinb"
            }
        },
        {
            "name": "generate_report",
            "module": "code.report",
            "function": "main",
            "description": "Generates final PDF report and visualizations",
            "parameters": {
                "results_path": "Path to analysis_results.json",
                "output_dir": "Directory for report outputs"
            }
        }
    ]

    manifest = {
        "version": "1.0.0",
        "project_id": "PROJ-508-evaluating-the-impact-of-llm-based-code-",
        "generated_at": timestamp.isoformat(),
        "generated_by": "generate_manifest.py",
        "environment": {
            "python_version": os.sys.version,
            "platform": os.sys.platform,
            "cwd": str(PROJECT_ROOT)
        },
        "pipeline": {
            "inputs": inputs,
            "outputs": outputs,
            "endpoints": endpoints,
            "config_snapshot": {
                "github_api_base": config.get("github_api_base", "https://api.github.com"),
                "data_dir": str(DATA_DIR),
                "derived_dir": str(DERIVED_DIR)
            }
        },
        "execution_context": {
            "task_id": "T029",
            "purpose": "Generate data manifest for reproducibility"
        }
    }

    return manifest


def write_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """
    Write the manifest dictionary to a JSON file.

    Args:
        manifest: The manifest dictionary to write.
        output_path: Path where the JSON file will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, default=str)


def main() -> None:
    """
    Main entry point for the manifest generation script.
    Generates the manifest and writes it to data/derived/manifest.json.
    """
    logging_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, logging_level, logging.INFO))
    logger = logging.getLogger(__name__)

    logger.info("Starting manifest generation...")

    try:
        manifest = generate_manifest()
        write_manifest(manifest, MANIFEST_PATH)
        logger.info(f"Manifest successfully written to {MANIFEST_PATH}")
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
