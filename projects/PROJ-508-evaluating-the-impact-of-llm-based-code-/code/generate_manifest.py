"""
Generate data/manifest.json documenting the data lineage, API endpoints,
parameters, and timestamps for the derived dataset.
"""
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
MANIFEST_PATH = DATA_DERIVED_DIR / "manifest.json"
MASTER_DATASET_PATH = DATA_DERIVED_DIR / "master_dataset.csv"


def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Get metadata for a file: size, modified time, and row count if CSV."""
    if not file_path.exists():
        return {
            "exists": False,
            "error": f"File not found: {file_path}"
        }

    stat = file_path.stat()
    metadata = {
        "exists": True,
        "size_bytes": stat.st_size,
        "modified_timestamp": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "absolute_path": str(file_path.resolve())
    }

    # Count rows for CSV
    if file_path.suffix == '.csv':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Count lines excluding header
                line_count = sum(1 for _ in f) - 1
                metadata["row_count"] = max(0, line_count)
        except Exception as e:
            metadata["row_count_error"] = str(e)

    return metadata


def generate_manifest() -> Dict[str, Any]:
    """
    Construct the manifest dictionary containing:
    - Generated timestamp
    - API Endpoints (GitHub API configuration used)
    - Parameters (hardcoded defaults or env vars used for ingestion)
    - Data Artifacts (metadata for master_dataset.csv)
    """
    # Simulate API configuration (matches code/ingest.py usage)
    # In a real scenario, these would be read from code/utils/config.py
    api_config = {
        "provider": "GitHub REST API",
        "base_url": "https://api.github.com",
        "version": "v3",
        "rate_limit_info": "Standard tier (5000 req/hr)",
        "auth_method": "PAT (Personal Access Token) via GITHUB_TOKEN env var"
    }

    # Parameters used for ingestion (derived from tasks T021-T028 logic)
    ingestion_params = {
        "min_prs_12m": 10,
        "llm_detection_methods": [
            "file_presence (.cursorrules, .copilot)",
            "readme_keyword_scan (Copilot, LLM)",
            "commit_message_frequency (>= 5% 'Copilot' or 'LLM')"
        ],
        "iteration_count_logic": "Total push events between PR open and merge (no exclusions)",
        "domain_complexity_metric": "unique_languages + dependency_count"
    }

    # Artifact metadata
    artifacts = []
    if MASTER_DATASET_PATH.exists():
        artifacts.append({
            "name": "master_dataset.csv",
            "description": "Derived dataset containing PR metadata, LLM adoption flags, and cognitive load proxies.",
            "path": str(MASTER_DATASET_PATH.relative_to(PROJECT_ROOT)),
            "format": "CSV",
            **get_file_metadata(MASTER_DATASET_PATH)
        })
    else:
        # Include placeholder if file missing (script should ideally run after T028)
        artifacts.append({
            "name": "master_dataset.csv",
            "description": "Derived dataset (MISSING - run code/generate_master_dataset.py first).",
            "path": str(MASTER_DATASET_PATH.relative_to(PROJECT_ROOT)),
            "format": "CSV",
            "exists": False
        })

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_id": "PROJ-508-evaluating-the-impact-of-llm-based-code-",
        "version": "1.0.0",
        "api_endpoints": api_config,
        "ingestion_parameters": ingestion_params,
        "artifacts": artifacts,
        "schema_reference": "specs/001-evaluating-the-impact-of-llm-based-code/data-model.md"
    }

    return manifest


def write_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Write the manifest to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest written to: {output_path}")


def main():
    """Entry point to generate the manifest."""
    print("Generating data manifest...")
    manifest = generate_manifest()
    write_manifest(manifest, MANIFEST_PATH)
    print("Done.")


if __name__ == "__main__":
    main()
