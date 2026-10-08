"""
Cue Intensity Weighting Schemes Definition.

This module defines the three weighting schemes for cue intensity calculation:
1. Equal: Equal distribution across emoji, punctuation, and length.
2. Emoji-Dominant: Emoji use is the primary driver of perceived warmth.
3. Punctuation-Dominant: Punctuation intensity signals emotional arousal.

All weights are normalized to sum to 1.0.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import get_processed_data_dir
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def round_normalized_weights(weights: Dict[str, float], decimals: int = 10) -> Dict[str, float]:
    """
    Round weights to specified decimal places and adjust the last component
    to ensure they sum to exactly 1.0.
    """
    # Round all weights
    rounded = {k: round(v, decimals) for k, v in weights.items()}
    
    # Calculate sum
    total = sum(rounded.values())
    
    # If not exactly 1.0, adjust the last component
    if abs(total - 1.0) > 1e-10:
        keys = list(rounded.keys())
        remainder = 1.0 - total
        rounded[keys[-1]] = round(rounded[keys[-1]] + remainder, decimals)
    
    return rounded

def get_cue_intensity_schemes() -> Dict[str, Dict[str, float]]:
    """
    Return the three cue intensity weighting schemes.
    
    Tuple Order: Always (emoji, punctuation, length)
    
    1. Equal: Equal distribution (rounded to 10 decimal places, remainder to last)
    2. Emoji-Dominant: Majority to emoji
    3. Punctuation-Dominant: High to punctuation
    """
    schemes = {
        "equal": {
            "emoji": 0.3333333333,
            "punctuation": 0.3333333333,
            "length": 0.3333333334  # Remainder to make sum = 1.0
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
    
    # Verify all schemes sum to 1.0
    for name, weights in schemes.items():
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-10:
            logger.warning(f"Scheme '{name}' sums to {total}, not 1.0")
            schemes[name] = round_normalized_weights(weights)
    
    return schemes

def save_schemes(output_path: Path = None) -> Path:
    """Save the weighting schemes to a JSON file."""
    if output_path is None:
        output_path = Path(get_processed_data_dir()) / "cue_intensity_weights.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    schemes = get_cue_intensity_schemes()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schemes, f, indent=2)
    
    logger.info(f"Saved cue intensity schemes to {output_path}")
    return output_path

def main():
    """Main entry point."""
    setup_logging()
    
    try:
        output_path = save_schemes()
        print(f"Cue intensity schemes saved to {output_path}")
        exit(0)
    except Exception as e:
        logger.error(f"Error saving schemes: {e}")
        exit(1)

if __name__ == "__main__":
    main()
