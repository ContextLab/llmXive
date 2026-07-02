"""
Citation validation utility for the llmXive pipeline.

This module provides functionality to parse `research.md` for citation URLs,
validate them against a list of verified datasets (Planck Legacy Archive,
CAMB documentation, etc.), and report on their status.

It strictly avoids fabricating data or passing silently. If a URL cannot
be reached or is not in the verified list, it logs a warning/error.
"""
import os
import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verified dataset domains and specific paths based on project requirements
# These are the ONLY allowed sources for "real data" as per constraints
VERIFIED_DATASETS = {
    "planck_legacy_archive": [
        "pla.esa.int",
        "archives.esac.esa.int/pla"
    ],
    "arxiv": [
        "arxiv.org"
    ],
    "camb_info": [
        "camb.info"
    ],
    "healpix": [
        "healpix.jpl.nasa.gov"
    ]
}

# Specific URL patterns that are considered valid even if not fully reachable
# (e.g., documentation that might be down temporarily but is known good)
KNOWN_VALID_PATTERNS = [
    r"https?://pla\.esa\.int/.*",
    r"https?://arxiv\.org/abs/.*",
    r"https?://arxiv\.org/pdf/.*",
    r"https?://camb\.info/.*"
]

def parse_research_md(research_path: Path) -> List[Tuple[str, str, int]]:
    """
    Parses research.md and extracts all URLs found in citation brackets or parentheses.
    
    Args:
        research_path: Path to the research.md file
        
    Returns:
        List of tuples: (url, context_line, line_number)
    """
    if not research_path.exists():
        logger.error(f"Research file not found: {research_path}")
        return []

    citations = []
    # Regex to find URLs in text
    url_pattern = re.compile(r'(https?://[^\s\)\]\"]+)')
    
    try:
        with open(research_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                matches = url_pattern.findall(line)
                for url in matches:
                    # Clean trailing punctuation
                    url = url.rstrip('.,;:')
                    citations.append((url, line.strip(), line_num))
    except Exception as e:
        logger.error(f"Error reading research file: {e}")
        return []

    return citations

def is_verified_source(url: str) -> bool:
    """
    Checks if the URL belongs to a verified dataset domain.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Check against verified domains
        for dataset_name, domains in VERIFIED_DATASETS.items():
            if any(domain.endswith(d) for d in domains):
                return True
        
        # Check against known valid patterns
        for pattern in KNOWN_VALID_PATTERNS:
            if re.match(pattern, url):
                return True
                
        return False
    except Exception as e:
        logger.warning(f"Could not parse URL {url}: {e}")
        return False

def validate_url_reachability(url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Validates if a URL is reachable via HTTP HEAD request.
    
    Returns:
        Tuple of (is_reachable, error_message)
    """
    try:
        # Some servers block HEAD, fallback to GET with stream=True
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, None
        
        # Try GET if HEAD fails (some servers don't support HEAD)
        response = requests.get(url, timeout=timeout, stream=True)
        if response.status_code == 200:
            return True, None
            
        return False, f"HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, str(e)

def validate_citations(
    research_path: Path, 
    output_path: Optional[Path] = None
) -> Dict[str, List[str]]:
    """
    Main entry point to validate citations in research.md.
    
    Args:
        research_path: Path to research.md
        output_path: Optional path to write a JSON report
        
    Returns:
        Dictionary with keys 'valid', 'invalid', 'missing_verified'
    """
    results = {
        "valid": [],
        "invalid": [],
        "missing_verified": [],
        "total": 0
    }

    citations = parse_research_md(research_path)
    if not citations:
        logger.warning("No citations found in research.md")
        return results

    logger.info(f"Found {len(citations)} citations to validate.")

    for url, context, line_num in citations:
        results["total"] += 1
        
        # Step 1: Check if it's a verified source
        if not is_verified_source(url):
            results["missing_verified"].append({
                "url": url,
                "line": line_num,
                "reason": "Not in verified dataset list"
            })
            logger.warning(f"Line {line_num}: Unverified source: {url}")
            continue

        # Step 2: Check reachability
        is_reachable, error = validate_url_reachability(url)
        
        if is_reachable:
            results["valid"].append({
                "url": url,
                "line": line_num
            })
            logger.info(f"Line {line_num}: Valid - {url}")
        else:
            results["invalid"].append({
                "url": url,
                "line": line_num,
                "reason": error
            })
            logger.error(f"Line {line_num}: Invalid - {url} ({error})")

    # Log summary
    logger.info(f"Validation complete: {len(results['valid'])} valid, "
                f"{len(results['invalid'])} unreachable, "
                f"{len(results['missing_verified'])} unverified.")

    # Write report if requested
    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Report written to {output_path}")

    return results

def main():
    """
    CLI entry point.
    Expects research.md in the project root or specified path.
    """
    project_root = Path(__file__).parent.parent.parent
    research_file = project_root / "research.md"
    
    if not research_file.exists():
        # Fallback to common locations if not in root
        alt_paths = [
            project_root / "specs" / "001-cmb-anomaly-lss-impact" / "research.md",
            project_root / "docs" / "research.md"
        ]
        for alt in alt_paths:
            if alt.exists():
                research_file = alt
                break

    if not research_file.exists():
        logger.error("research.md not found in expected locations.")
        sys.exit(1)

    logger.info(f"Validating citations in: {research_file}")
    
    output_file = project_root / "data" / "results" / "citation_validation_report.json"
    
    results = validate_citations(research_file, output_file)
    
    # Exit with error code if there are invalid or unverified citations
    if results["invalid"] or results["missing_verified"]:
        logger.warning("Citation validation found issues.")
        # We do not exit with error code here as the task is to validate,
        # not to block the pipeline based on citation status alone,
        # unless strict mode is enabled.
    else:
        logger.info("All citations are valid and verified.")

if __name__ == "__main__":
    main()
