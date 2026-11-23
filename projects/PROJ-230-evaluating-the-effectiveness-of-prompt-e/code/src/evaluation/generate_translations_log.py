"""
T025b: Aggregate raw LLM outputs into a CSV log for reproducibility and analysis.

This script scans the `data/evaluation/raw_translations/` directory, which is organized
by prompt condition subdirectories. It extracts the raw output text, the seed used
(from the associated metadata JSON), the prompt condition name, and the file modification
timestamp.

The resulting CSV `data/evaluation/raw_translations_log.csv` contains raw LLM outputs
and MUST be excluded from version control (added to .gitignore).
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from datetime import datetime

# Ensure project root is in path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging import get_logger

# Constants
RAW_TRANSLATIONS_DIR = PROJECT_ROOT / "data" / "evaluation" / "raw_translations"
OUTPUT_CSV_PATH = PROJECT_ROOT / "data" / "evaluation" / "raw_translations_log.csv"
METADATA_SUFFIX = "_metadata.json"

logger = get_logger(__name__)

def scan_translation_dirs(base_dir: Path) -> list:
    """
    Recursively scans the base directory for condition subdirectories.
    Returns a list of (condition_name, dir_path) tuples.
    """
    conditions = []
    if not base_dir.exists():
        logger.warning(f"Base directory does not exist: {base_dir}")
        return conditions

    for item in base_dir.iterdir():
        if item.is_dir():
            conditions.append((item.name, item))
    
    if not conditions:
        logger.warning(f"No condition subdirectories found in {base_dir}")
    
    return conditions

def extract_translation_data(condition_name: str, condition_dir: Path) -> list:
    """
    Scans a condition directory for translation JSON files and their corresponding
    metadata files to extract raw output and seed information.
    
    Returns a list of dicts with keys:
      - prompt_condition
      - seed
      - raw_output
      - timestamp
      - input_id (optional, for traceability)
    """
    entries = []
    
    # Look for .json files that are NOT metadata files
    translation_files = [f for f in condition_dir.iterdir() if f.is_file() and f.suffix == '.json' and not f.name.endswith(METADATA_SUFFIX)]
    
    for t_file in translation_files:
        try:
            with open(t_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine raw output
            raw_output = ""
            if isinstance(data, str):
                raw_output = data
            elif isinstance(data, dict):
                # Common keys for raw output in LLM responses
                raw_output = data.get('output', data.get('translation', data.get('text', '')))
            
            # Determine seed and input_id from metadata if available
            seed = "unknown"
            input_id = "unknown"
            metadata_path = condition_dir / f"{t_file.stem}{METADATA_SUFFIX}"
            
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as mf:
                        meta = json.load(mf)
                    seed = str(meta.get('seed', 'unknown'))
                    input_id = str(meta.get('input_id', 'unknown'))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in metadata file: {metadata_path}")
            
            # Get file modification time as timestamp
            timestamp = datetime.fromtimestamp(t_file.stat().st_mtime).isoformat()
            
            entries.append({
                'prompt_condition': condition_name,
                'seed': seed,
                'raw_output': raw_output,
                'timestamp': timestamp,
                'input_id': input_id,
                'source_file': t_file.name
            })
            
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON file: {t_file}")
        except Exception as e:
            logger.error(f"Error processing file {t_file}: {e}")

    return entries

def aggregate_translations(base_dir: Path) -> list:
    """
    Aggregates translation data from all condition subdirectories.
    """
    all_entries = []
    conditions = scan_translation_dirs(base_dir)
    
    if not conditions:
        logger.info("No conditions found to aggregate.")
        return all_entries

    for condition_name, condition_dir in conditions:
        logger.info(f"Processing condition: {condition_name}")
        entries = extract_translation_data(condition_name, condition_dir)
        all_entries.extend(entries)
    
    logger.info(f"Total entries aggregated: {len(all_entries)}")
    return all_entries

def save_translations_log(entries: list, output_path: Path):
    """
    Saves the aggregated entries to a CSV file.
    Columns: prompt_condition, seed, raw_output, timestamp, input_id, source_file
    """
    if not entries:
        logger.warning("No entries to save.")
        # Ensure the file is created even if empty, so downstream processes know it was run
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['prompt_condition', 'seed', 'raw_output', 'timestamp', 'input_id', 'source_file'])
            writer.writeheader()
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['prompt_condition', 'seed', 'raw_output', 'timestamp', 'input_id', 'source_file']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
    
    logger.info(f"Translations log saved to: {output_path}")

def main():
    """
    Main entry point for T025b.
    """
    logger.info("Starting T025b: Generate Translations Log")
    
    if not RAW_TRANSLATIONS_DIR.exists():
        logger.error(f"Raw translations directory not found: {RAW_TRANSLATIONS_DIR}")
        logger.error("Please ensure T023 (save translations) has been run first.")
        sys.exit(1)

    entries = aggregate_translations(RAW_TRANSLATIONS_DIR)
    save_translations_log(entries, OUTPUT_CSV_PATH)
    
    logger.info("T025b completed successfully.")

if __name__ == "__main__":
    main()
