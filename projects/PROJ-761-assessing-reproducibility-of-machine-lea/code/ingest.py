"""
Ingestion module for the reproducibility pipeline.

This module handles:
1. Loading and validating the PaperManifest against a JSON schema.
2. Fetching datasets from remote sources (URLs) or local paths.
3. Extracting supplementary material based on manifest patterns or standard conventions.
"""

import json
import os
import re
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml
from jsonschema import validate, ValidationError
from jsonschema.exceptions import SchemaError

# Constants for standard supplementary naming conventions
SUPP_PATTERNS = [
    r".*_supp\.csv",
    r".*_supplementary\.csv",
    r".*_data\.parquet",
    r".*_raw\.csv",
    r".*_dataset\.csv",
]

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the manifest file (YAML or JSON).
    Defaults to data/manifest.yaml if not provided.
    """
    if manifest_path is None:
        manifest_path = PROJECT_ROOT / "data" / "manifest.yaml"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Try YAML first, then JSON
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError("Manifest file is neither valid YAML nor JSON")


def validate_manifest(manifest: Dict[str, Any], schema_path: Optional[Path] = None) -> bool:
    """
    Validate the manifest against the PaperManifest JSON schema.
    """
    if schema_path is None:
        schema_path = CONTRACTS_DIR / "PaperManifest.json"

    if not schema_path.exists():
        # If schema doesn't exist yet, we can't validate strictly, but we can do basic checks
        # For T005, we assume the schema might be created in T006, but we need to be robust.
        # We will perform a basic structural check if the schema is missing.
        required_fields = ["doi", "title", "datasets"]
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Manifest missing required field: {field}")
        return True

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        validate(instance=manifest, schema=schema)
        return True
    except (SchemaError, ValidationError) as e:
        raise ValueError(f"Manifest validation failed: {e}")


def fetch_dataset(url: str, output_dir: Path) -> Path:
    """
    Fetch a dataset from a URL and save it to the output directory.
    Handles direct downloads and basic archive extraction (zip, tar).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0]
    local_path = output_dir / filename

    print(f"Downloading {url} to {local_path}...")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download {url}: {e}")

    # Check if it's an archive
    if filename.endswith(".zip"):
        extract_path = output_dir / filename.replace(".zip", "")
        extract_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(local_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        return extract_path
    elif filename.endswith((".tar.gz", ".tgz")):
        extract_path = output_dir / filename.replace(".tar.gz", "").replace(".tgz", "")
        extract_path.mkdir(parents=True, exist_ok=True)
        with tarfile.open(local_path, "r:gz") as tar_ref:
            tar_ref.extractall(extract_path)
        return extract_path
    elif filename.endswith(".tar"):
        extract_path = output_dir / filename.replace(".tar", "")
        extract_path.mkdir(parents=True, exist_ok=True)
        with tarfile.open(local_path, "r") as tar_ref:
            tar_ref.extractall(extract_path)
        return extract_path

    return local_path


def find_supplementary_files(source_dir: Path, manifest_patterns: Optional[List[str]] = None) -> List[Path]:
    """
    Find supplementary files in a directory based on manifest patterns or standard conventions.
    """
    found_files = []
    all_files = list(source_dir.rglob("*"))

    # Compile patterns
    patterns = []
    if manifest_patterns:
        patterns.extend(manifest_patterns)
    patterns.extend(SUPP_PATTERNS)

    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

    for file_path in all_files:
        if file_path.is_file():
            filename = file_path.name
            for pattern in compiled_patterns:
                if pattern.match(filename):
                    found_files.append(file_path)
                    break

    return found_files


def process_manifest_entry(entry: Dict[str, Any], base_output_dir: Path) -> Dict[str, Any]:
    """
    Process a single dataset entry from the manifest.
    Returns a result dict with status and paths.
    """
    result = {
        "doi": entry.get("doi", "unknown"),
        "dataset_name": entry.get("name", "unknown"),
        "status": "success",
        "message": "",
        "files": []
    }

    source_type = entry.get("source_type", "url")
    source_location = entry.get("location")

    if not source_location:
        result["status"] = "failed"
        result["message"] = "Missing source location"
        return result

    try:
        if source_type == "url":
            fetch_path = fetch_dataset(source_location, base_output_dir)
            if isinstance(fetch_path, Path) and fetch_path.is_file():
                # If it's a single file, just add it
                result["files"].append(str(fetch_path))
            elif isinstance(fetch_path, Path) and fetch_path.is_dir():
                # If it's a directory, look for data files inside
                data_files = find_supplementary_files(fetch_path, entry.get("patterns"))
                if not data_files:
                    # Fallback: if no specific patterns found, take all CSV/Parquet
                    data_files = list(fetch_path.rglob("*.csv")) + list(fetch_path.rglob("*.parquet"))
                result["files"].extend([str(f) for f in data_files])
        elif source_type == "local":
            local_path = Path(source_location)
            if not local_path.exists():
                result["status"] = "failed"
                result["message"] = f"Local path not found: {local_path}"
                return result

            if local_path.is_file():
                result["files"].append(str(local_path))
            elif local_path.is_dir():
                data_files = find_supplementary_files(local_path, entry.get("patterns"))
                if not data_files:
                    data_files = list(local_path.rglob("*.csv")) + list(local_path.rglob("*.parquet"))
                result["files"].extend([str(f) for f in data_files])
        else:
            result["status"] = "failed"
            result["message"] = f"Unsupported source type: {source_type}"

        if not result["files"]:
            result["status"] = "failed"
            result["message"] = "No data files found matching patterns"

    except Exception as e:
        result["status"] = "failed"
        result["message"] = str(e)

    return result


def ingest_pipeline(manifest_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Main entry point for the ingestion pipeline.
    1. Load manifest.
    2. Validate manifest.
    3. Fetch/Process each dataset entry.
    4. Return results.
    """
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)

    results = []
    datasets = manifest.get("datasets", [])

    if not datasets:
        print("No datasets found in manifest.")
        return results

    for entry in datasets:
        print(f"Processing dataset: {entry.get('name', 'Unknown')}")
        result = process_manifest_entry(entry, DATA_RAW_DIR)
        results.append(result)
        print(f"  Status: {result['status']}")
        if result['status'] == 'failed':
            print(f"  Error: {result['message']}")
        else:
            print(f"  Files: {len(result['files'])}")

    return results


def main():
    """
    CLI entry point for ingestion.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Ingest and validate research data.")
    parser.add_argument("--manifest", type=str, default=None, help="Path to manifest file")
    args = parser.parse_args()

    try:
        results = ingest_pipeline(Path(args.manifest) if args.manifest else None)
        # Write a summary log
        log_path = DATA_RAW_DIR / "ingestion_log.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Ingestion complete. Log saved to {log_path}")
    except Exception as e:
        print(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()