"""
Generate Narrative Summary (Task T015c).

Consumes narrative_content.md and produces narrative_summary.md with JSON metadata.

Output: data/derived/narrative_summary.md
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.name == "code":
            return parent.parent
    return current.parent

def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("narrative_generator")
    project_root = get_project_root()

    input_path = project_root / "data" / "derived" / "narrative_content.md"
    output_path = project_root / "data" / "derived" / "narrative_summary.md"

    if not input_path.exists():
        logger.warning("narrative_content.md not found. Creating empty summary.")
        content = "# No studies found\n\nNo data was available for synthesis."
    else:
        with open(input_path, 'r') as f:
            content = f.read()

    # Add JSON metadata block
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "type": "narrative_summary",
        "version": "1.0"
    }
    
    final_output = f"<!-- META: {json.dumps(metadata)} -->\n\n{content}"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(final_output)
    
    logger.info(f"Narrative summary saved to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
