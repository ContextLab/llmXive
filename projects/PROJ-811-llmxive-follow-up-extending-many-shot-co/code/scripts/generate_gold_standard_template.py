"""
Script to generate a template for the Gold Standard Annotations file.

This script handles the 'deferred' assumption for T015:
If data/processed/gold_standard_annotations.json is missing, it generates a
template file with instructions for expert annotation rather than failing.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

# Import from existing project structure
try:
    from code.src.config import PROJECT_ROOT
except ImportError:
    # Fallback for direct execution if config isn't fully set up yet
    PROJECT_ROOT = Path(__file__).parent.parent.parent

GOLD_STANDARD_PATH = PROJECT_ROOT / "data" / "processed" / "gold_standard_annotations.json"

def generate_template() -> Dict[str, Any]:
    """
    Generates the template structure for expert annotation.
    
    The template includes:
    1. Metadata about the file generation
    2. A list of examples requiring annotation
    3. Instructions for the expert annotator
    4. Placeholder fields for the 'human-rated logical complexity' score
    """
    template = {
        "metadata": {
            "description": "Gold Standard Annotations for Logical Dependency vs. Semantic Curvature Study",
            "generated_by": "generate_gold_standard_template.py",
            "status": "DEFERRED",
            "instruction": (
              "This file is a template. Please populate the 'annotations' list with "
              "expert human ratings for a subset of 50 traces from the 'aaabiao/DAG_sft' dataset. "
              "Each annotation must include the 'trace_id', 'raw_trace' (or a hash), and the "
              "'human_rated_complexity' score (1-5 scale or continuous)."
            ),
            "required_fields": [
                "trace_id",
                "human_rated_complexity",
                "annotator_id",
                "notes"
            ],
            "target_count": 50
        },
        "annotations": [
            {
                "trace_id": "example_trace_id_001",
                "human_rated_complexity": None,  # To be filled by expert
                "annotator_id": None,
                "notes": "Awaiting expert review. Please rate logical complexity based on depth of dependency chains."
            }
        ]
    }
    return template

def main():
    """Main entry point to generate the template file."""
    processed_dir = GOLD_STANDARD_PATH.parent
    
    # Ensure directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    if GOLD_STANDARD_PATH.exists():
        print(f"File {GOLD_STANDARD_PATH} already exists. Skipping generation.")
        print("Delete the file manually if you wish to regenerate the template.")
        return

    template_data = generate_template()
    
    with open(GOLD_STANDARD_PATH, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, indent=2)
    
    print(f"Template generated successfully at: {GOLD_STANDARD_PATH}")
    print("Please open this file and fill in the 'annotations' list with real expert data.")

if __name__ == "__main__":
    main()
