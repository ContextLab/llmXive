import json
import os
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from utils.logger import get_logger, log_fallback

logger = get_logger(__name__)

def load_methodology_config(config_path: Path) -> Dict[str, Any]:
    """Load the narrative methodology configuration."""
    if not config_path.exists():
        logger.error(f"Methodology config not found: {config_path}")
        raise FileNotFoundError(f"Methodology config not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_qualitative_notes(file_path: Path) -> List[Dict[str, Any]]:
    """Load qualitative notes from a CSV file."""
    studies = []
    if not file_path.exists():
        logger.warning(f"Input CSV file not found: {file_path}")
        return studies
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append({
                'study_id': row.get('study_id', ''),
                'qualitative_desc': row.get('qualitative_desc', ''),
                'narrative_pool': row.get('narrative_pool', 'false').lower() == 'true'
            })
    return studies

def load_study_count(file_path: Path) -> int:
    """Load study count from a JSON file."""
    if not file_path.exists():
        logger.warning(f"Study count file not found: {file_path}")
        return 0
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data.get('study_count', 0)

def extract_themes(studies: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract recurring themes from qualitative descriptions based on methodology config."""
    themes = {}
    keywords = [k['term'] for k in config.get('coding_scheme', {}).get('keywords', [])]
    
    for study in studies:
        if not study.get('qualitative_desc'):
            continue
        
        desc = study['qualitative_desc'].lower()
        study_id = study['study_id']
        
        for keyword in keywords:
            if keyword in desc:
                if keyword not in themes:
                    themes[keyword] = []
                if study_id not in themes[keyword]:
                    themes[keyword].append(study_id)
    
    return themes

def generate_overview(study_count: int, synthesis_mode: str) -> str:
    """Generate the study overview section."""
    return f"""## Study Overview

This narrative synthesis includes **{study_count}** eligible studies.
Synthesis mode: **{synthesis_mode}**.

Due to the limited number of studies (N < 10), a quantitative meta-analysis was not performed. Instead, a qualitative narrative synthesis was conducted to summarize findings and identify recurring themes.
"""

def generate_themes(themes: Dict[str, List[str]]) -> str:
    """Generate the qualitative themes section."""
    if not themes:
        return "## Qualitative Themes\n\nNo specific themes could be identified from the available qualitative data."
    
    theme_text = "## Qualitative Themes\n\n"
    for theme, studies in sorted(themes.items()):
        theme_text += f"### {theme.capitalize()}\n"
        theme_text += f"Studies mentioning this theme: {', '.join(studies)}\n\n"
    
    return theme_text

def generate_limitations(study_count: int) -> str:
    """Generate the limitations section."""
    return f"""## Limitations

1. **Sample Size**: Only {study_count} studies were eligible for inclusion, which is below the threshold (N ≥ 10) required for quantitative meta-analysis.
2. **Heterogeneity**: The small sample size prevents robust assessment of heterogeneity across studies.
3. **Publication Bias**: With limited studies, formal tests for publication bias (e.g., Egger's regression) cannot be reliably performed.
4. **Generalizability**: Findings may not be generalizable to broader populations due to the limited number of studies.
"""

def generate_narrative_summary(
    input_csv_path: Path,
    study_count_path: Path,
    config_path: Path,
    output_path: Path
) -> None:
    """Generate a comprehensive narrative summary."""
    # Load inputs
    config = load_methodology_config(config_path)
    studies = load_qualitative_notes(input_csv_path)
    study_count_from_file = load_study_count(study_count_path)
    
    # Use the actual count from the CSV if available, otherwise from JSON
    actual_study_count = len(studies) if studies else study_count_from_file
    
    synthesis_mode = "narrative" if actual_study_count < 10 else "quantitative"
    
    # Extract themes
    themes = extract_themes(studies, config)
    
    # Build the markdown content
    content = f"""# Narrative Synthesis: Structural Brain Connectivity and Music Preferences

```json
{{
  "study_count": {actual_study_count},
  "synthesis_mode": "{synthesis_mode}",
  "timestamp": "{datetime.utcnow().isoformat()}"
}}
```

{generate_overview(actual_study_count, synthesis_mode)}
{generate_themes(themes)}
{generate_limitations(actual_study_count)}
"""
    
    # Handle zero studies case
    if actual_study_count == 0:
        content = """# No studies found

```json
{
  "study_count": 0,
  "synthesis_mode": "narrative",
  "timestamp": "
```

No eligible studies were found for this analysis.
"""
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Narrative summary generated: {output_path}")

def main() -> None:
    """Main entry point for narrative synthesis."""
    import argparse
    parser = argparse.ArgumentParser(description="Narrative synthesis generator")
    parser.add_argument("--input-csv", type=str, required=True, help="Input CSV file with qualitative descriptions")
    parser.add_argument("--study-count", type=str, required=True, help="JSON file with study count")
    parser.add_argument("--config", type=str, required=True, help="YAML configuration file for methodology")
    parser.add_argument("--output", type=str, required=True, help="Output Markdown file")
    args = parser.parse_args()
    
    generate_narrative_summary(
        Path(args.input_csv),
        Path(args.study_count),
        Path(args.config),
        Path(args.output)
    )
    print(f"Narrative summary generated: {args.output}")

if __name__ == "__main__":
    main()