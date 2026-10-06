"""
Research file verification module.
Validates research.md for static URLs/IDs and absence of dynamic search logic.
"""
import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Import from sibling modules as per API surface
from logging_config import get_logger, raise_on_missing_data

# Constants
RESEARCH_FILE_PATH = Path("specs/001-predict-lst-wear/research.md")
OUTPUT_FILE_PATH = Path("state/research_validation.json")

# Patterns to detect dynamic search logic
DYNAMIC_SEARCH_PATTERNS = [
    r"search\s*\(.*\)",
    r"query\s*\(.*\)",
    r"find\s*\(.*\)",
    r"browse\s*\(.*\)",
    r"lookup\s*\(.*\)",
    r"api\.search",
    r"engine\.search",
    r"dynamic.*url",
    r"runtime.*lookup",
    r"on-the-fly.*fetch",
]

# Patterns to detect static URLs/IDs
STATIC_URL_PATTERNS = [
    r"https?://[^\s]+",  # HTTP/HTTPS URLs
    r"dataset_id\s*[:=]\s*['\"][^'\"]+['\"]",  # dataset_id assignments
    r"openml_id\s*[:=]\s*['\"][^'\"]+['\"]",  # OpenML specific
    r"hf_dataset\s*[:=]\s*['\"][^'\"]+['\"]",  # HuggingFace specific
]

def setup_logging():
    """Configure logging for the verification process."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "research_validation.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return get_logger(__name__)

def parse_research_md(file_path: Path) -> Dict[str, Any]:
    """
    Parse research.md file and extract structured data.
    
    Args:
        file_path: Path to the research.md file
        
    Returns:
        Dictionary containing parsed content and metadata
    """
    logger = logging.getLogger(__name__)
    
    if not file_path.exists():
        logger.error(f"Research file not found: {file_path}")
        raise FileNotFoundError(f"Research file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract sections
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if line.startswith('### '):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line[4:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return {
        'raw_content': content,
        'sections': sections,
        'file_path': str(file_path),
        'file_size': len(content)
    }

def check_static_urls(content: str) -> Tuple[bool, List[str], List[str]]:
    """
    Check if content contains only static URLs/IDs and no dynamic search logic.
    
    Args:
        content: Text content to analyze
        
    Returns:
        Tuple of (is_valid, static_urls_found, dynamic_patterns_found)
    """
    logger = logging.getLogger(__name__)
    static_urls = []
    dynamic_patterns = []
    
    # Check for dynamic search logic
    for pattern in DYNAMIC_SEARCH_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            dynamic_patterns.extend(matches)
            logger.warning(f"Dynamic search pattern detected: {pattern}")
    
    # Check for static URLs/IDs
    for pattern in STATIC_URL_PATTERNS:
        matches = re.findall(pattern, content)
        static_urls.extend(matches)
    
    is_valid = len(dynamic_patterns) == 0 and len(static_urls) > 0
    
    if not is_valid:
        if len(dynamic_patterns) > 0:
            logger.error(f"Dynamic search logic detected: {dynamic_patterns}")
        if len(static_urls) == 0:
            logger.error("No static URLs/IDs found in research.md")
    
    return is_valid, static_urls, dynamic_patterns

def validate_research_file(file_path: Path = RESEARCH_FILE_PATH) -> Dict[str, Any]:
    """
    Validate the research.md file for compliance with Constitution II.
    
    Args:
        file_path: Path to research.md file
        
    Returns:
        Validation results dictionary
    """
    logger = setup_logging()
    logger.info(f"Starting validation of research file: {file_path}")
    
    try:
        # Parse the file
        parsed_data = parse_research_md(file_path)
        
        # Check for static URLs and dynamic patterns
        is_valid, static_urls, dynamic_patterns = check_static_urls(
            parsed_data['raw_content']
        )
        
        # Compile results
        results = {
            'file_path': str(file_path),
            'validation_passed': is_valid,
            'static_urls_count': len(static_urls),
            'static_urls': static_urls[:10],  # Limit to first 10 for brevity
            'dynamic_patterns_found': len(dynamic_patterns),
            'dynamic_patterns': dynamic_patterns,
            'sections_found': list(parsed_data['sections'].keys()),
            'file_size': parsed_data['file_size'],
            'timestamp': str(Path(file_path).stat().st_mtime),
            'validation_details': {
                'has_static_urls': len(static_urls) > 0,
                'has_dynamic_logic': len(dynamic_patterns) > 0,
                'meets_constitution_ii': is_valid
            }
        }
        
        # Log results
        if is_valid:
            logger.info("✓ Validation PASSED: Research file contains only static URLs/IDs")
            logger.info(f"  Found {len(static_urls)} static URLs/IDs")
        else:
            logger.error("✗ Validation FAILED: Research file contains dynamic search logic")
            logger.error(f"  Found {len(dynamic_patterns)} dynamic patterns")
        
        return results
        
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        raise

def save_validation_results(results: Dict[str, Any], output_path: Path = OUTPUT_FILE_PATH):
    """
    Save validation results to JSON file.
    
    Args:
        results: Validation results dictionary
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logging.getLogger(__name__).info(f"Validation results saved to: {output_path}")

def main():
    """Main entry point for research validation."""
    logger = setup_logging()
    logger.info("=== Research File Validation (T039a) ===")
    
    try:
        # Validate the research file
        results = validate_research_file()
        
        # Save results
        save_validation_results(results)
        
        # Exit with appropriate code
        if results['validation_passed']:
            logger.info("Validation successful - proceeding to T010")
            sys.exit(0)
        else:
            logger.error("Validation failed - cannot proceed to T010")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
