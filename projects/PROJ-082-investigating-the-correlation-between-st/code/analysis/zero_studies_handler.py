"""
No-Studies-Found Handler (Task T043).

Generates narrative_summary.md with header '# No studies found' when N=0.
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

def load_study_count() -> int:
    path = get_project_root() / "data" / "processed" / "study_count.json"
    if not path.exists():
        return 0
    with open(path) as f:
        data = json.load(f)
    return data.get("N", 0)

def generate_zero_studies_summary() -> str:
    content = "# No studies found\n\n"
    content += "The analysis could not identify any studies meeting the inclusion criteria.\n\n"
    content += "## Implications\n\n"
    content += "No quantitative or qualitative synthesis could be performed due to the absence of data.\n"
    return content

def run_zero_case_handler() -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("zero_handler")
    project_root = get_project_root()

    N = load_study_count()
    if N != 0:
        logger.info(f"N={N}. Zero case handler not needed.")
        return 0

    content = generate_zero_studies_summary()
    output_path = project_root / "data" / "derived" / "narrative_summary.md"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Zero studies summary written to {output_path}")
    return 0

def main() -> int:
    return run_zero_case_handler()

if __name__ == "__main__":
    sys.exit(main())