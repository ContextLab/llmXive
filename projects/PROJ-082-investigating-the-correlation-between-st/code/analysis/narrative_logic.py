"""
T015a: Implement narrative logic for thematic aggregation.

Reads extracted studies and methodology config to aggregate qualitative descriptors
by theme and count frequencies. Outputs structured JSON for the narrative engine.
"""
import json
import csv
import re
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from sibling modules as per API surface
from utils.config import get_project_root
from utils.logger import get_logger

logger = get_logger(__name__)


def load_methodology_config(config_path: Path) -> Dict[str, Any]:
    """
    Load the narrative methodology configuration from YAML/JSON.
    
    Expected schema:
    {
        "keywords": ["list", "of", "strings"],
        "sentiment_rules": {
            "positive": ["list"],
            "negative": ["list"]
        },
        "exclusion_criteria": ["list"]
    }
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Methodology config not found at {config_path}")
    
    try:
        # Simple YAML loader without external dependency if possible, 
        # but project has pyyaml in requirements (T002a).
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not found, attempting JSON fallback or raising error")
        raise
    except Exception as e:
        logger.error(f"Failed to load methodology config: {e}")
        raise


def load_extracted_studies(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load the extracted studies CSV produced by T013.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Extracted studies CSV not found at {csv_path}")
    
    studies = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)
    
    logger.info(f"Loaded {len(studies)} studies from {csv_path}")
    return studies


def extract_themes(
    qualitative_desc: str, 
    keywords: List[str], 
    sentiment_rules: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
    """
    Extract themes from a single qualitative description string.
    
    Matches keywords against the text and assigns sentiment based on rules.
    Returns a list of matched theme objects.
    """
    if not qualitative_desc or qualitative_desc.lower() == "nan":
        return []
    
    text_lower = qualitative_desc.lower()
    found_themes = []
    
    # 1. Keyword Matching (Theme Identification)
    for keyword in keywords:
        if keyword.lower() in text_lower:
            # Determine sentiment
            sentiment = "neutral"
            for sent_type, terms in sentiment_rules.items():
                if any(term.lower() in text_lower for term in terms):
                    sentiment = sent_type
                    break
            
            found_themes.append({
                "theme": keyword,
                "sentiment": sentiment,
                "source_text": qualitative_desc
            })
    
    # If no specific keyword found, check for generic "no_descriptor"
    if not found_themes and "no_descriptor" in text_lower:
        found_themes.append({
            "theme": "no_descriptor_found",
            "sentiment": "neutral",
            "source_text": qualitative_desc
        })
        
    return found_themes


def generate_themes_json(
    studies: List[Dict[str, Any]], 
    methodology: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate themes across all studies into a frequency count.
    
    Output structure:
    {
        "timestamp": "...",
        "total_studies_processed": N,
        "themes": {
            "theme_name": {
                "count": X,
                "sentiment_breakdown": {
                    "positive": Y,
                    "negative": Z,
                    "neutral": W
                },
                "examples": ["list of source texts"]
            }
        }
    }
    """
    theme_counts = defaultdict(lambda: {
        "count": 0,
        "sentiment_breakdown": defaultdict(int),
        "examples": []
    })
    
    keywords = methodology.get("keywords", [])
    sentiment_rules = methodology.get("sentiment_rules", {})
    
    for study in studies:
        desc = study.get("qualitative_desc", "")
        themes = extract_themes(desc, keywords, sentiment_rules)
        
        for theme in themes:
            t_name = theme["theme"]
            t_sent = theme["sentiment"]
            
            theme_counts[t_name]["count"] += 1
            theme_counts[t_name]["sentiment_breakdown"][t_sent] += 1
            
            # Keep up to 3 examples per theme
            if len(theme_counts[t_name]["examples"]) < 3:
                theme_counts[t_name]["examples"].append(desc)
    
    # Convert defaultdicts to standard dicts for JSON serialization
    final_themes = {}
    for t_name, data in theme_counts.items():
        final_themes[t_name] = {
            "count": data["count"],
            "sentiment_breakdown": dict(data["sentiment_breakdown"]),
            "examples": data["examples"]
        }
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_studies_processed": len(studies),
        "themes": final_themes
    }


def run_narrative_logic(
    csv_path: Optional[Path] = None,
    config_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point for T015a.
    
    Loads data, processes themes, and writes the JSON output.
    """
    project_root = get_project_root()
    
    # Defaults
    if csv_path is None:
        csv_path = project_root / "data" / "processed" / "extracted_studies.csv"
    if config_path is None:
        config_path = project_root / "data" / "config" / "narrative_methodology.yaml"
    if output_path is None:
        output_path = project_root / "data" / "derived" / "narrative_themes.json"
    
    logger.info(f"Starting narrative logic: CSV={csv_path}, Config={config_path}")
    
    # 1. Load Config
    try:
        methodology = load_methodology_config(config_path)
    except FileNotFoundError as e:
        logger.error(f"Configuration missing: {e}")
        raise
    
    # 2. Load Studies
    try:
        studies = load_extracted_studies(csv_path)
    except FileNotFoundError as e:
        logger.error(f"Input data missing: {e}")
        raise
    
    if not studies:
        logger.warning("No studies found to process. Generating empty theme report.")
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_studies_processed": 0,
            "themes": {}
        }
    else:
        # 3. Process Themes
        result = generate_themes_json(studies, methodology)
    
    # 4. Ensure Output Directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 5. Write Output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Narrative themes written to {output_path}")
    return result


def main():
    """CLI entry point."""
    run_narrative_logic()
    print("Narrative logic completed successfully.")


if __name__ == "__main__":
    main()
