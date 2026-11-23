"""
URL Validation Module for llmXive Project PROJ-282.

Implements Constitution II: Data Integrity & Source Verification.
Validates dataset URLs against the research.md manifest to ensure
all data sources are real, accessible, and correctly referenced.
"""

import os
import re
import sys
import requests
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESEARCH_MD_PATH = PROJECT_ROOT / "research.md"

# Expected manifest keys in research.md
DATASET_MANIFEST_KEY = "dataset_manifest"
URL_PATTERN = re.compile(
    r'https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)', re.IGNORECASE)

class URLValidationError(Exception):
    """Raised when a URL validation fails."""
    pass

def load_research_manifest() -> Dict:
    """
    Parses research.md to extract the dataset manifest section.
    Expects a YAML block or a structured list of URLs under 'dataset_manifest'.
    """
    if not RESEARCH_MD_PATH.exists():
        raise FileNotFoundError(f"research.md not found at {RESEARCH_MD_PATH}")

    content = RESEARCH_MD_PATH.read_text(encoding='utf-8')

    # Attempt to find a YAML block (--- ... ---) or a specific section
    # Assuming the manifest is defined in a YAML block or a clear list format
    yaml_block = re.search(r'```yaml\s*(.*?)\s*```', content, re.DOTALL)
    
    manifest = {}
    if yaml_block:
        try:
            manifest = yaml.safe_load(yaml_block.group(1)) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML block in research.md: {e}")
    else:
        # Fallback: Try to parse a section header manually if no code block
        # This is a heuristic; strict YAML blocks are preferred.
        if DATASET_MANIFEST_KEY in content:
            # Simple heuristic: extract lines after the key until next header
            lines = content.split('\n')
            in_manifest = False
            manifest_lines = []
            for line in lines:
                if DATASET_MANIFEST_KEY in line:
                    in_manifest = True
                    continue
                if in_manifest:
                    if line.startswith('#') and 'dataset_manifest' not in line.lower():
                        break
                    manifest_lines.append(line)
            if manifest_lines:
                try:
                    # Try to join and parse as YAML list/dict
                    manifest = yaml.safe_load('\n'.join(manifest_lines)) or {}
                except yaml.YAMLError:
                    pass

    if not manifest or DATASET_MANIFEST_KEY not in manifest:
        # If the key isn't in a block, maybe the whole file is the structure or key is top level
        # Try parsing the whole file if it looks like YAML (unlikely for .md, but safe fallback)
        # Or assume the user put the list directly under the key in text format
        # For robustness, we assume the YAML block is the source of truth.
        raise ValueError(f"Could not find '{DATASET_MANIFEST_KEY}' section in research.md")

    return manifest.get(DATASET_MANIFEST_KEY, {})

def validate_url_accessibility(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Checks if a URL is accessible (HTTP 200 or 302 for redirects).
    Returns (is_valid, message).
    """
    if not URL_PATTERN.match(url):
        return False, f"Invalid URL format: {url}"

    try:
        # Use HEAD first, fallback to GET if HEAD not allowed
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 405: # Method Not Allowed
            response = requests.get(url, timeout=timeout, stream=True)
            # If we just need to check existence, we can stop after headers
            response.close()
        
        if response.status_code == 200:
            return True, "Accessible"
        elif response.status_code == 301 or response.status_code == 302:
            return True, "Redirected (Accessible)"
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"

def validate_dataset_urls(manifest: Optional[Dict] = None) -> Dict[str, Dict]:
    """
    Validates all URLs found in the dataset manifest.
    
    Args:
        manifest: Optional pre-loaded manifest. If None, loads from research.md.
    
    Returns:
        Dict mapping dataset name to validation status:
        {
            "dataset_name": {
                "url": "...",
                "valid": True/False,
                "message": "Accessible" or "Error..."
            }
        }
    """
    if manifest is None:
        manifest = load_research_manifest()

    results = {}
    
    # Flatten potential nested structures if the manifest is a list of objects
    datasets = []
    if isinstance(manifest, list):
        datasets = manifest
    elif isinstance(manifest, dict):
        # Assume keys are dataset names and values are URL strings or dicts with 'url'
        for name, value in manifest.items():
            if isinstance(value, dict) and 'url' in value:
                datasets.append({'name': name, 'url': value['url']})
            elif isinstance(value, str):
                datasets.append({'name': name, 'url': value})
    
    if not datasets:
        raise ValueError("No datasets found in manifest to validate.")

    for item in datasets:
        name = item.get('name', 'unknown')
        url = item.get('url')
        
        if not url:
            results[name] = {
                "url": None,
                "valid": False,
                "message": "No URL provided in manifest"
            }
            continue

        is_valid, message = validate_url_accessibility(url)
        results[name] = {
            "url": url,
            "valid": is_valid,
            "message": message
        }

    return results

def main():
    """
    CLI entry point for URL validation.
    Prints results and exits with code 1 if any URL is invalid.
    """
    print("Starting URL validation against research.md manifest...")
    try:
        results = validate_dataset_urls()
        
        all_valid = True
        print(f"\n{'Dataset':<30} {'Status':<10} {'Message'}")
        print("-" * 70)
        
        for name, data in results.items():
            status = "VALID" if data['valid'] else "INVALID"
            if not data['valid']:
                all_valid = False
            print(f"{name:<30} {status:<10} {data['message']}")
        
        print("-" * 70)
        if all_valid:
            print("SUCCESS: All dataset URLs are valid and accessible.")
            sys.exit(0)
        else:
            print("FAILURE: One or more dataset URLs are invalid or inaccessible.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: Manifest parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
