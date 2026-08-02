"""
Narrative Logic Implementation (T015a)

Performs thematic aggregation of qualitative study descriptors.
Reads extracted studies and methodology config, aggregates by theme,
and writes the result to data/derived/narrative_themes.json.
"""
import json
import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import project utilities (matching API surface)
from utils.logger import get_logger
from utils.config import get_project_root, ensure_directory

logger = get_logger(__name__)

# --- Configuration Paths ---
# These paths are relative to the project root
PROJECT_ROOT = get_project_root()
EXTRACTED_STUDIES_PATH = PROJECT_ROOT / "data" / "processed" / "extracted_studies.csv"
METHODOLOGY_CONFIG_PATH = PROJECT_ROOT / "data" / "config" / "narrative_methodology.yaml"
OUTPUT_PATH = PROJECT_ROOT / "data" / "derived" / "narrative_themes.json"

# --- Helper Functions ---

def load_methodology_config(config_path: Path) -> Dict[str, Any]:
    """
    Loads the narrative methodology configuration from a YAML file.
    Expected schema:
      keywords: [list of strings]
      sentiment_rules: {positive: [list], negative: [list]}
      exclusion_criteria: [list of strings]
    """
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        if not config:
            logger.warning(f"Methodology config at {config_path} is empty.")
            return {"keywords": [], "sentiment_rules": {"positive": [], "negative": []}, "exclusion_criteria": []}
        return config
    except FileNotFoundError:
        logger.error(f"Methodology config not found at {config_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load methodology config: {e}")
        raise

def load_extracted_studies(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Loads the extracted studies from the CSV file produced by T013.
    Returns a list of dictionaries.
    """
    studies = []
    if not csv_path.exists():
        logger.error(f"Extracted studies file not found at {csv_path}")
        raise FileNotFoundError(f"Input file not found: {csv_path}")

    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ensure qualitative_desc is treated as a string
                if 'qualitative_desc' in row and row['qualitative_desc']:
                    studies.append(row)
                else:
                    # If no qualitative_desc, we might still include it if narrative_pool is True?
                    # Based on T013 spec: "Include in narrative pool" if r/n missing.
                    # We assume if it's in the CSV, it's a candidate.
                    studies.append(row)
    except Exception as e:
        logger.error(f"Failed to read extracted studies CSV: {e}")
        raise

    return studies

def extract_themes(studies: List[Dict[str, Any]], methodology: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregates qualitative descriptions by theme.
    
    Logic:
    1. Iterate through studies.
    2. If a study has a 'qualitative_desc', check it against 'keywords' in methodology.
    3. If a keyword matches, assign the study to that theme.
    4. If no keyword matches, assign to 'uncategorized' (or a generic 'general' theme).
    5. Count frequencies and collect sample texts.
    """
    keywords = methodology.get('keywords', [])
    # Compile regex patterns for keywords to handle case-insensitivity and word boundaries
    patterns = []
    for kw in keywords:
        # Escape special regex chars in the keyword
        escaped_kw = re.escape(kw)
        # Match whole words or phrases, case-insensitive
        patterns.append(re.compile(escaped_kw, re.IGNORECASE))

    theme_data = defaultdict(lambda: {"count": 0, "studies": [], "descriptions": []})

    for study in studies:
        desc = study.get('qualitative_desc', '')
        if not desc or not isinstance(desc, str):
            continue

        matched_theme = None
        for i, pattern in enumerate(patterns):
            if pattern.search(desc):
                matched_theme = keywords[i] # Use the original keyword string as theme name
                break

        if not matched_theme:
            matched_theme = "uncategorized"

        theme_data[matched_theme]["count"] += 1
        # Store a snippet of the study for reference
        study_ref = {
            "author": study.get('author', 'Unknown'),
            "year": study.get('year', 'Unknown'),
            "tract": study.get('tract', 'Unknown'),
            "desc_snippet": desc[:100] + "..." if len(desc) > 100 else desc
        }
        theme_data[matched_theme]["studies"].append(study_ref)
        theme_data[matched_theme]["descriptions"].append(desc)

    # Convert defaultdict to standard dict and format output
    result = {
        "timestamp": datetime.now().isoformat(),
        "total_studies_processed": len(studies),
        "themes": {}
    }

    for theme_name, data in theme_data.items():
        result["themes"][theme_name] = {
            "count": data["count"],
            "sample_studies": data["studies"][:5], # Limit samples to 5 for brevity
            "unique_descriptions": len(set(data["descriptions"]))
        }

    return result

def generate_themes_json(themes_data: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the theme aggregation results to a JSON file.
    """
    ensure_directory(output_path.parent)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(themes_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Narrative themes written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write narrative themes JSON: {e}")
        raise

def run_narrative_logic() -> Dict[str, Any]:
    """
    Main entry point for T015a.
    Orchestrates loading, processing, and saving.
    """
    logger.info("Starting Narrative Logic (T015a)...")
    
    # 1. Load Config
    logger.info(f"Loading methodology config from {METHODOLOGY_CONFIG_PATH}")
    methodology = load_methodology_config(METHODOLOGY_CONFIG_PATH)
    
    # 2. Load Data
    logger.info(f"Loading extracted studies from {EXTRACTED_STUDIES_PATH}")
    studies = load_extracted_studies(EXTRACTED_STUDIES_PATH)
    
    if not studies:
        logger.warning("No studies found in extracted CSV. Generating empty themes.")
        themes_data = {
            "timestamp": datetime.now().isoformat(),
            "total_studies_processed": 0,
            "themes": {}
        }
    else:
        # 3. Process
        logger.info(f"Processing {len(studies)} studies for thematic aggregation...")
        themes_data = extract_themes(studies, methodology)
    
    # 4. Save
    logger.info(f"Saving results to {OUTPUT_PATH}")
    generate_themes_json(themes_data, OUTPUT_PATH)
    
    logger.info("Narrative Logic (T015a) completed successfully.")
    return themes_data

def main():
    """CLI Entry point."""
    try:
        run_narrative_logic()
    except Exception as e:
        logger.error(f"Narrative Logic execution failed: {e}")
        # Re-raise to ensure the pipeline fails loudly as per constraints
        raise

if __name__ == "__main__":
    main()
