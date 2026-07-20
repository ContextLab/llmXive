"""
Generate the tract lexicon configuration file.

This script produces `data/config/tract_lexicon.yaml` containing
specific tract names and directional verbs required for the
NLP extraction logic (T007d-2) and parser (T013).

Output:
    data/config/tract_lexicon.yaml
"""
import os
import sys
from pathlib import Path
import yaml

# Ensure we can import from the project root if run as a script
# but rely on the project structure for imports if run via module
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger

logger = get_logger(__name__)

# Define the required lexicon content as per task specification
LEXICON_DATA = {
    "tract_names": [
        "arcuate fasciculus",
        "cingulum bundle",
        "uncinate fasciculus",
        "inferior longitudinal fasciculus",
        "auditory cortex",
        "ventral striatum"
    ],
    "directional_verbs": [
        "increased",
        "decreased",
        "correlated",
        "associated with"
    ]
}

def generate_lexicon(output_path: Path) -> None:
    """
    Write the tract lexicon to a YAML file.

    Args:
        output_path: The path where the YAML file will be saved.
    """
    ensure_directory(output_path)
    
    logger.info(f"Generating tract lexicon at: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(LEXICON_DATA, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Successfully generated tract lexicon with {len(LEXICON_DATA['tract_names'])} tracts and {len(LEXICON_DATA['directional_verbs'])} verbs.")

def main():
    """Main entry point for the script."""
    project_root = get_project_root()
    output_path = project_root / "data" / "config" / "tract_lexicon.yaml"
    
    try:
        generate_lexicon(output_path)
        logger.info("Lexicon generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate lexicon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()