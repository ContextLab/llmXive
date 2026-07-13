import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
from logging_config import setup_logger, get_logger

# Error codes defined in tasks.md
ERROR_104 = 104
MIN_SNIPPETS_PER_GROUP = 1000

def load_processed_snippets(data_dir: Path, group_name: str) -> List[Dict]:
    """
    Load processed snippets for a specific group from the data directory.
    Expects files named like: data/processed/{group_name}_snippets.json
    """
    file_path = data_dir / "processed" / f"{group_name}_snippets.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Processed snippets file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def count_valid_snippets(snippets: List[Dict]) -> int:
    """
    Count the number of valid snippets in the list.
    A snippet is considered valid if it has 'id', 'code', and 'language' fields
    and the language is 'python'.
    """
    count = 0
    for snippet in snippets:
        if (isinstance(snippet, dict) and 
            'id' in snippet and 
            'code' in snippet and 
            snippet.get('language') == 'python'):
            count += 1
    return count

def verify_snippet_counts(data_dir: Path, groups: List[str], min_count: int = MIN_SNIPPETS_PER_GROUP) -> bool:
    """
    Verify that each group has at least min_count valid Python snippets.
    Returns True if all groups meet the requirement.
    Returns False and exits with error code 104 if any group fails.
    """
    logger = get_logger(__name__)
    all_valid = True

    for group in groups:
        try:
            logger.info(f"Loading and verifying snippets for group: {group}")
            snippets = load_processed_snippets(data_dir, group)
            valid_count = count_valid_snippets(snippets)
            logger.info(f"Group '{group}': Found {valid_count} valid Python snippets.")

            if valid_count < min_count:
                logger.error(f"Group '{group}' has insufficient snippets: {valid_count} < {min_count}")
                all_valid = False
            else:
                logger.info(f"Group '{group}' meets the minimum threshold.")

        except FileNotFoundError as e:
            logger.error(f"Failed to load snippets for group '{group}': {e}")
            all_valid = False
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for group '{group}': {e}")
            all_valid = False
        except Exception as e:
            logger.error(f"Unexpected error processing group '{group}': {e}")
            all_valid = False

    if not all_valid:
        logger.error(f"VERIFICATION FAILED: One or more groups do not meet the minimum snippet count of {min_count}.")
        logger.error(f"Aborting with error code {ERROR_104}.")
        sys.exit(ERROR_104)

    logger.info("VERIFICATION PASSED: All groups meet the minimum snippet count requirement.")
    return True

def main():
    """
    Main entry point for snippet count verification.
    Expects data directory to be passed via environment or hardcoded based on project structure.
    """
    logger = setup_logger("snippet_counter")
    logger.info("Starting snippet count verification workflow.")

    # Define project paths
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    
    # Groups defined in the project (Human-written vs LLM-generated)
    # Based on T012/T013: CodeSearchNet (human) and CodeParrot/CodeGen (LLM)
    groups = ["codesearchnet", "codegen"]

    try:
        verify_snippet_counts(data_dir, groups, MIN_SNIPPETS_PER_GROUP)
        logger.info("Snippet verification completed successfully.")
    except SystemExit as e:
        if e.code == ERROR_104:
            sys.exit(ERROR_104)
        raise

if __name__ == "__main__":
    main()
