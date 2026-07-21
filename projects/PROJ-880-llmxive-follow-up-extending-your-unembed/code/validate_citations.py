"""
Citation validation module.
Parses markdown, extracts URLs, and verifies against a manifest.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

def load_manifest(manifest_path: Path) -> Dict[str, str]:
    """Load the citation manifest."""
    if not manifest_path.exists():
        return {}
    with open(manifest_path, "r") as f:
        return json.load(f)

def extract_urls_from_markdown(md_path: Path) -> List[str]:
    """Extract URLs from a markdown file."""
    with open(md_path, "r") as f:
        content = f.read()
    
    # Regex for markdown links [text](url)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, content)
    return [url for _, url in matches]

def verify_citations(urls: List[str], manifest: Dict[str, str]) -> Dict[str, bool]:
    """Verify URLs against the manifest."""
    results = {}
    for url in urls:
        # Check if URL is in manifest or matches a key
        found = False
        for key, value in manifest.items():
            if url == key or url == value or key in url:
                results[url] = True
                found = True
                break
        if not found:
            results[url] = False
    return results

def main():
    """Run citation validation."""
    parser = argparse.ArgumentParser(description="Validate citations in markdown files.")
    parser.add_argument("--md", type=str, required=True, help="Path to markdown file")
    parser.add_argument("--manifest", type=str, default="data/checksums.json", help="Path to manifest")
    args = parser.parse_args()

    md_path = Path(args.md)
    manifest_path = Path(args.manifest)

    if not md_path.exists():
        print(f"Error: {md_path} not found")
        sys.exit(1)

    manifest = load_manifest(manifest_path)
    urls = extract_urls_from_markdown(md_path)
    results = verify_citations(urls, manifest)

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
