"""
Narrative Logic Module (T015a)

Implements thematic aggregation of qualitative study descriptors.
Reads extracted studies and methodology config to generate theme counts.
"""
import json
import csv
import re
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_project_root
from utils.logger import get_logger

logger = get_logger(__name__)

def load_methodology_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the narrative methodology configuration."""
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / "data" / "config" / "narrative_methodology.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Methodology config not found at {config_path}")
    
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_extracted_studies(csv_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the extracted studies CSV."""
    if csv_path is None:
        project_root = get_project_root()
        csv_path = project_root / "data" / "processed" / "extracted_studies.csv"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Extracted studies CSV not found at {csv_path}")
    
    studies = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)
    
    return studies

def extract_themes(studies: List[Dict[str, Any]], methodology: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract themes from qualitative descriptions based on the methodology.
    
    Uses keyword frequency counting and sentiment rule mapping.
    """
    theme_counts = defaultdict(int)
    keywords = methodology.get('keywords', [])
    sentiment_rules = methodology.get('sentiment_rules', {})
    
    for study in studies:
        desc = study.get('qualitative_desc', '')
        if not desc or desc == 'no_descriptor_found':
            continue
        
        desc_lower = desc.lower()
        
        # Keyword frequency counting
        for keyword in keywords:
            if keyword.lower() in desc_lower:
                theme_counts[keyword] += 1
        
        # Sentiment mapping
        for sentiment, terms in sentiment_rules.items():
            for term in terms:
                if term.lower() in desc_lower:
                    theme_counts[f"{sentiment}_sentiment"] += 1
                    break
    
    return dict(theme_counts)

def generate_themes_json(theme_counts: Dict[str, int], output_path: Optional[Path] = None) -> Path:
    """Generate the narrative themes JSON output."""
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "derived" / "narrative_themes.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "theme_counts": theme_counts,
        "total_themes_identified": len(theme_counts)
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Narrative themes JSON written to {output_path}")
    return output_path

def run_narrative_logic(
    csv_path: Optional[Path] = None,
    config_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point for the narrative logic task.
    
    Reads extracted studies and methodology config, extracts themes,
    and writes the narrative_themes.json output.
    """
    try:
        logger.info("Starting narrative logic execution...")
        
        # Load inputs
        methodology = load_methodology_config(config_path)
        studies = load_extracted_studies(csv_path)
        
        logger.info(f"Loaded {len(studies)} studies for narrative analysis")
        
        # Extract themes
        theme_counts = extract_themes(studies, methodology)
        
        logger.info(f"Extracted {len(theme_counts)} unique themes")
        
        # Generate output
        output_file = generate_themes_json(theme_counts, output_path)
        
        return {
            "status": "completed",
            "output_path": str(output_file),
            "themes_found": len(theme_counts),
            "studies_processed": len(studies)
        }
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during narrative logic execution: {e}")
        raise

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run narrative theme extraction')
    parser.add_argument('--csv', type=str, help='Path to extracted studies CSV')
    parser.add_argument('--config', type=str, help='Path to methodology config YAML')
    parser.add_argument('--output', type=str, help='Path to output JSON')
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv) if args.csv else None
    config_path = Path(args.config) if args.config else None
    output_path = Path(args.output) if args.output else None
    
    result = run_narrative_logic(csv_path, config_path, output_path)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
