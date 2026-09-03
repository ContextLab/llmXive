"""
Cue Intensity Weight Schemes Definition (T090)

Defines and saves the three weighting schemes for cue intensity calculation.
Output: data/processed/cue_intensity_weights.json
"""
import json
import sys
from pathlib import Path
from config import get_processed_data_dir
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def get_cue_intensity_schemes():
    """
    Returns the three predefined cue intensity weighting schemes.
    
    Returns:
        dict: Dictionary containing the three schemes
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

def save_schemes(output_path: Path = None):
    """
    Saves the cue intensity schemes to a JSON file.
    
    Args:
        output_path: Optional path to save the file. Defaults to data/processed/cue_intensity_weights.json
    """
    if output_path is None:
        output_path = get_processed_data_dir() / "cue_intensity_weights.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    schemes = get_cue_intensity_schemes()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schemes, f, indent=2)
    
    logger.info(f"Saved cue intensity schemes to {output_path}")
    return output_path

def main():
    """Main entry point for defining weights."""
    setup_logging()
    
    try:
        output_path = save_schemes()
        logger.info("Weights defined and saved successfully")
        return 0
    except Exception as e:
        logger.error(f"Error defining weights: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())