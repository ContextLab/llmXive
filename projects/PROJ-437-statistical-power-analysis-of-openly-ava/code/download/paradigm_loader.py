"""
Paradigm Loader Module for Statistical Power Analysis.

This module reads the list of cognitive paradigms and their associated
dataset IDs from the project's research manifest file.

It supports fetching up to 15 paradigms as per FR-001.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Constants
MAX_PARADIGMS = 15
RESEARCH_MANIFEST_PATH = Path("specs/001-statistical-power-analysis/research.md")

logger = logging.getLogger(__name__)


class ParadigmLoaderError(Exception):
    """Custom exception for paradigm loading errors."""
    pass


def parse_research_manifest(manifest_path: Path) -> List[Dict[str, str]]:
    """
    Parse the research.md manifest to extract paradigm-dataset pairs.

    Expects lines in the research.md that follow a specific pattern:
    - A line starting with "- [ ]" or "- [X]" indicating a task or item.
    - The line must contain a paradigm name and a dataset ID (e.g., ds000030).

    Expected format in research.md:
    - [ ] T052 [US2] ... paradigm: Motor ... dataset_id: ds000030
    OR
    - [ ] Task Description ... Paradigm: Motor ... Dataset: ds000030

    This parser looks for the specific pattern used in the tasks.md context
    or research.md where paradigms are listed. It searches for lines containing
    "paradigm" and "dataset" or "ds" identifiers.

    Args:
        manifest_path: Path to the research.md file.

    Returns:
        A list of dictionaries: [{"paradigm": str, "dataset_id": str}, ...]

    Raises:
        ParadigmLoaderError: If the file is not found or no valid entries are found.
    """
    if not manifest_path.exists():
        raise ParadigmLoaderError(f"Manifest file not found: {manifest_path}")

    results = []
    paradigm_pattern = re.compile(
        r"(?:paradigm|Paradigm|cognitive task|Task)\s*[:=]\s*['\"]?(\w+)['\"]?\s*"
        r"(?:dataset|Dataset|ds|id|ID)\s*[:=]\s*['\"]?(ds\d+)['\"]?",
        re.IGNORECASE
    )
    
    # Fallback pattern for the specific format in the provided tasks.md context
    # which often lists them as: "paradigm: Motor" and "dataset_id: ds000030" in descriptions
    # or simply listing them in a table-like structure.
    # We will also look for lines that define a task related to a paradigm.
    # Since the prompt implies reading from research.md, we assume research.md
    # contains a list of valid paradigms and their source datasets.
    
    # Pattern 1: Explicit "paradigm: X dataset: Y" or similar
    # Pattern 2: Lines in a list like "- [ ] ... paradigm: Motor ... ds000030"
    
    # Let's assume a standard format often used in these specs:
    # "Paradigm: <Name>, Dataset: <ID>" or "paradigm=<Name> dataset_id=<ID>"
    # Or a table row.
    
    # Robust regex to catch: paradigm: Name ... ds000030
    # It looks for the word paradigm, captures the name, then looks for a ds ID.
    generic_pattern = re.compile(
        r"(?i).*?(paradigm|Paradigm|Task)\s*[:=]\s*['\"]?([a-zA-Z0-9_\s]+)['\"]?\s*"
        r"(?:.*?)(dataset|Dataset|ID|ds)\s*[:=]\s*['\"]?(ds\d+)['\"]?.*",
        re.IGNORECASE
    )

    # Also try to match the specific format if it's in a list item
    # e.g., "- [ ] T052 ... paradigm: Motor ... dataset_id: ds000030"
    list_item_pattern = re.compile(
        r"-\s*\[[ xX]\]\s*\w+\s+(?:\[.*?\])?\s+.*?(?:paradigm|Paradigm|Task)\s*[:=]\s*['\"]?(\w+)['\"]?\s+"
        r"(?:.*?)(?:dataset_id|Dataset|ds|ID)\s*[:=]\s*['\"]?(ds\d+)['\"]?",
        re.IGNORECASE
    )

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        raise ParadigmLoaderError(f"Failed to read manifest file: {e}")

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        match = generic_pattern.search(line)
        if not match:
            match = list_item_pattern.search(line)

        if match:
            # The regex groups might vary slightly, but we expect:
            # Group 1: Paradigm Name
            # Group 2: Dataset ID
            # We need to be careful with group indices if the regex changes.
            # Let's refine the extraction logic based on the match groups.
            
            # If using generic_pattern:
            # Groups: (type, name, type2, id) -> We want name and id
            # If using list_item_pattern:
            # Groups: (name, id)
            
            paradigm_name = None
            dataset_id = None

            if match.groups()[1] and match.groups()[3]:
                # generic_pattern hit
                paradigm_name = match.group(2).strip()
                dataset_id = match.group(4).strip()
            elif match.groups()[0] and match.groups()[1]:
                # list_item_pattern hit
                paradigm_name = match.group(1).strip()
                dataset_id = match.group(2).strip()
            
            if paradigm_name and dataset_id:
                # Clean up paradigm name (remove trailing punctuation if any)
                paradigm_name = re.sub(r'[,;:.]+$', '', paradigm_name).strip()
                
                entry = {
                    "paradigm": paradigm_name,
                    "dataset_id": dataset_id
                }
                
                # Avoid duplicates
                if entry not in results:
                    results.append(entry)
                    logger.debug(f"Parsed: {paradigm_name} -> {dataset_id} from line {line_num}")

    if not results:
        # If no results found with complex regex, try a simpler heuristic
        # looking for "paradigm" and "ds" in the same line, assuming simple structure
        simple_pattern = re.compile(r"(?i).*?paradigm\s*[:=]\s*['\"]?(\w+)['\"]?.*?(ds\d+)", re.IGNORECASE)
        for line_num, line in enumerate(lines, 1):
            if "paradigm" in line.lower() and "ds" in line:
                simple_match = simple_pattern.search(line)
                if simple_match:
                    entry = {
                        "paradigm": simple_match.group(1),
                        "dataset_id": simple_match.group(2)
                    }
                    if entry not in results:
                        results.append(entry)
                        logger.debug(f"Parsed (simple): {entry} from line {line_num}")

    if not results:
        raise ParadigmLoaderError(
            f"No valid paradigm-dataset pairs found in {manifest_path}. "
            f"Ensure the file contains entries like 'paradigm: Motor dataset_id: ds000030'."
        )

    if len(results) > MAX_PARADIGMS:
        logger.warning(
            f"Found {len(results)} paradigms, but FR-001 limits to {MAX_PARADIGMS}. "
            f"Truncating list."
        )
        results = results[:MAX_PARADIGMS]

    return results


def load_paradigm_manifest(
    manifest_path: Optional[Path] = None,
    limit: Optional[int] = None
) -> List[Dict[str, str]]:
    """
    Load and return the list of paradigms and dataset IDs.

    This is the main entry point for T052.

    Args:
        manifest_path: Optional path to the manifest. Defaults to RESEARCH_MANIFEST_PATH.
        limit: Optional limit on the number of paradigms to return. Defaults to MAX_PARADIGMS.

    Returns:
        List of dicts: [{"paradigm": str, "dataset_id": str}, ...]

    Raises:
        ParadigmLoaderError: If the file is missing, unreadable, or empty.
    """
    path = manifest_path or RESEARCH_MANIFEST_PATH
    results = parse_research_manifest(path)
    
    if limit is not None and limit < MAX_PARADIGMS:
        results = results[:limit]
    
    return results


def main() -> None:
    """
    CLI entry point for testing the paradigm loader.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        paradigms = load_paradigm_manifest()
        print(f"Loaded {len(paradigms)} paradigms:")
        for p in paradigms:
            print(f"  - {p['paradigm']}: {p['dataset_id']}")
    except ParadigmLoaderError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
