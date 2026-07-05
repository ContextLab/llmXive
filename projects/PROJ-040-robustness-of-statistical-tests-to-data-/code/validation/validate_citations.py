"""
validate_citations.py

Verifies dataset URLs and checksums against the "# Verified datasets" block in plan.md.
Downloads files to data/raw/ if missing, computes SHA-256 hashes, and validates
against the expected hashes defined in plan.md.
"""
import hashlib
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

# Project root relative to this file (assuming code/validation/ is inside code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_MD_PATH = PROJECT_ROOT / "plan.md"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-040-robustness-of-statistical-tests-to-data-.yaml"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def parse_verified_datasets(plan_path: Path) -> list[dict]:
    """
    Parse the '# Verified datasets' block from plan.md.
    Expected format per line:
    - Dataset Name: <name> | URL: <url> | SHA256: <hash>
    """
    if not plan_path.exists():
        raise FileNotFoundError(f"plan.md not found at {plan_path}")

    content = plan_path.read_text()
    datasets = []
    in_block = False
    # Regex patterns to capture fields on a single line
    pattern_name = re.compile(r"-?\s*(?:\*|\-)?\s*(?:Dataset\s*)?Name:\s*(.+?)(?:\s*\||$)")
    pattern_url = re.compile(r"URL:\s*(.+?)(?:\s*\||$)")
    pattern_hash = re.compile(r"SHA256:\s*(.+?)(?:\s*\||$)")

    for line in content.splitlines():
        if "# Verified datasets" in line:
            in_block = True
            continue
        if in_block:
            # End block if a new section header appears
            if line.strip().startswith("#") and "Verified datasets" not in line:
                break
            if not line.strip():
                continue

            # Extract fields
            name_match = pattern_name.search(line)
            url_match = pattern_url.search(line)
            hash_match = pattern_hash.search(line)

            if name_match and url_match and hash_match:
                datasets.append({
                    "name": name_match.group(1).strip(),
                    "url": url_match.group(1).strip(),
                    "expected_hash": hash_match.group(1).strip().lower()
                })
    return datasets

def download_file(url: str, dest_path: Path) -> bool:
    """Download file from URL to dest_path. Returns True on success."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed for {url}: {e}")
        return False

def write_state_file(dataset_hashes: dict[str, str]):
    """
    Write the artifact_hashes map to the YAML state file.
    Format:
    artifact_hashes:
      filename1: hash1
      filename2: hash2
    """
    # Load existing state if it exists to preserve other keys, or start fresh
    state_data = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                state_data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            state_data = {}

    state_data["artifact_hashes"] = dataset_hashes

    with open(STATE_FILE, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"State file updated: {STATE_FILE}")

def main():
    print("Starting citation validation...")
    try:
        datasets = parse_verified_datasets(PLAN_MD_PATH)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not datasets:
        print("ERROR: No verified datasets found in plan.md.")
        sys.exit(1)

    print(f"Found {len(datasets)} dataset(s) to verify.")
    verified_hashes = {}
    all_valid = True

    for ds in datasets:
        name = ds["name"]
        url = ds["url"]
        expected_hash = ds["expected_hash"]
        
        # Derive filename from URL or name
        filename = Path(urlparse(url).path).name
        if not filename or '.' not in filename:
            filename = f"{name.replace(' ', '_').lower()}.csv"
        
        dest_path = DATA_RAW_DIR / filename

        # Download if missing
        if not dest_path.exists():
            print(f"Downloading {name} from {url}...")
            if not download_file(url, dest_path):
                print(f"FAIL: Could not download {name}.")
                all_valid = False
                continue
        else:
            print(f"Using existing file: {dest_path}")

        # Compute hash
        actual_hash = compute_sha256(dest_path)
        verified_hashes[filename] = actual_hash

        if actual_hash.lower() == expected_hash:
            print(f"PASS: {name} hash verified.")
        else:
            print(f"FAIL: {name} hash mismatch.")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {actual_hash}")
            all_valid = False

    # Update state file
    write_state_file(verified_hashes)

    if all_valid:
        print("\nAll citations verified successfully.")
        sys.exit(0)
    else:
        print("\nVerification failed for one or more datasets.")
        sys.exit(1)

if __name__ == "__main__":
    main()