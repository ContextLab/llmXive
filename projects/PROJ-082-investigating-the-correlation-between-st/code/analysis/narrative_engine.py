"""
Narrative Synthesis Engine (Task T015b).

Reads themes and study counts to decide if a narrative should be generated.
If mode is 'narrative' or meta_status is 'skipped', it produces narrative_content.md.

Output: data/derived/narrative_content.md
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

def get_project_root() -> Path:
    """Find the project root (parent of 'code' directory)."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.name == "code":
            return parent.parent
    return current.parent

def load_json(path: Path) -> Optional[Dict]:
    """Load a JSON file, returning None if it doesn't exist or is invalid."""
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Failed to load JSON from {path}: {e}")
        return None

def should_generate_narrative(real_data_status: Optional[Dict], meta_status: Optional[Dict]) -> bool:
    """
    Determine if narrative synthesis is required based on data mode or meta-analysis status.
    Returns True if:
      - real_data_status['mode'] == 'narrative'
      - meta_status['status'] == 'skipped'
    """
    if not real_data_status:
        return False
    
    mode = real_data_status.get("mode", "")
    if mode == "narrative":
        return True
    
    if meta_status and meta_status.get("status") == "skipped":
        return True
    
    return False

def generate_narrative_content(study_count: int, themes: Optional[Dict]) -> str:
    """Generate the markdown content for the narrative synthesis."""
    content = f"# Narrative Synthesis of Brain Connectivity and Music Preferences\n\n"
    content += f"**Generated**: {datetime.utcnow().isoformat()}Z\n\n"
    content += f"## Overview\n\n"
    
    if study_count == 0:
        content += "No studies were found in the dataset. A quantitative meta-analysis could not be performed.\n\n"
    else:
        content += f"This synthesis is based on a qualitative analysis of {study_count} studies.\n\n"
    
    content += "## Thematic Findings\n\n"
    
    if themes:
        for theme, count in themes.items():
            content += f"- **{theme}**: Mentioned in {count} studies.\n"
        content += "\n"
    else:
        content += "No specific themes were identified in the extracted data.\n\n"
    
    content += "## Limitations\n\n"
    content += "This narrative synthesis is subject to the limitations of the source data and the qualitative extraction method.\n"
    content += "If the quantitative meta-analysis was skipped due to insufficient data, these limitations are compounded.\n"
    
    return content

def save_narrative_content(content: str, path: Path) -> None:
    """Write the narrative content to the specified file path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("narrative_engine")
    project_root = get_project_root()

    # Load inputs
    real_data_status = load_json(project_root / "data" / "processed" / "real_data_status.json")
    meta_status = load_json(project_root / "data" / "processed" / "meta_status.json")
    study_count_data = load_json(project_root / "data" / "processed" / "study_count.json")
    themes = load_json(project_root / "data" / "derived" / "narrative_themes.json")

    # Check if we should proceed
    if not should_generate_narrative(real_data_status, meta_status):
        logger.info("Conditions for narrative synthesis not met. Skipping generation.")
        return 0

    # Extract study count
    N = study_count_data.get("N", 0) if study_count_data else 0
    
    logger.info(f"Generating narrative synthesis for {N} studies.")
    
    # Generate content
    content = generate_narrative_content(N, themes)
    
    # Save output
    output_path = project_root / "data" / "derived" / "narrative_content.md"
    save_narrative_content(content, output_path)
    
    logger.info(f"Narrative content saved to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())