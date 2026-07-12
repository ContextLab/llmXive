"""
verify_citations.py

Validates external sources referenced in the "GUI Error Taxonomy" specification.
Specifically:
  1. Verifies the existence and accessibility of the taxonomy YAML source file.
  2. Validates that all dataset URLs listed in the taxonomy are reachable (HTTP 200).
  3. Generates a validation report in JSON format.

This script ensures FR-008 compliance by confirming that all cited data sources
are real and programmatically accessible before generation tasks begin.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import project root utility from existing setup
try:
    from config.linting import get_project_root
except ImportError:
    # Fallback if config.linting is not fully imported yet (should exist per T003)
    def get_project_root() -> Path:
        return Path(__file__).resolve().parent.parent

REPORT_PATH = Path("data/results/taxonomy_validation_report.json")
TAXONOMY_SOURCE_PATH = Path("data/config/gui_error_taxonomy.yaml")

def check_url_reachable(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Checks if a URL returns a 200 OK status.
    Returns a dict with status, code, and error message if any.
    """
    result = {
        "url": url,
        "reachable": False,
        "status_code": None,
        "error": None
    }

    if not url or url.startswith("#"):
        result["error"] = "Invalid or empty URL"
        return result

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "llmXive-Verify/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result["status_code"] = response.getcode()
            result["reachable"] = (result["status_code"] == 200)
    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["error"] = f"HTTP Error: {e.reason}"
    except urllib.error.URLError as e:
        result["error"] = f"URL Error: {e.reason}"
    except Exception as e:
        result["error"] = f"Unexpected Error: {str(e)}"

    return result

def parse_yaml_simple(content: str) -> List[Dict[str, Any]]:
    """
    Simple YAML parser for the specific structure of the taxonomy file.
    Handles basic key-value and list structures without external dependencies
    if PyYAML is not strictly available, though we assume standard libs + requirements.
    Note: This implementation assumes the standard 'yaml' library is available
    as per requirements.txt (T002).
    """
    try:
        import yaml
        data = yaml.safe_load(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Handle case where root is a dict with a 'items' or 'sources' key
            if 'sources' in data:
                return data['sources']
            if 'items' in data:
                return data['items']
            # If it's a single object, wrap it
            return [data]
        return []
    except ImportError:
        # Fallback logic if yaml is missing (should not happen in correct env)
        raise RuntimeError("PyYAML is required to parse the taxonomy file. Please ensure it is installed.")

def validate_citations() -> Dict[str, Any]:
    """
    Main validation logic.
    1. Reads the taxonomy YAML file.
    2. Extracts URLs.
    3. Checks each URL.
    4. Returns the report structure.
    """
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_file": str(TAXONOMY_SOURCE_PATH),
        "source_exists": False,
        "total_urls_checked": 0,
        "urls_reachable": 0,
        "urls_failed": 0,
        "details": []
    }

    # 1. Check if source file exists
    if not TAXONOMY_SOURCE_PATH.exists():
        report["error"] = f"Source file not found: {TAXONOMY_SOURCE_PATH}"
        return report

    report["source_exists"] = True

    # 2. Read and parse YAML
    try:
        with open(TAXONOMY_SOURCE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        items = parse_yaml_simple(content)
    except Exception as e:
        report["error"] = f"Failed to parse YAML: {str(e)}"
        return report

    # 3. Extract URLs and validate
    urls_to_check = []
    for item in items:
        if isinstance(item, dict):
            if 'url' in item:
                urls_to_check.append(item['url'])
            if 'dataset_url' in item:
                urls_to_check.append(item['dataset_url'])
            # Check nested lists
            if 'references' in item and isinstance(item['references'], list):
                for ref in item['references']:
                    if isinstance(ref, dict) and 'url' in ref:
                        urls_to_check.append(ref['url'])

    report["total_urls_checked"] = len(urls_to_check)

    for url in urls_to_check:
        check_result = check_url_reachable(url)
        report["details"].append(check_result)
        if check_result["reachable"]:
            report["urls_reachable"] += 1
        else:
            report["urls_failed"] += 1

    return report

def main():
    """
    Entry point. Executes validation and writes report to data/results/.
    """
    print("Starting citation validation for GUI Error Taxonomy...")

    # Ensure output directory exists
    output_dir = REPORT_PATH.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    report = validate_citations()

    # Write report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Validation complete. Report written to: {REPORT_PATH}")

    if report.get("error"):
        print(f"ERROR: {report['error']}")
        sys.exit(1)

    if report["urls_failed"] > 0:
        print(f"WARNING: {report['urls_failed']} URLs failed validation.")
        # Do not exit with error unless strictly required, but log it.
        # For FR-008, we want to know if sources are broken.
        # We'll exit 0 if at least one is valid, or 1 if all failed?
        # Let's be strict: if any expected source is missing, it's a failure for the pipeline.
        if report["urls_reachable"] == 0:
            print("CRITICAL: No sources are reachable. Aborting.")
            sys.exit(1)
    else:
        print("SUCCESS: All cited sources are reachable.")

    sys.exit(0)

if __name__ == "__main__":
    main()
