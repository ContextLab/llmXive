"""
Narrative Synthesis Engine (T015b)

Implements the core 'pivot' mechanism and text assembly logic for User Story 1.
Reads `data/derived/narrative_themes.json` and `data/processed/study_count.json`.
If N < 10, generates the structured text content for the narrative review.
Output: `data/derived/narrative_content.md`.
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import logger utility from existing project surface
from utils.logger import get_logger, log_error_context

logger = get_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_THEMES_PATH = PROJECT_ROOT / "data" / "derived" / "narrative_themes.json"
INPUT_COUNT_PATH = PROJECT_ROOT / "data" / "processed" / "study_count.json"
OUTPUT_CONTENT_PATH = PROJECT_ROOT / "data" / "derived" / "narrative_content.md"


def load_study_count_json(path: Path) -> Dict[str, Any]:
    """Load study count JSON. Raises FileNotFoundError if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file missing: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_narrative_themes_json(path: Path) -> Dict[str, Any]:
    """Load narrative themes JSON. Raises FileNotFoundError if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file missing: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_narrative_content(themes_data: Dict[str, Any], count_data: Dict[str, Any]) -> str:
    """
    Generate the structured text content for the narrative review.

    This function implements the pivot logic:
    1. Check N from count_data.
    2. If N < 10 (or N=0), assemble the narrative text based on themes_data.
    3. Return the formatted markdown string.
    """
    n = count_data.get("N", 0)
    
    lines = []
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Header
    lines.append("# Narrative Synthesis Report")
    lines.append("")
    lines.append(f"**Generated**: {timestamp}")
    lines.append(f"**Study Count (N)**: {n}")
    lines.append(f"**Synthesis Mode**: Narrative (Quantitative meta-analysis not applicable due to N < 10)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Overview
    lines.append("## 1. Overview")
    lines.append("")
    if n == 0:
        lines.append("No studies were found in the input dataset. A quantitative meta-analysis could not be performed.")
        lines.append("The following sections reflect the absence of data.")
    else:
        lines.append(f"This report synthesizes findings from **{n}** study(ies).")
        lines.append("Due to the limited number of studies (N < 10), a random-effects meta-analysis was skipped.")
        lines.append("Instead, a qualitative narrative synthesis was performed based on extracted descriptors and themes.")
    lines.append("")

    # Section 2: Themes
    lines.append("## 2. Qualitative Themes")
    lines.append("")
    
    themes = themes_data.get("themes", [])
    if not themes:
        lines.append("No specific themes were identified in the extracted data.")
        lines.append("This may indicate a lack of consistent terminology across studies or empty qualitative descriptors.")
    else:
        lines.append("The following themes were identified through thematic coding of the extracted study descriptors:")
        lines.append("")
        
        # Sort themes by frequency (descending) for better readability
        sorted_themes = sorted(themes, key=lambda x: x.get("count", 0), reverse=True)
        
        for idx, theme in enumerate(sorted_themes, 1):
            theme_name = theme.get("name", "Unknown Theme")
            theme_count = theme.get("count", 0)
            theme_desc = theme.get("description", "No description available.")
            related_tracts = theme.get("tracts", [])
            
            lines.append(f"### {idx}. {theme_name}")
            lines.append("")
            lines.append(f"- **Frequency**: {theme_count} study(ies)")
            if related_tracts:
                tracts_str = ", ".join(related_tracts)
                lines.append(f"- **Associated Tracts**: {tracts_str}")
            lines.append(f"- **Description**: {theme_desc}")
            lines.append("")

    # Section 3: Limitations
    lines.append("## 3. Limitations")
    lines.append("")
    lines.append("This synthesis is subject to the following limitations:")
    lines.append("")
    lines.append(f"1. **Sample Size**: The analysis is based on {n} study(ies), which is below the threshold (N=10) required for robust quantitative meta-analysis.")
    lines.append("2. **Statistical Power**: Heterogeneity (I²) and publication bias (Egger's test) could not be calculated reliably.")
    lines.append("3. **Data Availability**: Many studies lacked quantitative effect sizes (r, n), necessitating reliance on qualitative descriptors.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*End of Narrative Synthesis Report*")

    return "\n".join(lines)


def run_narrative_engine() -> bool:
    """
    Main entry point for the Narrative Engine.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Starting Narrative Synthesis Engine (T015b)...")
        
        # 1. Load Inputs
        logger.info(f"Loading study count from {INPUT_COUNT_PATH}...")
        count_data = load_study_count_json(INPUT_COUNT_PATH)
        logger.info(f"Loaded count: N={count_data.get('N')}")

        logger.info(f"Loading narrative themes from {INPUT_THEMES_PATH}...")
        themes_data = load_narrative_themes_json(INPUT_THEMES_PATH)
        logger.info("Loaded themes successfully.")

        # 2. Pivot Logic Check
        n = count_data.get("N", 0)
        if n >= 10:
            logger.warning(f"N={n} is >= 10. Narrative synthesis is not the primary path, but generating content as requested.")
        
        # 3. Generate Content
        logger.info("Generating narrative content...")
        content = generate_narrative_content(themes_data, count_data)

        # 4. Write Output
        logger.info(f"Writing output to {OUTPUT_CONTENT_PATH}...")
        OUTPUT_CONTENT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_CONTENT_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Successfully generated {OUTPUT_CONTENT_PATH}")
        return True

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in narrative engine: {e}")
        return False


def main() -> None:
    """CLI entry point."""
    success = run_narrative_engine()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()