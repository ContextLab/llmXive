import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger

def load_candidate_sources(file_path: str) -> list:
    """Load the raw candidate sources list from T008a-Query."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Candidate sources file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("Candidate sources file must contain a JSON list.")
    
    return data

def format_sources(sources: list) -> list:
    """
    Format the candidate sources into a standardized structure for T008b.
    
    This ensures all required fields are present and normalized.
    """
    formatted = []
    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            logging.warning(f"Skipping non-dict entry at index {i}")
            continue
        
        formatted_source = {
            "url": source.get("url", ""),
            "source_type": source.get("source_type", "unknown"),
            "citation": source.get("citation", ""),
            "metadata": source.get("metadata", {})
        }
        
        # Validate URL
        if not formatted_source["url"].startswith(('http://', 'https://')):
            logging.warning(f"Invalid URL at index {i}: {formatted_source['url']}")
            continue
        
        formatted.append(formatted_source)
    
    return formatted

def main():
    """Main entry point for T008a-Format."""
    logger = get_logger(__name__)
    
    project_root = Path(__file__).resolve().parent.parent.parent
    input_file = project_root / "data" / "config" / "candidate_sources.txt"
    output_file = project_root / "data" / "config" / "candidate_sources_formatted.json"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        print(f"Error: Input file {input_file} not found. Please run T008a-Query first.")
        sys.exit(1)
    
    try:
        raw_sources = load_candidate_sources(str(input_file))
        logger.info(f"Loaded {len(raw_sources)} candidate sources.")
        
        formatted_sources = format_sources(raw_sources)
        logger.info(f"Formatted {len(formatted_sources)} sources.")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_sources, f, indent=2)
        
        logger.info(f"Formatted sources saved to {output_file}")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error formatting sources: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
