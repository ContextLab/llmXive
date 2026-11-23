"""
Citation and Data Source Verification Module.

This module verifies dataset URLs listed in `data_sources.yaml` by performing:
1. HTTP 200 status checks to ensure availability.
2. Metadata schema validation against expected fields (title, author, year, url).
"""

import os
import sys
import time
import requests
import yaml
from pathlib import Path

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from src.utils.config import load_config, resolve_path


def load_data_sources(config_path: str = "data_sources.yaml") -> dict:
    """
    Load the data sources configuration from a YAML file.

    Args:
        config_path: Relative or absolute path to the YAML file.

    Returns:
        Dictionary containing the data sources configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    path = resolve_path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Data sources configuration not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_metadata_schema(metadata: dict, source_id: str) -> list[str]:
    """
    Validates that the metadata dictionary contains required fields.

    Required fields: title, author, year, url.
    Optional fields: description, license, tags.

    Args:
        metadata: The metadata dictionary to validate.
        source_id: Identifier for the source (for logging purposes).

    Returns:
        A list of validation error messages. Empty if valid.
    """
    errors = []
    required_fields = ["title", "author", "year", "url"]

    for field in required_fields:
        if field not in metadata:
            errors.append(f"Source '{source_id}': Missing required field '{field}'")
        elif metadata[field] is None or (isinstance(metadata[field], str) and not metadata[field].strip()):
            errors.append(f"Source '{source_id}': Field '{field}' is empty or null")

    # Validate URL format if present
    if "url" in metadata and metadata["url"]:
        url = metadata["url"]
        if not (url.startswith("http://") or url.startswith("https://")):
            errors.append(f"Source '{source_id}': Invalid URL format '{url}'")

    return errors


def check_url_availability(url: str, timeout: int = 10) -> tuple[bool, int, str]:
    """
    Performs an HTTP HEAD request to check URL availability.

    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.

    Returns:
        Tuple of (is_available, status_code, message).
    """
    try:
        # Try HEAD first as it is lighter, fallback to GET if HEAD not allowed
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 405: # Method Not Allowed
            response = requests.get(url, timeout=timeout, allow_redirects=True)
        
        is_available = response.status_code == 200
        return is_available, response.status_code, response.reason or "OK" if is_available else "Not Found/Forbidden"
    except requests.exceptions.Timeout:
        return False, 0, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, 0, "Connection Error"
    except requests.exceptions.RequestException as e:
        return False, 0, str(e)


def run_citation_check(config_file: str = "data_sources.yaml") -> dict:
    """
    Main entry point to run the citation check against all defined data sources.

    Args:
        config_file: Path to the data_sources.yaml file.

    Returns:
        Dictionary containing the verification results.
    """
    print(f"Loading data sources from: {config_file}")
    try:
        sources = load_data_sources(config_file)
    except Exception as e:
        print(f"Error loading data sources: {e}")
        return {"success": False, "error": str(e), "results": []}

    if not sources or "sources" not in sources:
        print("No 'sources' key found in data_sources.yaml")
        return {"success": False, "error": "Missing 'sources' key", "results": []}

    results = []
    total_sources = len(sources["sources"])
    passed = 0
    failed = 0

    print(f"Verifying {total_sources} data sources...")
    print("-" * 60)

    for source_id, metadata in sources["sources"].items():
        print(f"Checking: {source_id}")
        
        # 1. Schema Validation
        schema_errors = validate_metadata_schema(metadata, source_id)
        
        # 2. URL Availability Check
        url = metadata.get("url")
        url_ok = False
        status_code = 0
        status_msg = ""
        
        if url:
            url_ok, status_code, status_msg = check_url_availability(url)
            if not url_ok:
                schema_errors.append(f"URL check failed: {status_msg} ({status_code})")

        is_valid = len(schema_errors) == 0
        
        result_entry = {
            "id": source_id,
            "valid": is_valid,
            "url": url,
            "schema_errors": schema_errors,
            "http_status": status_code,
            "http_message": status_msg
        }
        results.append(result_entry)

        if is_valid:
            print(f"  [PASS] {source_id}")
            passed += 1
        else:
            print(f"  [FAIL] {source_id}")
            for err in schema_errors:
                print(f"       - {err}")
            failed += 1
        print("-" * 60)

    summary = {
        "total": total_sources,
        "passed": passed,
        "failed": failed,
        "success_rate": f"{(passed/total_sources*100):.2f}%" if total_sources > 0 else "0%"
    }

    final_report = {
        "success": failed == 0,
        "summary": summary,
        "results": results
    }

    # Save report to data/results
    output_dir = resolve_path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "citation_check_report.json"
    
    import json
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)
    
    print(f"\nReport saved to: {output_file}")
    print(f"Summary: {passed}/{total_sources} passed ({summary['success_rate']})")

    return final_report


if __name__ == "__main__":
    # Default path relative to project root
    config_path = "data_sources.yaml"
    
    # Allow override via command line argument
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    result = run_citation_check(config_path)
    
    # Exit with error code if any checks failed
    if not result["success"]:
        sys.exit(1)
    else:
        sys.exit(0)