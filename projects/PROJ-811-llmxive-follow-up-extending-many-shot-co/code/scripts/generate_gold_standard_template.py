import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from code.src.config import PROJECT_ROOT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOLD_STANDARD_PATH = PROJECT_ROOT / "data" / "processed" / "gold_standard_annotations.json"

def generate_template() -> Dict[str, Any]:
    """
    Generates the template structure for gold standard annotations.
    This template is designed to be filled by human experts.
    
    Structure:
    {
        "metadata": {
            "description": "...",
            "instructions": "...",
            "version": "1.0"
        },
        "annotations": [
            {
                "example_id": "...",
                "trace_snippet": "...",
                "human_complexity_rating": <int 1-5>,
                "notes": "..."
            }
        ]
    }
    """
    template = {
        "metadata": {
            "description": "Gold Standard Annotations for Logical Complexity vs. DAG Depth",
            "instructions": (
                "Please review the provided CoT trace snippets and assign a 'human_complexity_rating' "
                "from 1 (Very Simple/Linear) to 5 (Very Complex/Highly Interdependent). "
                "This rating should reflect the perceived logical difficulty of the reasoning chain, "
                "independent of the specific domain content. "
                "Ensure the 'example_id' matches an ID from the source dataset (aaabiao/DAG_sft)."
            ),
            "version": "1.0",
            "created_by": "system",
            "status": "template"
        },
        "annotations": []
    }
    return template

def load_gold_standard(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Loads the gold standard annotations if the file exists.
    Returns None if the file is missing or invalid.
    """
    target_path = path if path else GOLD_STANDARD_PATH
    if not target_path.exists():
        logger.warning(f"Gold standard file not found at {target_path}")
        return None
    
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if "annotations" not in data:
            logger.error(f"Gold standard file at {target_path} is missing 'annotations' key")
            return None
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in gold standard file: {e}")
        return None

def save_gold_standard(data: Dict[str, Any], path: Optional[Path] = None) -> bool:
    """
    Saves the gold standard data to the specified path.
    """
    target_path = path if path else GOLD_STANDARD_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved gold standard to {target_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to save gold standard: {e}")
        return False

def main():
    """
    Main entry point for generating the gold standard template.
    Checks if the file exists. If not, generates a template.
    If it exists, logs a message indicating it is skipped.
    """
    if GOLD_STANDARD_PATH.exists():
        logger.info(f"Gold standard file already exists at {GOLD_STANDARD_PATH}. Skipping generation.")
        logger.info("To regenerate, manually delete the file and run this script again.")
        return

    logger.info(f"Gold standard file missing at {GOLD_STANDARD_PATH}. Generating template...")
    template = generate_template()
    
    if save_gold_standard(template):
        logger.info("Template generation complete.")
        logger.info("INSTRUCTIONS: Please open data/processed/gold_standard_annotations.json, "
                    "fill in the 'annotations' list with human-rated examples, and set "
                    "metadata.status to 'complete' when finished.")
    else:
        logger.error("Template generation failed.")
        exit(1)

if __name__ == "__main__":
    main()
