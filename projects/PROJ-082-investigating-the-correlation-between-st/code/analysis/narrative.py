"""
Narrative synthesis module for generating structured text summaries
when the eligible study count is insufficient for quantitative meta-analysis.

This module consumes qualitative notes extracted by T013 and the study count
from T014 to produce a standardized report.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing project utilities
from utils.logger import get_logger, log_fallback
from utils.config import get_project_root, ensure_directory

logger = get_logger(__name__)


def load_qualitative_notes(notes_path: str) -> List[Dict[str, Any]]:
    """
    Load qualitative notes from the extraction output JSON.

    Args:
        notes_path: Path to the JSON file containing extracted descriptors.

    Returns:
        List of dictionaries containing study details and qualitative notes.
    """
    path = Path(notes_path)
    if not path.exists():
        logger.warning(f"Qualitative notes file not found: {notes_path}")
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list format and dict with 'studies' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'studies' in data:
                return data['studies']
            else:
                logger.warning("Unexpected format in qualitative notes JSON")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse qualitative notes JSON: {e}")
        return []


def load_study_count(count_path: str) -> int:
    """
    Load the study count from the meta-analysis output JSON.

    Args:
        count_path: Path to the JSON file containing the study count.

    Returns:
        The number of eligible studies.
    """
    path = Path(count_path)
    if not path.exists():
        logger.warning(f"Study count file not found: {count_path}")
        return 0

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return int(data.get('study_count', 0))
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse study count JSON: {e}")
        return 0


def extract_themes(notes: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Extract recurring themes from qualitative notes.

    Args:
        notes: List of study dictionaries with qualitative data.

    Returns:
        Dictionary mapping tract names to lists of associated behaviors/observations.
    """
    themes = {}
    target_tracts = [
        'arcuate fasciculus', 'cingulum bundle', 'uncinate fasciculus',
        'arcuate', 'cingulum', 'uncinate', 'superior longitudinal fasciculus',
        'slf', 'corpus callosum', 'inferior longitudinal fasciculus', 'ilf'
    ]

    for note in notes:
        if note.get('no_qualitative_data', False):
            continue

        tract_name = note.get('tract_name', '').lower()
        observation = note.get('qualitative_description', '')

        # Check if this tract matches our target list
        for target in target_tracts:
            if target in tract_name:
                if target not in themes:
                    themes[target] = []
                if observation and observation not in themes[target]:
                    themes[target].append(observation)
                break

    return themes


def generate_overview(study_count: int, references: List[Dict[str, Any]]) -> str:
    """
    Generate the Study Overview section.

    Args:
        study_count: Number of eligible studies.
        references: List of reference dictionaries with author and year.

    Returns:
        Formatted overview text.
    """
    refs_text = ""
    if references:
        ref_strs = []
        for ref in references:
            author = ref.get('author', 'Unknown')
            year = ref.get('year', 'n.d.')
            ref_strs.append(f"{author} et al. ({year})")
        refs_text = "References include " + ", ".join(ref_strs) + "."

    overview = f"""## Study Overview
This study investigates the correlation between structural brain connectivity (dMRI metrics) and individual music preferences. The methodology employs a qualitative thematic analysis to identify emerging trends regarding neural circuitry. {refs_text}
"""
    return overview


def generate_themes(themes: Dict[str, List[str]]) -> str:
    """
    Generate the Qualitative Themes section.

    Args:
        themes: Dictionary mapping tract names to observations.

    Returns:
        Formatted themes text.
    """
    if not themes:
        return """## Qualitative Themes
No specific tract-behavior associations were identified in the extracted qualitative data.
"""

    theme_text = "## Qualitative Themes\n"
    theme_text += "The analysis focuses on categorizing recurring themes regarding specific tracts and their reported associations with music preference behaviors.\n\n"

    for tract, observations in sorted(themes.items()):
        # Capitalize tract name for display
        display_name = tract.title()
        theme_text += f"### {display_name}\n"
        for obs in observations:
            theme_text += f"- {obs}\n"
        theme_text += "\n"

    return theme_text


def generate_limitations(study_count: int) -> str:
    """
    Generate the Limitations section.

    Args:
        study_count: Number of eligible studies.

    Returns:
        Formatted limitations text.
    """
    limitations = f"""## Limitations
The scope is constrained by the limited number of eligible studies (N = {study_count} < 10), precluding quantitative meta-analysis.
This narrative synthesis approach, while informative, lacks the statistical power and precision of a full meta-analytic approach.
Further research with larger sample sizes is required to draw definitive conclusions about the relationship between structural brain connectivity and music preferences.
"""
    return limitations


def generate_narrative_summary(
    notes_path: str,
    count_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Generate a structured text summary if eligible study count < 10.

    This function consumes qualitative notes from T013 and study count from T014.
    It produces a markdown report and a JSON metadata block.

    Args:
        notes_path: Path to the JSON file with qualitative notes (from T013).
        count_path: Path to the JSON file with study count (from T014).
        output_path: Path where the markdown report will be saved.

    Returns:
        Dictionary containing the summary and metadata.
    """
    # Load inputs
    notes = load_qualitative_notes(notes_path)
    study_count = load_study_count(count_path)

    # Check eligibility
    if study_count >= 10:
        logger.info(f"Study count ({study_count}) >= 10. Narrative mode not triggered.")
        return {
            "status": "skipped",
            "reason": "Study count sufficient for quantitative analysis",
            "study_count": study_count
        }

    if study_count == 0:
        logger.warning("No studies found. Generating empty narrative summary.")

    # Extract data
    themes = extract_themes(notes)
    references = [n for n in notes if n.get('author') and n.get('year')]

    # Generate sections
    overview = generate_overview(study_count, references)
    themes_text = generate_themes(themes)
    limitations = generate_limitations(study_count)

    # Assemble full report
    timestamp = datetime.now().isoformat()
    report = f"""# Narrative Synthesis Report: Brain Connectivity and Music Preferences

## Metadata
```json
{{
  "study_count": {study_count},
  "synthesis_mode": "narrative",
  "timestamp": "{timestamp}"
}}
```

{overview}
{themes_text}
{limitations}
"""

    # Ensure output directory exists
    ensure_directory(output_path)

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"Narrative summary generated successfully at {output_path}")

    # Return metadata
    return {
        "status": "completed",
        "study_count": study_count,
        "synthesis_mode": "narrative",
        "timestamp": timestamp,
        "output_path": output_path,
        "themes_identified": len(themes),
        "references_count": len(references)
    }


def main():
    """
    Main entry point for running the narrative synthesis.
    Uses default paths based on project structure.
    """
    project_root = get_project_root()

    # Default paths
    notes_path = project_root / "data" / "derived" / "qualitative_notes.json"
    count_path = project_root / "data" / "derived" / "meta_analysis_result.json"
    output_path = project_root / "data" / "derived" / "narrative_summary.md"

    # Allow override via environment variables
    notes_path = os.getenv("NARRATIVE_NOTES_PATH", str(notes_path))
    count_path = os.getenv("NARRATIVE_COUNT_PATH", str(count_path))
    output_path = os.getenv("NARRATIVE_OUTPUT_PATH", str(output_path))

    logger.info(f"Running narrative synthesis with inputs: notes={notes_path}, count={count_path}")

    result = generate_narrative_summary(notes_path, count_path, output_path)

    # Print result summary
    if result.get("status") == "skipped":
        logger.info(f"Narrative synthesis skipped: {result.get('reason')}")
    else:
        logger.info(f"Narrative synthesis completed. Themes: {result.get('themes_identified')}, References: {result.get('references_count')}")

    return result


if __name__ == "__main__":
    main()