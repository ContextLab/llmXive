"""
Qualitative Extraction for Narrative Path (Task T012).

Reads data/raw/studies.csv and extracts qualitative descriptors for rows
lacking both 'r' and 'n' values using the NLP logic defined in
code/extraction/nlp_logic.py.

Writes the extracted qualitative data to data/processed/qualitative_data.json.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import the NLP logic as defined in the API surface
from extraction.nlp_logic import extract_tract_descriptors

# Import utility functions for config and paths
from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger

logger = get_logger(__name__)

# Paths relative to project root
INPUT_PATH = "data/raw/studies.csv"
OUTPUT_PATH = "data/processed/qualitative_data.json"
LEXICON_PATH = "code/config/tract_lexicon.yaml"
METHODOLOGY_PATH = "data/config/narrative_methodology.yaml"


def load_lexicon(lexicon_path: Path) -> Dict[str, List[str]]:
    """Load the tract lexicon from YAML."""
    import yaml
    if not lexicon_path.exists():
        logger.error(f"Lexicon file not found: {lexicon_path}")
        return {"tracts": [], "verbs": []}
    
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    return {
        "tracts": data.get("tracts", []),
        "verbs": data.get("verbs", [])
    }


def load_methodology(methodology_path: Path) -> Dict[str, Any]:
    """Load the narrative methodology configuration."""
    import yaml
    if not methodology_path.exists():
        logger.warning(f"Methodology file not found: {methodology_path}. Using defaults.")
        return {
            "keywords": [],
            "sentiment_rules": {"positive": [], "negative": []},
            "exclusion_criteria": []
        }
    
    with open(methodology_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def extract_qualitative_descriptors(input_file: Path, lexicon: Dict, scheme: Dict) -> List[Dict[str, Any]]:
    """
    Iterate over the input CSV and extract qualitative descriptors for rows
    where 'r' and 'n' are missing.
    
    Returns a list of dictionaries containing the extracted data.
    """
    results = []
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return results

    with open(input_file, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader):
            # Check if both 'r' and 'n' are missing or empty
            r_val = row.get('r', '').strip()
            n_val = row.get('n', '').strip()
            
            is_missing_quant = (not r_val) and (not n_val)
            
            if is_missing_quant:
                # Extract text for NLP processing
                # Assuming 'narrative' or 'description' column exists, otherwise use a combined text
                text_to_process = row.get('narrative', '') or row.get('description', '') or row.get('notes', '')
                
                if not text_to_process:
                    logger.debug(f"Row {row_idx}: No text to process.")
                    continue
                
                # Use the NLP logic to extract descriptors
                # The function signature in nlp_logic.py is extract_tract_descriptors(text, lexicon, scheme)
                descriptor = extract_tract_descriptors(text_to_process, lexicon, scheme)
                
                if descriptor:
                    results.append({
                        "row_index": row_idx,
                        "author": row.get('author', 'Unknown'),
                        "year": row.get('year', 'Unknown'),
                        "tract": row.get('tract', 'Unknown'),
                        "qualitative_desc": descriptor.get('description', ''),
                        "detected_tract": descriptor.get('detected_tract', None),
                        "detected_verb": descriptor.get('detected_verb', None),
                        "confidence": descriptor.get('confidence', 0.0)
                    })
            else:
                logger.debug(f"Row {row_idx}: Quantitative data present (r={r_val}, n={n_val}), skipping qualitative extraction.")

    return results


def save_qualitative_data(results: List[Dict], output_path: Path) -> None:
    """Save the extracted qualitative data to a JSON file."""
    ensure_directory(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Qualitative data saved to {output_path} with {len(results)} entries.")


def run_extraction() -> None:
    """Main entry point for the extraction task."""
    project_root = get_project_root()
    input_file = project_root / INPUT_PATH
    output_file = project_root / OUTPUT_PATH
    lexicon_file = project_root / LEXICON_PATH
    methodology_file = project_root / METHODOLOGY_PATH

    logger.info(f"Starting qualitative extraction from {input_file}")

    # Load configurations
    lexicon = load_lexicon(lexicon_file)
    scheme = load_methodology(methodology_file)

    # Perform extraction
    extracted_data = extract_qualitative_descriptors(input_file, lexicon, scheme)

    # Save results
    save_qualitative_data(extracted_data, output_file)

    logger.info("Qualitative extraction completed.")


def main() -> None:
    """CLI entry point."""
    try:
        run_extraction()
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
