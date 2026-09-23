import os
import sys
import logging
import json
import requests
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

class ConstitutionError(Exception):
    """Raised when a source fails constitutional checks (e.g., unreachable, invalid format)."""
    pass

def validate_research_md(candidate_source_path: Path, output_path: Path) -> Tuple[bool, str]:
    """
    Validates sources listed in candidate_source.txt.
    Reads JSON lines or JSON list from candidate_source_path.
    Checks if URLs are reachable (GET request).
    Writes verified sources to output_path.
    Returns (True, content) if successful, (False, content) if partial/failed.
    """
    verified_sources = []
    failed_sources = []
    
    if not candidate_source_path.exists():
        raise FileNotFoundError(f"Candidate source file not found: {candidate_source_path}")

    try:
        with open(candidate_source_path, 'r') as f:
            raw_content = f.read().strip()
            if not raw_content:
                raise ValueError("Candidate source file is empty.")
            
            # Try parsing as JSON list
            try:
                candidates = json.loads(raw_content)
            except json.JSONDecodeError:
                # Try parsing as JSON lines
                candidates = []
                for line in raw_content.splitlines():
                    line = line.strip()
                    if line:
                        try:
                            candidates.append(json.loads(line))
                        except json.JSONDecodeError:
                            logger.warning(f"Skipping invalid JSON line: {line}")

        if not isinstance(candidates, list):
            raise ValueError("Candidate sources must be a list of objects.")

        logger.info(f"Validating {len(candidates)} candidate sources...")

        for idx, source in enumerate(candidates):
            url = source.get('url')
            source_type = source.get('source_type', 'unknown')
            citation = source.get('citation', 'Unknown')
            
            if not url:
                logger.warning(f"Source {idx} missing URL. Skipping.")
                continue

            logger.info(f"Checking source {idx+1}/{len(candidates)}: {url}")
            
            is_healthy = False
            try:
                # Simple health check: HEAD or GET with timeout
                # For APIs, we might need a key, but we just check connectivity for now
                # If it's a DOI, we check the resolver
                if 'doi.org' in url:
                    # Redirect check
                    resp = requests.head(url, allow_redirects=True, timeout=10)
                    is_healthy = resp.status_code == 200
                else:
                    resp = requests.head(url, timeout=10)
                    is_healthy = resp.status_code < 400
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to reach {url}: {e}")
                is_healthy = False

            if is_healthy:
                source['verified'] = True
                verified_sources.append(source)
            else:
                source['verified'] = False
                failed_sources.append(source)

        # Construct output content
        output_lines = [
            "# Research Sources Verification Report",
            f"# Generated: {os.popen('date').read().strip()}",
            f"# Verified Count: {len(verified_sources)}",
            f"# Failed Count: {len(failed_sources)}",
            "",
            "## Verified Sources",
            ""
        ]

        for s in verified_sources:
            output_lines.append(f"- **{s.get('name', 'Unnamed')}** ({s.get('source_type', 'unknown')}): {s['url']}")
            output_lines.append(f"  - Citation: {s.get('citation', 'N/A')}")
            output_lines.append("")

        if failed_sources:
            output_lines.append("## Failed Sources (Excluded)")
            for s in failed_sources:
                output_lines.append(f"- {s.get('url', 'N/A')}: {s.get('citation', 'N/A')}")
            output_lines.append("")

        output_content = "\n".join(output_lines)

        # Write to output file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(output_content)

        if len(failed_sources) == len(candidates):
            return False, output_content
        return True, output_content

    except Exception as e:
        logger.error(f"Validation process failed: {e}")
        raise ConstitutionError(f"Validation failed: {e}")
