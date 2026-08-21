"""
Task T004a: Resolve Zenodo ID.

Reads the idea file to extract the specific Zenodo Accession ID and URL.
Writes the resolved ID to a file for downstream tasks to consume.
"""
import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

# Project root relative to this script's location (code/)
PROJECT_ROOT = Path(__file__).parent.parent
IDEA_DIR = PROJECT_ROOT / "idea"
OUTPUT_FILE = PROJECT_ROOT / "data" / "zenodo_id.txt"
LOG_FILE = PROJECT_ROOT / "logs" / "resolve_zenodo.log"

def find_idea_file() -> Optional[Path]:
    """Locate the idea file 'predicting-molecular-properties-from-qua.md'."""
    if not IDEA_DIR.exists():
        print(f"Error: Idea directory not found at {IDEA_DIR}", file=sys.stderr)
        return None

    target_file = IDEA_DIR / "predicting-molecular-properties-from-qua.md"
    if target_file.exists():
        return target_file

    # Fallback: search for any .md file in the idea directory
    md_files = list(IDEA_DIR.glob("*.md"))
    if md_files:
        print(f"Warning: Specific idea file not found. Using first available: {md_files[0]}", file=sys.stderr)
        return md_files[0]

    print(f"Error: No .md files found in {IDEA_DIR}", file=sys.stderr)
    return None

def extract_zenodo_id(file_path: Path) -> Optional[Tuple[str, str]]:
    """
    Extract Zenodo ID and URL from the idea file.
    Returns (zenodo_id, url) or None if not found.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return None

    # Pattern 1: "Zenodo ID: 1234567" or "Accession ID: 1234567"
    # Pattern 2: "https://doi.org/10.5281/zenodo.1234567"
    # Pattern 3: "zenodo.1234567"

    zenodo_id = None
    zenodo_url = None

    # Look for DOI pattern first (most reliable)
    doi_pattern = r'10\.5281/zenodo\.(\d+)'
    doi_matches = re.findall(doi_pattern, content)
    if doi_matches:
        zenodo_id = doi_matches[0]
        zenodo_url = f"https://doi.org/10.5281/zenodo.{zenodo_id}"
        return (zenodo_id, zenodo_url)

    # Look for direct ID mention
    id_pattern = r'(?:Zenodo\s*(?:ID|Accession|Number)[:\s]+)?(\d{4,})'
    id_matches = re.findall(id_pattern, content, re.IGNORECASE)
    if id_matches:
        # Filter for likely Zenodo IDs (usually 6+ digits)
        for match in id_matches:
            if len(match) >= 6:
                zenodo_id = match
                zenodo_url = f"https://zenodo.org/records/{zenodo_id}"
                return (zenodo_id, zenodo_url)

    print("Warning: Could not extract Zenodo ID from the idea file.", file=sys.stderr)
    return None

def main():
    """Main entry point for T004a."""
    print("Starting T004a: Resolve Zenodo ID")

    # Ensure output directories exist
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    idea_file = find_idea_file()
    if not idea_file:
        print("Failed to locate idea file. Cannot resolve Zenodo ID.", file=sys.stderr)
        return 1

    result = extract_zenodo_id(idea_file)
    if not result:
        print("Failed to extract Zenodo ID from idea file.", file=sys.stderr)
        return 1

    zenodo_id, zenodo_url = result

    # Write the resolved ID to the output file
    try:
        OUTPUT_FILE.write_text(f"{zenodo_id}\n", encoding="utf-8")
        print(f"Successfully resolved Zenodo ID: {zenodo_id}")
        print(f"URL: {zenodo_url}")
        print(f"Output written to: {OUTPUT_FILE}")
        return 0
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
