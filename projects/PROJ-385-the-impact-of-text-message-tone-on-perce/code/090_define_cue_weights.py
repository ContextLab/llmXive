"""
Task T090: Define cue-intensity weighting schemes.

This script defines four specific weighting schemes for calculating
cue intensity based on emoji, punctuation, and text cues.

Schemes:
1. Primary:      (0.4, 0.3, 0.3)
2. Equal:        (0.33, 0.33, 0.33)
3. Emoji-Dominant: (0.6, 0.2, 0.2)
4. Punctuation-Dominant: (0.2, 0.6, 0.2)

Output:
Writes the definitions to `data/processed/cue_intensity_weights.json`.
"""
import json
import os
from pathlib import Path
from config import get_processed_data_dir

def get_cue_intensity_schemes():
    """
    Returns a dictionary of cue intensity weighting schemes.
    
    Returns:
        dict: Keys are scheme names, values are dicts with 'emoji', 'punctuation', 'text' weights.
    """
    schemes = {
        "Primary": {
            "emoji": 0.4,
            "punctuation": 0.3,
            "text": 0.3
        },
        "Equal": {
            "emoji": 0.33,
            "punctuation": 0.33,
            "text": 0.33
        },
        "Emoji-Dominant": {
            "emoji": 0.6,
            "punctuation": 0.2,
            "text": 0.2
        },
        "Punctuation-Dominant": {
            "emoji": 0.2,
            "punctuation": 0.6,
            "text": 0.2
        }
    }
    return schemes

def save_schemes(schemes, output_path):
    """
    Saves the schemes dictionary to a JSON file.
    
    Args:
        schemes (dict): The schemes to save.
        output_path (Path): The path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schemes, f, indent=2)

def main():
    """Main entry point for T090."""
    output_dir = get_processed_data_dir()
    output_file = output_dir / "cue_intensity_weights.json"
    
    schemes = get_cue_intensity_schemes()
    save_schemes(schemes, output_file)
    
    print(f"Cue intensity weights saved to: {output_file}")
    print(f"Defined schemes: {list(schemes.keys())}")

if __name__ == "__main__":
    main()
