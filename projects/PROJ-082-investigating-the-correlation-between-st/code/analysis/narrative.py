import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import get_logger, log_fallback

logger = get_logger(__name__)

def load_qualitative_notes(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load qualitative notes from a JSON file.
    If input_path is None or file does not exist, returns an empty list.
    """
    if input_path is None:
        return []
    
    path = Path(input_path)
    if not path.exists():
        logger.warning(f"Qualitative notes file not found: {path}")
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'notes' in data:
                return data['notes']
            else:
                logger.warning("Unexpected format in qualitative notes file")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse qualitative notes JSON: {e}")
        return []

def load_study_count(input_path: Optional[str] = None) -> int:
    """
    Load study count from a JSON file.
    If input_path is None or file does not exist, returns 0.
    """
    if input_path is None:
        return 0
    
    path = Path(input_path)
    if not path.exists():
        logger.warning(f"Study count file not found: {path}")
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
    Extract themes from qualitative notes.
    Returns a dictionary mapping theme categories to lists of extracted strings.
    """
    themes: Dict[str, List[str]] = {
        'tracts': [],
        'behaviors': [],
        'findings': []
    }
    
    for note in notes:
        if isinstance(note, dict):
            if note.get('tract'):
                themes['tracts'].append(note['tract'])
            if note.get('behavior'):
                themes['behaviors'].append(note['behavior'])
            if note.get('finding'):
                themes['findings'].append(note['finding'])
    
    return themes

def generate_overview(study_count: int, references: Optional[List[str]] = None) -> str:
    """
    Generate the study overview section of the narrative.
    Handles the zero-studies edge case explicitly.
    """
    if study_count == 0:
        return (
            "## Study Overview\n"
            "This systematic review investigated the correlation between structural brain "
            "connectivity (dMRI metrics) and individual music preferences. However, no eligible "
            "studies were found in the input dataset that met the inclusion criteria. "
            "Consequently, no quantitative or qualitative synthesis could be performed. "
            "References: None available."
        )
    
    ref_text = ", ".join(references) if references else "Various authors"
    return (
        f"## Study Overview\n"
        f"This study investigates the correlation between structural brain connectivity "
        f"(dMRI metrics) and individual music preferences. The methodology employs a qualitative "
        f"thematic analysis to identify emerging trends regarding neural circuitry. "
        f"References include {ref_text}."
    )

def generate_themes(themes: Dict[str, List[str]], study_count: int) -> str:
    """
    Generate the qualitative themes section.
    Handles the zero-studies edge case.
    """
    if study_count == 0:
        return (
            "## Qualitative Themes\n"
            "No qualitative themes could be extracted as no eligible studies were found "
            "in the input dataset."
        )
    
    lines = [
        "## Qualitative Themes",
        "The analysis focuses on categorizing recurring themes regarding specific tracts "
        "(e.g., arcuate fasciculus, cingulum bundle) and their reported associations with "
        "music preference behaviors."
    ]
    
    if themes['tracts']:
        unique_tracts = list(set(themes['tracts']))
        lines.append(f"\n- **Tracts mentioned**: {', '.join(unique_tracts)}")
    
    if themes['behaviors']:
        unique_behaviors = list(set(themes['behaviors']))
        lines.append(f"- **Behaviors observed**: {', '.join(unique_behaviors)}")
    
    if themes['findings']:
        lines.append(f"\n- **Key findings**:\n")
        for finding in themes['findings'][:5]:  # Limit to top 5
            lines.append(f"  - {finding}")
    
    return "\n".join(lines)

def generate_limitations(study_count: int) -> str:
    """
    Generate the limitations section.
    Handles the zero-studies edge case explicitly.
    """
    if study_count == 0:
        return (
            "## Limitations\n"
            "The primary limitation of this review is the complete absence of eligible studies "
            "meeting the inclusion criteria. This precludes any form of synthesis, quantitative "
            "or qualitative. Future research efforts should focus on identifying and extracting "
            "relevant studies that explicitly report dMRI connectivity metrics in relation to "
            "music preference behaviors."
        )
    
    return (
        "## Limitations\n"
        f"The scope is constrained by the limited number of eligible studies (N = {study_count} < 10), "
        f"precluding quantitative meta-analysis.\n"
        "Additionally, the heterogeneity of dMRI methodologies and music preference assessments "
        "across studies may limit the comparability of effect sizes."
    )

def generate_narrative_summary(
    study_count: int,
    notes: List[Dict[str, Any]],
    output_path: str
) -> Dict[str, Any]:
    """
    Generate the full narrative summary and write it to a JSON file.
    Handles the zero-studies edge case by producing a valid "No studies found" summary.
    """
    timestamp = datetime.now().isoformat()
    synthesis_mode = "narrative_zero_studies" if study_count == 0 else "narrative"
    
    themes = extract_themes(notes)
    
    summary_text = "\n\n".join([
        generate_overview(study_count),
        generate_themes(themes, study_count),
        generate_limitations(study_count)
    ])
    
    result = {
        "study_count": study_count,
        "synthesis_mode": synthesis_mode,
        "timestamp": timestamp,
        "narrative_summary": summary_text,
        "themes": themes,
        "eligibility_status": "no_studies_found" if study_count == 0 else "included"
    }
    
    # Write to output file
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path_obj, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Narrative summary generated with {study_count} studies and saved to {output_path}")
    
    return result

def main():
    """
    Main entry point for the narrative module.
    Reads study count and qualitative notes, generates narrative summary.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate narrative summary from meta-analysis data")
    parser.add_argument("--study-count", type=str, required=True, help="Path to study count JSON")
    parser.add_argument("--notes", type=str, required=False, help="Path to qualitative notes JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output narrative JSON")
    
    args = parser.parse_args()
    
    study_count = load_study_count(args.study_count)
    notes = load_qualitative_notes(args.notes)
    
    if study_count == 0:
        logger.warning("Zero studies found. Generating 'No studies found' narrative summary.")
    
    result = generate_narrative_summary(study_count, notes, args.output)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()