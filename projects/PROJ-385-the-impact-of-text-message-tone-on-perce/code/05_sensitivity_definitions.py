"""
T027: Define three alternative structural definitions of 'Cue Intensity'.

This module generates the machine-readable JSON definitions for sensitivity analysis.
It does NOT perform the analysis itself, but defines the operationalization rules
that code/05_sensitivity_analysis.py will consume.

Definitions:
1. Conjunctive: High Emoji AND High Punctuation.
2. Disjunctive: High Emoji OR High Punctuation.
3. Threshold-based: Weighted sum of features exceeding a specific threshold.
"""
import json
from pathlib import Path
from typing import Dict, Any
import sys
import os

# Ensure we can import from the code directory if run as a script
if __name__ == "__main__":
    code_dir = Path(__file__).parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

from config import get_processed_data_dir

def get_sensitivity_definitions() -> Dict[str, Any]:
    """
    Returns a dictionary containing three alternative structural definitions
    for 'Cue Intensity'.
    
    These definitions align with FR-005 (structural rules) and exclude simple
    re-weighting of existing variables.
    """
    definitions = {
        "metadata": {
            "description": "Alternative structural definitions for Cue Intensity sensitivity analysis",
            "version": "1.0",
            "source_task": "T027"
        },
        "definitions": [
            {
                "id": "conjunctive",
                "name": "Conjunctive High Intensity",
                "logic": "AND",
                "description": "Cue Intensity is High ONLY if both Emoji Count is High AND Punctuation Count is High.",
                "conditions": {
                    "emoji_count": {
                        "operator": ">=",
                        "threshold": 2,
                        "source_column": "emoji_count"
                    },
                    "punctuation_count": {
                        "operator": ">=",
                        "threshold": 3,
                        "source_column": "punctuation_count"
                    }
                },
                "output_variable": "cue_intensity_conjunctive"
            },
            {
                "id": "disjunctive",
                "name": "Disjunctive High Intensity",
                "logic": "OR",
                "description": "Cue Intensity is High if EITHER Emoji Count is High OR Punctuation Count is High.",
                "conditions": {
                    "emoji_count": {
                        "operator": ">=",
                        "threshold": 1,
                        "source_column": "emoji_count"
                    },
                    "punctuation_count": {
                        "operator": ">=",
                        "threshold": 2,
                        "source_column": "punctuation_count"
                    }
                },
                "output_variable": "cue_intensity_disjunctive"
            },
            {
                "id": "threshold_weighted",
                "name": "Threshold-Based Composite",
                "logic": "SUM_THRESHOLD",
                "description": "Cue Intensity is High if a weighted sum of features exceeds a composite threshold. "
                              "Weights are fixed structural constants, not learned parameters.",
                "formula": "(emoji_count * 0.4) + (punctuation_count * 0.3) + (length_bonus * 0.3) >= 2.0",
                "components": [
                    {
                        "source_column": "emoji_count",
                        "weight": 0.4
                    },
                    {
                        "source_column": "punctuation_count",
                        "weight": 0.3
                    },
                    {
                        "source_column": "length_bonus",
                        "weight": 0.3,
                        "note": "Binary flag: 1 if message length > 50 chars, else 0"
                    }
                ],
                "composite_threshold": 2.0,
                "output_variable": "cue_intensity_threshold"
            }
        ]
    }
    return definitions

def save_definitions(output_path: Path) -> None:
    """
    Saves the sensitivity definitions to the specified JSON file.
    
    Args:
        output_path: Path to the output JSON file.
    """
    definitions = get_sensitivity_definitions()
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(definitions, f, indent=2)
    
    print(f"Sensitivity definitions saved to: {output_path}")

def main():
    """Main entry point for T027."""
    processed_dir = get_processed_data_dir()
    output_file = processed_dir / "sensitivity_definitions.json"
    
    if not processed_dir.exists():
        processed_dir.mkdir(parents=True, exist_ok=True)
        
    save_definitions(output_file)

if __name__ == "__main__":
    main()
