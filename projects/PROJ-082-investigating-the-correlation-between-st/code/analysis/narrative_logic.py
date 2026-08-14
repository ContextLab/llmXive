"""
Narrative Logic Implementation for Thematic Aggregation.

This module performs thematic aggregation of qualitative descriptors from
extracted studies, implementing keyword frequency counting and sentiment
  rule mapping as defined in the narrative methodology configuration.
"""
import json
import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sys
import os

# Add project root to path for imports if running as script
if 'code' not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if code_root.name == 'code':
        sys.path.insert(0, str(code_root))

from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

def load_methodology_config(config_path: str) -> Dict[str, Any]:
    """
    Load the narrative methodology configuration file.
    
    Args:
        config_path: Path to the narrative_methodology.yaml file.
        
    Returns:
        Dictionary containing keywords, sentiment_rules, and exclusion_criteria.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the file is not valid YAML/JSON (simplified to JSON for this impl).
    """
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Methodology config not found: {path}")
        raise FileNotFoundError(f"Methodology config not found: {path}")
    
    # Assuming YAML format as per spec, but using standard json for strictness if not yaml installed
    # The spec implies YAML. We will try to read it as text and parse basic structure if yaml is not available,
    # but standard practice in this project likely has PyYAML.
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except ImportError:
        # Fallback for environments without yaml, though requirements.txt should have it
        logger.warning("PyYAML not found, attempting basic parsing or failing.")
        raise ImportError("PyYAML is required to load methodology config.")
        
    return config

def load_extracted_studies(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load the extracted studies CSV file.
    
    Args:
        csv_path: Path to the extracted_studies.csv file.
        
    Returns:
        List of dictionaries representing each study row.
        
    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    path = Path(csv_path)
    if not path.exists():
        logger.error(f"Extracted studies file not found: {path}")
        raise FileNotFoundError(f"Extracted studies file not found: {path}")
    
    studies = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)
    
    logger.info(f"Loaded {len(studies)} studies from {csv_path}")
    return studies

def extract_themes(studies: List[Dict[str, Any]], methodology: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and aggregate themes from qualitative descriptors based on methodology.
    
    Args:
        studies: List of study dictionaries containing 'qualitative_desc'.
        methodology: Configuration dictionary with keywords and sentiment rules.
        
    Returns:
        Dictionary mapping theme names to their counts and associated details.
    """
    theme_counts = defaultdict(int)
    theme_details = defaultdict(list)
    
    keywords = methodology.get('keywords', [])
    sentiment_rules = methodology.get('sentiment_rules', {})
    positive_indicators = sentiment_rules.get('positive', [])
    negative_indicators = sentiment_rules.get('negative', [])
    
    # Compile regex for efficiency
    keyword_patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]
    positive_patterns = [re.compile(re.escape(ind), re.IGNORECASE) for ind in positive_indicators]
    negative_patterns = [re.compile(re.escape(ind), re.IGNORECASE) for ind in negative_indicators]
    
    for study in studies:
        desc = study.get('qualitative_desc', '')
        if not desc or desc == 'no_descriptor_found':
            continue
        
        # Determine sentiment
        sentiment = 'neutral'
        if any(p.search(desc) for p in positive_patterns):
            sentiment = 'positive'
        elif any(p.search(desc) for p in negative_patterns):
            sentiment = 'negative'
        
        # Match keywords to themes
        matched_keywords = []
        for kw, pattern in zip(keywords, keyword_patterns):
            if pattern.search(desc):
                matched_keywords.append(kw)
                # Theme name is the keyword itself or a mapped group if specified
                # For now, we map directly to the keyword
                theme_counts[kw] += 1
                theme_details[kw].append({
                    'author': study.get('author', 'Unknown'),
                    'year': study.get('year', 'N/A'),
                    'sentiment': sentiment,
                    'text_snippet': desc[:100] + '...' if len(desc) > 100 else desc
                })
        
        # If no specific keyword matched but there is text, categorize as 'general'
        if not matched_keywords and desc:
            theme_counts['general'] += 1
            theme_details['general'].append({
                'author': study.get('author', 'Unknown'),
                'year': study.get('year', 'N/A'),
                'sentiment': sentiment,
                'text_snippet': desc[:100] + '...' if len(desc) > 100 else desc
            })
    
    return {
        'themes': dict(theme_counts),
        'details': dict(theme_details)
    }

def generate_themes_json(themes_data: Dict[str, Any], output_path: str) -> None:
    """
    Save the aggregated theme data to a JSON file.
    
    Args:
        themes_data: Dictionary containing themes and details.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'total_studies_processed': sum(themes_data['themes'].values()),
        'theme_counts': themes_data['themes'],
        'theme_details': themes_data['details']
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Narrative themes saved to {output_path}")

def run_narrative_logic(
    extracted_studies_path: str,
    methodology_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Main entry point for running the narrative logic pipeline.
    
    Args:
        extracted_studies_path: Path to the input CSV.
        methodology_path: Path to the methodology YAML config.
        output_path: Path for the output JSON.
        
    Returns:
        The generated themes dictionary.
    """
    logger.info("Starting narrative logic analysis...")
    
    # Load configuration
    methodology = load_methodology_config(methodology_path)
    logger.debug(f"Loaded methodology config: {list(methodology.keys())}")
    
    # Load studies
    studies = load_extracted_studies(extracted_studies_path)
    logger.info(f"Processing {len(studies)} studies for thematic analysis.")
    
    # Extract themes
    themes_data = extract_themes(studies, methodology)
    
    # Save results
    generate_themes_json(themes_data, output_path)
    
    logger.info("Narrative logic analysis completed successfully.")
    return themes_data

def main() -> None:
    """
    Command-line entry point for the narrative logic script.
    """
    project_root = get_project_root()
    
    # Default paths relative to project root
    extracted_studies_path = project_root / "data" / "processed" / "extracted_studies.csv"
    methodology_path = project_root / "data" / "config" / "narrative_methodology.yaml"
    output_path = project_root / "data" / "derived" / "narrative_themes.json"
    
    # Allow overriding via command line args
    if len(sys.argv) > 1:
        extracted_studies_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        methodology_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])
        
    try:
        run_narrative_logic(
            str(extracted_studies_path),
            str(methodology_path),
            str(output_path)
        )
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during narrative logic execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()