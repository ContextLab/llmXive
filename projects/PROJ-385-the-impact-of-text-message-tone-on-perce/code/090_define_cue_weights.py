"""
Defines and saves the cue intensity weighting schemes for the sensitivity analysis.

This module creates the JSON file containing three weighting dictionaries:
1. Equal: Equal distribution across emoji, punctuation, and length.
2. Emoji-Dominant: Higher weight on emoji cues.
3. Punctuation-Dominant: Higher weight on punctuation cues.

The output file is saved to data/processed/cue_intensity_weights.json.
"""
import json
from pathlib import Path
from typing import Dict, Any

from config import get_processed_data_dir
from logging_config import setup_logging, get_logger

# Initialize logger
logger = get_logger(__name__)

def get_cue_intensity_schemes() -> Dict[str, Dict[str, float]]:
    """
    Returns the three cue intensity weighting schemes with exact numeric values.
    
    Returns:
        Dict mapping scheme names to their weight dictionaries.
    """
    return {
        "Equal": {
            "emoji": 0.33,
            "punctuation": 0.33,
            "length": 0.34
        },
        "Emoji-Dominant": {
            "emoji": 0.6,
            "punctuation": 0.2,
            "length": 0.2
        },
        "Punctuation-Dominant": {
            "emoji": 0.2,
            "punctuation": 0.6,
            "length": 0.2
        }
    }

def save_schemes(output_path: Path, schemes: Dict[str, Dict[str, float]]) -> None:
    """
    Saves the weighting schemes to a JSON file.
    
    Args:
        output_path: Path to the output JSON file.
        schemes: The weighting schemes to save.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schemes, f, indent=2)
    logger.info(f"Saved cue intensity weights to {output_path}")

def main() -> None:
    """Main entry point to generate and save the weighting schemes."""
    setup_logging()
    
    # Get the output directory
    processed_dir = get_processed_data_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Define the output path
    output_path = processed_dir / "cue_intensity_weights.json"
    
    # Get the schemes
    schemes = get_cue_intensity_schemes()
    
    # Save them
    save_schemes(output_path, schemes)
    
    logger.info("Task T090 completed: Cue-intensity weighting schemes generated.")

if __name__ == "__main__":
    main()
