"""
Thematic aggregation logic for narrative synthesis.
Reads extracted studies and methodology config to aggregate qualitative descriptors by theme.
"""
import json
import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
# Add parent directory to path to allow imports if running as script
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

# Default theme mapping if specific rules aren't found in config
DEFAULT_THEME_KEYWORDS = {
    "auditory-reward pathway": [
        "auditory", "reward", "striatum", "ventral", "dopamine", "pleasure", "music", "sound"
    ],
    "frontal connectivity": [
        "frontal", "prefrontal", "cortex", "executive", "cognitive", "control", "dorsolateral"
    ],
    "limbic system": [
        "amygdala", "hippocampus", "limbic", "emotion", "affect", "mood"
    ],
    "structural integrity": [
        "integrity", "fractional anisotropy", "fa", "md", "diffusion", "tract", "white matter"
    ],
    "general connectivity": [
        "connectivity", "connection", "association", "correlation", "linked", "associated"
    ]
}

def load_methodology_config(config_path: Path) -> Dict[str, Any]:
    """Load the narrative methodology configuration."""
    if not config_path.exists():
        logger.warning(f"Methodology config not found at {config_path}, using defaults.")
        return {"keywords": [], "sentiment_rules": {}, "exclusion_criteria": []}
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load methodology config: {e}")
        return {}

def load_extracted_studies(csv_path: Path) -> List[Dict[str, Any]]:
    """Load the extracted studies CSV."""
    studies = []
    if not csv_path.exists():
        logger.error(f"Extracted studies file not found at {csv_path}")
        return studies
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)
    return studies

def extract_themes(studies: List[Dict[str, Any]], methodology: Dict[str, Any]) -> Dict[str, int]:
    """
    Aggregate qualitative descriptions by theme.
    
    Args:
        studies: List of study dictionaries with 'qualitative_desc' field.
        methodology: Configuration containing keywords and rules.
    
    Returns:
        Dictionary mapping theme names to their frequency counts.
    """
    theme_counts = defaultdict(int)
    
    # Determine keywords to use: config overrides or extends defaults
    config_keywords = methodology.get("keywords", [])
    # If config has specific theme mapping, use it; otherwise use defaults
    theme_rules = methodology.get("theme_rules", DEFAULT_THEME_KEYWORDS)
    
    for study in studies:
        desc = study.get("qualitative_desc", "")
        if not desc or not isinstance(desc, str):
            continue
        
        desc_lower = desc.lower()
        matched_themes = set()
        
        # Check against theme rules
        for theme, keywords in theme_rules.items():
            if theme == "exclusion_criteria":
                continue
            for keyword in keywords:
                if keyword.lower() in desc_lower:
                    matched_themes.add(theme)
                    break  # One match per theme is enough
        
        # If no specific theme matched, check generic keywords from config
        if not matched_themes and config_keywords:
            for keyword in config_keywords:
                if keyword.lower() in desc_lower:
                    theme_counts["general"] += 1
                    break
        
        # Increment counts for matched themes
        for theme in matched_themes:
            theme_counts[theme] += 1

    return dict(theme_counts)

def generate_themes_json(theme_counts: Dict[str, int], output_path: Path) -> None:
    """Write the theme counts to the output JSON file."""
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "total_studies_processed": sum(theme_counts.values()),
        "themes": theme_counts
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Narrative themes written to {output_path}")

def run_narrative_logic(
    extracted_studies_path: Path,
    methodology_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Main entry point for narrative logic execution.
    
    Args:
        extracted_studies_path: Path to extracted_studies.csv
        methodology_path: Path to narrative_methodology.yaml
        output_path: Path for narrative_themes.json
    
    Returns:
        The generated theme data dictionary.
    """
    logger.info("Starting narrative theme aggregation...")
    
    methodology = load_methodology_config(methodology_path)
    studies = load_extracted_studies(extracted_studies_path)
    
    if not studies:
        logger.warning("No studies found in extracted_studies.csv. Generating empty themes.")
        theme_counts = {}
    else:
        theme_counts = extract_themes(studies, methodology)
    
    generate_themes_json(theme_counts, output_path)
    
    return {"themes": theme_counts, "count": len(theme_counts)}

def main() -> int:
    """CLI entry point."""
    project_root = get_project_root()
    extracted_studies_path = project_root / "data" / "processed" / "extracted_studies.csv"
    methodology_path = project_root / "data" / "config" / "narrative_methodology.yaml"
    output_path = project_root / "data" / "derived" / "narrative_themes.json"
    
    try:
        result = run_narrative_logic(extracted_studies_path, methodology_path, output_path)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Narrative logic failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())