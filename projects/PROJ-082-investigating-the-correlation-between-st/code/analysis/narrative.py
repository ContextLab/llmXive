"""
Narrative synthesis module for generating structured text summaries when
quantitative meta-analysis is not feasible (N < 10).
"""
import json
import os
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from local utils to ensure project consistency
from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)


def load_methodology_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the narrative methodology configuration from YAML.

    Args:
        config_path: Path to the methodology YAML file. Defaults to
                     data/config/narrative_methodology.yaml.

    Returns:
        Dictionary containing the coding scheme.
    """
    root = get_project_root()
    if config_path is None:
        config_path = root / "data" / "config" / "narrative_methodology.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Methodology config not found at {config_path}")

    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_qualitative_notes(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load extracted qualitative descriptors from the processed CSV.

    Args:
        input_path: Path to extracted_studies.csv. Defaults to
                    data/processed/extracted_studies.csv.

    Returns:
        List of dictionaries containing study metadata and qualitative descriptions.
    """
    root = get_project_root()
    if input_path is None:
        input_path = root / "data" / "processed" / "extracted_studies.csv"
    else:
        input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found at {input_path}")

    studies = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only include studies that have a qualitative description and are in the narrative pool
            if row.get('narrative_pool', 'False') == 'True' and row.get('qualitative_desc'):
                studies.append({
                    'author': row.get('author', 'Unknown'),
                    'year': row.get('year', 'n.d.'),
                    'tract': row.get('tract', 'Unknown'),
                    'qualitative_desc': row.get('qualitative_desc', ''),
                    'qualitative_desc': row['qualitative_desc'].strip()
                })
    return studies


