"""
T090: Define cue-intensity weighting schemes.

This script defines three specific weighting schemes for cue intensity
(emoji, punctuation, length) and saves them to a JSON file in the processed data directory.

Schemes required by FR-005:
1. Equal Weight: { "emoji": 0.333, "punctuation": 0.333, "length": 0.333 }
2. Emoji-Dominant: { "emoji": 0.6, "punctuation": 0.2, "length": 0.2 }
3. Punctuation-Dominant: { "emoji": 0.2, "punctuation": 0.6, "length": 0.2 }

The 'Equal Weight' scheme serves as the baseline.
"""

import json
import sys
from pathlib import Path

# Add the code directory to the path to allow imports from config
code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_processed_data_dir
from logging_config import setup_logging, get_logger

# Setup logging
logger = setup_logging()
logger = get_logger(__name__)

def get_cue_intensity_schemes():
    """
    Returns a dictionary containing the three predefined cue intensity weighting schemes.
    
    Returns:
        dict: A dictionary with keys 'equal_weight', 'emoji_dominant', and 'punctuation_dominant'
              mapping to their respective weight dictionaries.
    """
    schemes = {
        "equal_weight": {
            "emoji": 0.333,
            "punctuation": 0.333,
            "length": 0.333
        },
        "emoji_dominant": {
            "emoji": 0.6,
            "punctuation": 0.2,
            "length": 0.2
        },
        "punctuation_dominant": {
            "emoji": 0.2,
            "punctuation": 0.6,
            "length": 0.2
        }
    }
    return schemes

def save_schemes(schemes, output_path):
    """
    Saves the cue intensity schemes to a JSON file.
    
    Args:
        schemes (dict): The dictionary of schemes to save.
        output_path (Path): The path where the JSON file will be written.
    """
    try:
        # Ensure the directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schemes, f, indent=4)
        
        logger.info(f"Successfully saved cue intensity schemes to {output_path}")
    except IOError as e:
        logger.error(f"Failed to save schemes to {output_path}: {e}")
        raise

def main():
    """Main entry point for the script."""
    logger.info("Starting T090: Define cue-intensity weighting schemes")
    
    # Get the output path
    processed_dir = get_processed_data_dir()
    output_file = processed_dir / "cue_intensity_weights.json"
    
    # Get the schemes
    schemes = get_cue_intensity_schemes()
    
    # Save the schemes
    save_schemes(schemes, output_file)
    
    logger.info("T090 completed successfully")

if __name__ == "__main__":
    main()