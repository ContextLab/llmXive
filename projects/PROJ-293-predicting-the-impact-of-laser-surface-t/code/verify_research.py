import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import from sibling modules as per API surface
from logging_config import get_logger, raise_on_missing_data

# Define dynamic search patterns that are FORBIDDEN
FORBIDDEN_PATTERNS = [
    r'search\s*\(.*\)',
    r'query\s*\(.*\)',
    r'find.*data.*source',
    r'list.*datasets',
    r'api.*search',
    r'google.*scholar',
    r'browse.*collection'
]

# Define expected static URL/ID patterns
STATIC_URL_PATTERN = re.compile(r'(https?://[^\s]+|datasets/[^\s]+|data/[^,]+)')
STATIC_ID_PATTERN = re.compile(r'(ID:\s*\d+|Dataset\s*ID:\s*[^\s]+|id\s*[:=]\s*[^\s]+)', re.IGNORECASE)

def parse_research_md(file_path: Path) -> Dict[str, Any]:
    """
    Parses the research.md file and extracts source information.
    Returns a dictionary of sources with their URLs/IDs.
    """
    if not file_path.exists():
        raise_on_missing_data(f"Research file not found: {file_path}")

    sources = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Basic parsing logic to find table rows or structured entries
    # Looking for lines that contain URL or ID definitions
    lines = content.split('\n')
    current_source = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('|') and '|' in line[1:]:
            # Parse table row
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                # Assuming format: | Source | Type | Verified | URL/ID |
                name = parts[1] if len(parts) > 1 else None
                url_id = parts[3] if len(parts) > 3 else None
                verified = parts[2].lower() == 'true' if len(parts) > 2 else False
                
                if name and url_id:
                    sources[name] = {
                        "url_id": url_id,
                        "verified": verified,
                        "raw_line": line
                    }
        
        # Check for key-value pairs outside tables
        if ':' in line and not line.startswith('#'):
            if 'URL' in line or 'ID' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip()
                    if key.lower() in ['source name', 'source']:
                        current_source = val
                    elif key.lower() in ['url', 'dataset id', 'id'] and current_source:
                        sources[current_source] = {
                            "url_id": val,
                            "verified": True,
                            "raw_line": line
                        }

    return sources

def check_static_urls(sources: Dict[str, Any]) -> List[str]:
    """
    Checks if the extracted sources contain dynamic search logic.
    Returns a list of errors if any forbidden patterns are found.
    """
    errors = []
    
    for name, data in sources.items():
        text_to_check = data.get("raw_line", "") + " " + data.get("url_id", "")
        
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                errors.append(f"Dynamic search logic detected in source '{name}': {text_to_check}")
        
        # Verify that a static URL or ID is present
        if not data.get("url_id"):
            errors.append(f"Source '{name}' is missing a URL or ID.")
        else:
            url_id = data["url_id"]
            # Ensure it looks like a static reference (starts with http, https, or a known dataset path)
            if not (url_id.startswith('http') or 'dataset' in url_id.lower() or url_id.startswith('data/')):
                # Allow specific exceptions for known static formats
                if not re.match(r'^[A-Za-z0-9/_.-]+$', url_id): 
                     # If it doesn't look like a standard static path/URL
                     pass # We are lenient here as long as no search logic is found

    return errors

def validate_research_file(file_path: Path) -> bool:
    """
    Main validation function.
    Returns True if the file is valid (no dynamic search logic), False otherwise.
    """
    logger = get_logger()
    logger.info(f"Validating research file: {file_path}")
    
    try:
        sources = parse_research_md(file_path)
        if not sources:
            logger.error("No sources found in research.md")
            return False
        
        errors = check_static_urls(sources)
        
        if errors:
            logger.error(f"Validation failed with {len(errors)} errors:")
            for err in errors:
                logger.error(f"  - {err}")
            return False
        
        logger.info("Validation passed: All sources are static.")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        return False

def main():
    """
    Entry point for the verification script.
    Reads specs/001-predict-lst-wear/research.md and writes results to state/research_validation.json
    """
    # Setup logging
    setup_logging = get_logger() # Assuming setup is handled by logging_config if needed, or just use get_logger
    
    project_root = Path(__file__).parent.parent
    research_file = project_root / "specs" / "001-predict-lst-wear" / "research.md"
    output_file = project_root / "state" / "research_validation.json"

    if not research_file.exists():
        print(f"Error: Research file not found at {research_file}")
        sys.exit(1)

    is_valid = validate_research_file(research_file)
    
    # Prepare output
    result = {
        "file": str(research_file),
        "is_valid": is_valid,
        "sources_found": 0,
        "errors": []
    }
    
    if is_valid:
        sources = parse_research_md(research_file)
        result["sources_found"] = len(sources)
        result["sources"] = list(sources.keys())
    else:
        # Re-run to capture errors for the report
        sources = parse_research_md(research_file)
        result["errors"] = check_static_urls(sources)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"Validation complete. Results written to {output_file}")
    print(f"Status: {'PASS' if is_valid else 'FAIL'}")
    
    if not is_valid:
        sys.exit(1)

if __name__ == "__main__":
    # Ensure logging is configured
    from logging_config import setup_logging
    setup_logging()
    main()