def load_study_count(count_path: Optional[str] = None) -> int:
    """
    Load the study count from the study_count.json file.

    Args:
        count_path: Path to study_count.json. Defaults to
                    data/processed/study_count.json.

    Returns:
        The integer study count N.
    """
    root = get_project_root()
    if count_path is None:
        count_path = root / "data" / "processed" / "study_count.json"
    else:
        count_path = Path(count_path)

    if not count_path.exists():
        raise FileNotFoundError(f"Study count file not found at {count_path}")

    with open(count_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return int(data.get('N', 0))


def load_themes_json(themes_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the pre-computed narrative themes from JSON.

    Args:
        themes_path: Path to narrative_themes.json. Defaults to
                     data/derived/narrative_themes.json.

    Returns:
        Dictionary of themes and their frequencies.
    """
    root = get_project_root()
    if themes_path is None:
        themes_path = root / "data" / "derived" / "narrative_themes.json"
    else:
        themes_path = Path(themes_path)

    if not themes_path.exists():
        logger.warning(f"Themes file not found at {themes_path}, generating empty themes.")
        return {"themes": [], "total_studies": 0}

    with open(themes_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_themes(studies: List[Dict], methodology: Dict) -> Dict[str, Any]:
    """
    Extract and categorize themes based on the methodology config.
    This is a fallback if the themes JSON is missing, but T015a should have generated it.
    """
    themes = defaultdict(list)
    keywords = methodology.get('keywords', [])
    
    for study in studies:
        desc = study['qualitative_desc'].lower()
        matched_themes = []
        for kw in keywords:
            if kw.lower() in desc:
                matched_themes.append(kw)
        
        if not matched_themes:
            matched_themes.append("General Connectivity")
        
        for theme in matched_themes:
            themes[theme].append(study)

    return {
        "themes": [{"name": k, "count": len(v), "studies": v} for k, v in themes.items()],
        "total_studies": len(studies)
    }


def generate_overview(study_count: int, timestamp: str) -> str:
    """
    Generate the Study Overview section.
    """
    return f"""## Study Overview

**Methodology**: Systematic Review Fallback (Narrative Synthesis)
**Study Count**: {study_count}
**Timestamp**: {timestamp}

This summary is generated using a narrative synthesis approach because the number of eligible studies ({study_count}) is below the threshold required for quantitative meta-analysis (N < 10). The analysis follows the coding scheme defined in `data/config/narrative_methodology.yaml`.

### References
The following studies were included in the qualitative pool:
"""


def generate_themes(themes_data: Dict[str, Any]) -> str:
    """
    Generate the Qualitative Themes section.
    """
    if not themes_data.get('themes'):
        return "\n## Qualitative Themes\n\nNo specific themes identified in the available literature.\n"

    lines = ["## Qualitative Themes\n"]
    
    for theme in themes_data['themes']:
        name = theme['name']
        count = theme['count']
        lines.append(f"\n### {name} ({count} studies)")
        lines.append("")
        
        # List studies contributing to this theme
        for study in theme['studies']:
            author = study['author']
            year = study['year']
            tract = study['tract']
            desc = study['qualitative_desc']
            lines.append(f"- **{author} ({year})**: {tract} - {desc}")
        
        lines.append("")

    return "\n".join(lines)


def generate_limitations(study_count: int) -> str:
    """
    Generate the Limitations section, explicitly stating the N < 10 constraint.
    """
    return f"""## Limitations

**Data Insufficient for Quantitative Synthesis**: This review is based on only {study_count} studies, which is below the minimum threshold (N >= 10) required to perform a random-effects meta-analysis. Consequently:

1. **Statistical Power**: The ability to detect a true effect size is significantly reduced.
2. **Heterogeneity Assessment**: Metrics such as I² and Egger's regression test cannot be reliably calculated or interpreted with this sample size.
3. **Generalizability**: Findings are preliminary and should be interpreted with caution. Further research with larger sample sizes is required to confirm these associations.

**Systematic Review Fallback**: As per Constitution Principle VII, this narrative summary serves as a fallback to ensure that no data is discarded, even when quantitative aggregation is not feasible.
"""


def generate_narrative_summary(
    study_count: int,
    themes_data: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Generate the full structured text summary (Markdown).

    Args:
        study_count: Total number of studies (N).
        themes_data: Dictionary containing theme analysis.
        output_path: Path for the output MD file. Defaults to
                     data/derived/narrative_summary.md.

    Returns:
        The generated markdown string.
    """
    timestamp = datetime.now().isoformat()
    
    # Construct metadata block
    metadata = {
        "study_count": study_count,
        "synthesis_mode": "narrative",
        "timestamp": timestamp
    }
    
    # Handle Zero-Studies Edge Case
    if study_count == 0:
        header = "# No studies found"
        content = f"""
## Study Overview

**Methodology**: Systematic Review Fallback (Narrative Synthesis)
**Study Count**: 0
**Timestamp**: {timestamp}

No studies were found that met the inclusion criteria or contained qualitative descriptors.

## Limitations

**Data Insufficient**: No data was available for synthesis.
"""
    else:
        header = "# Correlation Between Structural Brain Connectivity and Music Preferences: Narrative Summary"
        overview = generate_overview(study_count, timestamp)
        themes_section = generate_themes(themes_data)
        limitations = generate_limitations(study_count)
        
        content = f"""
{overview}

{themes_section}
{limitations}
"""

    full_md = f"""```json
{json.dumps(metadata, indent=2)}
```

{header}
{content}
"""

    root = get_project_root()
    if output_path is None:
        output_path = root / "data" / "derived" / "narrative_summary.md"
    else:
        output_path = Path(output_path)

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_md)

    logger.info(f"Narrative summary generated at {output_path}")
    return full_md


def main():
    """
    Main entry point for the narrative generation task.
    Orchestrates loading data and generating the summary.
    """
    try:
        # 1. Load Study Count
        logger.info("Loading study count...")
        study_count = load_study_count()
        logger.info(f"Study count: {study_count}")

        # 2. Load Themes (from T015a output)
        logger.info("Loading narrative themes...")
        try:
            themes_data = load_themes_json()
        except FileNotFoundError:
            # Fallback: Load raw studies and re-extract if themes file missing
            logger.warning("Themes file missing. Loading raw studies and re-extracting.")
            methodology = load_methodology_config()
            studies = load_qualitative_notes()
            themes_data = extract_themes(studies, methodology)

        # 3. Generate Summary
        logger.info("Generating narrative summary...")
        generate_narrative_summary(study_count, themes_data)
        
        logger.info("Narrative generation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Narrative generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())