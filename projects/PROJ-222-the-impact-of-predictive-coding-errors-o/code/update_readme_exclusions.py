"""
Task T018: Update data/README.md with exclusion logs and reasons for dropped datasets.

This script reads the exclusion logs generated during the filtering phase (T014)
and updates the data/README.md file to include a structured 'Exclusion Logs' section.
It ensures the documentation reflects the actual state of the dataset pipeline.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import project utilities
from config import get_data_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXCLUSION_LOG_PATH = Path("data/processed/exclusion_log.json")
README_PATH = Path("data/README.md")

def load_exclusion_log() -> List[Dict[str, Any]]:
    """
    Loads the exclusion log from the processed data directory.
    If the file does not exist, returns an empty list.
    """
    if not EXCLUSION_LOG_PATH.exists():
        logger.warning(f"No exclusion log found at {EXCLUSION_LOG_PATH}. Assuming no exclusions.")
        return []
    
    try:
        with open(EXCLUSION_LOG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure it's a list
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'exclusions' in data:
                return data['exclusions']
            else:
                logger.error(f"Unexpected format in {EXCLUSION_LOG_PATH}")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {EXCLUSION_LOG_PATH}: {e}")
        return []

def generate_exclusion_section(exclusions: List[Dict[str, Any]]) -> str:
    """
    Generates the Markdown content for the Exclusion Logs section.
    """
    if not exclusions:
        return "### Exclusion Logs\n\nNo datasets were excluded during preprocessing.\n"

    lines = [
        "### Exclusion Logs",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "| Dataset ID | Source | Reason | Status |",
        "|------------|--------|--------|--------|"
    ]

    for entry in exclusions:
        dataset_id = entry.get("dataset_id", "Unknown")
        source = entry.get("source", "Unknown")
        reason = entry.get("reason", "No reason provided")
        status = "Excluded"
        
        # Escape pipes in reason if necessary
        reason = reason.replace("|", "\\|")
        
        lines.append(f"| {dataset_id} | {source} | {reason} | {status} |")

    lines.append("")
    return "\n".join(lines)

def update_readme(exclusions: List[Dict[str, Any]]) -> None:
    """
    Updates the data/README.md file with the new exclusion logs section.
    It preserves the existing content before the 'Exclusion Logs' header
    and replaces the entire 'Exclusion Logs' section.
    """
    if not README_PATH.exists():
        logger.error(f"README.md not found at {README_PATH}. Cannot update.")
        return

    readme_content = README_PATH.read_text(encoding='utf-8')
    lines = readme_content.splitlines()

    new_section = generate_exclusion_section(exclusions)
    
    # Find the start of the Exclusion Logs section
    start_index = None
    end_index = None

    for i, line in enumerate(lines):
        if line.strip().startswith("### Exclusion Logs"):
            start_index = i
            break

    if start_index is not None:
        # Find the end of the section (next header or end of file)
        for i in range(start_index + 1, len(lines)):
            if lines[i].startswith("###") or lines[i].startswith("#"):
                end_index = i
                break
        if end_index is None:
            end_index = len(lines)
    
    # Reconstruct the file
    if start_index is not None:
        new_lines = lines[:start_index] + [new_section] + lines[end_index:]
    else:
        # Append if section doesn't exist (shouldn't happen based on template, but safe guard)
        new_lines = lines + ["", new_section]

    new_content = "\n".join(new_lines)
    
    # Ensure single trailing newline
    new_content = new_content.rstrip() + "\n"

    README_PATH.write_text(new_content, encoding='utf-8')
    logger.info(f"Successfully updated {README_PATH} with {len(exclusions)} exclusion entries.")

def run_t018() -> None:
    """
    Main entry point for Task T018.
    """
    logger.info("Starting T018: Updating README with exclusion logs...")
    
    exclusions = load_exclusion_log()
    update_readme(exclusions)
    
    logger.info("T018 completed.")

if __name__ == "__main__":
    run_t018()
