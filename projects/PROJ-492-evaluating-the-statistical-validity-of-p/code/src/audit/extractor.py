"""
Extraction logic for A/B test summaries from fetched HTML content.

Produces ABTestSummary objects, handles missing fields gracefully,
and logs specific error codes (ERR-001 to ERR-099) per FR-007.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from bs4 import BeautifulSoup

from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message


def extract_single_float(html_content: str, patterns: List[str], field_name: str, logger: AuditLogger) -> Optional[float]:
    """
    Extract a single float value from HTML using a list of regex patterns.
    Returns None if not found and logs ERR-001.
    """
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                value_str = match.group(1)
                # Clean up common formatting issues (commas, percent signs)
                value_str = value_str.replace(',', '').replace('%', '').strip()
                return float(value_str)
            except ValueError:
                logger.error(f"ERR-002: Failed to parse float value '{match.group(1)}' for {field_name}")
                return None

    logger.error(f"ERR-001: Missing field '{field_name}' in HTML content")
    return None


def extract_single_int(html_content: str, patterns: List[str], field_name: str, logger: AuditLogger) -> Optional[int]:
    """
    Extract a single integer value from HTML using a list of regex patterns.
    Returns None if not found and logs ERR-003.
    """
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                return int(match.group(1).replace(',', '').strip())
            except ValueError:
                logger.error(f"ERR-004: Failed to parse int value '{match.group(1)}' for {field_name}")
                return None

    logger.error(f"ERR-003: Missing field '{field_name}' in HTML content")
    return None


def extract_field_from_html(soup: BeautifulSoup, field_name: str, selectors: List[str]) -> Optional[str]:
    """
    Extract a text field from HTML using CSS selectors.
    Returns None if not found and logs ERR-005.
    """
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            if text:
                return text
    
    # Log specific error if field is critical, otherwise generic
    logger = get_default_logger()
    logger.error(f"ERR-005: Missing field '{field_name}' in HTML content (selectors: {selectors})")
    return None


def extract_summary_from_html(url: str, html_content: str, logger: AuditLogger) -> Optional[ABTestSummary]:
    """
    Extract a complete ABTestSummary from HTML content.
    Handles missing fields by setting them to None and logging appropriate errors.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Define patterns for common metric extractions
    # These patterns are designed to match common A/B test reporting formats
    
    # P-value patterns (various formats)
    p_value_patterns = [
        r'p\s*[=:]\s*([0-9.]+)',
        r'p-value\s*[=:]\s*([0-9.]+)',
        r'p\s*=\s*([0-9.]+)',
        r'<\s*([0-9.]+)\s*\(p\s*<\s*([0-9.]+)\)',
        r'p\s*[<>=]\s*([0-9.]+)',
    ]
    
    # Effect size patterns
    effect_size_patterns = [
        r'effect\s*size\s*[=:]\s*([0-9.-]+)',
        r'lift\s*[=:]\s*([0-9.-]+)',
        r'difference\s*[=:]\s*([0-9.-]+)',
        r'([0-9.-]+)\s*%\s*lift',
        r'([0-9.-]+)\s*%\s*difference',
    ]
    
    # Sample size patterns (control and treatment)
    n_control_patterns = [
        r'n\s*control\s*[=:]\s*([0-9,]+)',
        r'control\s*n\s*[=:]\s*([0-9,]+)',
        r'sample\s*size\s*control\s*[=:]\s*([0-9,]+)',
        r'([0-9,]+)\s*control',
    ]
    
    n_treatment_patterns = [
        r'n\s*treatment\s*[=:]\s*([0-9,]+)',
        r'treatment\s*n\s*[=:]\s*([0-9,]+)',
        r'sample\s*size\s*treatment\s*[=:]\s*([0-9,]+)',
        r'([0-9,]+)\s*treatment',
    ]
    
    # Conversion rate patterns
    conversion_rate_patterns = [
        r'conversion\s*rate\s*[=:]\s*([0-9.]+)',
        r'baseline\s*rate\s*[=:]\s*([0-9.]+)',
        r'control\s*rate\s*[=:]\s*([0-9.]+)',
    ]
    
    # Try to extract all fields
    p_value = extract_single_float(html_content, p_value_patterns, "p-value", logger)
    effect_size = extract_single_float(html_content, effect_size_patterns, "effect_size", logger)
    n_control = extract_single_int(html_content, n_control_patterns, "n_control", logger)
    n_treatment = extract_single_int(html_content, n_treatment_patterns, "n_treatment", logger)
    conversion_rate = extract_single_float(html_content, conversion_rate_patterns, "conversion_rate", logger)
    
    # Extract domain from URL
    domain = url.split('/')[2] if len(url.split('/')) > 2 else "unknown"
    
    # Extract title if available
    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else "Unknown"
    
    # Create summary object with extracted values
    summary = ABTestSummary(
        url=url,
        domain=domain,
        title=title,
        p_value=p_value,
        effect_size=effect_size,
        n_control=n_control,
        n_treatment=n_treatment,
        conversion_rate=conversion_rate,
        extraction_timestamp=None,  # Will be set by caller
        raw_html_hash=None  # Will be set by caller
    )
    
    return summary


def extract_all(url_list: List[str], html_files_dir: Path, output_dir: Path, logger: AuditLogger) -> List[ABTestSummary]:
    """
    Extract summaries from all fetched HTML files.
    Returns a list of ABTestSummary objects.
    """
    summaries = []
    
    for url in url_list:
        # Generate filename from URL hash
        url_hash = abs(hash(url)) % (10 ** 8)
        html_file = html_files_dir / f"{url_hash}.html"
        
        if not html_file.exists():
            logger.error(f"ERR-006: HTML file not found for URL {url}")
            continue
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            summary = extract_summary_from_html(url, html_content, logger)
            if summary:
                summaries.append(summary)
            else:
                logger.error(f"ERR-007: Failed to extract summary from {url}")
                
        except Exception as e:
            logger.error(f"ERR-008: Error processing {url}: {str(e)}")
            continue
    
    return summaries


def write_summaries_to_json(summaries: List[ABTestSummary], output_path: Path, logger: AuditLogger) -> bool:
    """
    Write extracted summaries to a JSON file.
    Returns True on success, False on failure.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert ABTestSummary objects to dictionaries
        summary_dicts = [summary.model_dump() for summary in summaries]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary_dicts, f, indent=2, default=str)
        
        logger.info(f"Successfully wrote {len(summaries)} summaries to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"ERR-009: Failed to write summaries to {output_path}: {str(e)}")
        return False


def main():
    """
    Main entry point for the extractor module.
    Reads from data/raw/ and writes to data/extracted/.
    """
    logger = get_default_logger()
    logger.info("Starting extraction process...")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent.parent
    html_files_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "extracted"
    output_file = output_dir / "extracted_summaries.json"
    
    # Check if raw directory exists and has files
    if not html_files_dir.exists():
        logger.error("ERR-010: Raw HTML directory not found. Run fetcher first.")
        return 1
    
    html_files = list(html_files_dir.glob("*.html"))
    if not html_files:
        logger.error("ERR-011: No HTML files found in raw directory.")
        return 1
    
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    # Load URLs from input (we need to map back to URLs)
    # For simplicity, we'll read from a manifest or assume filenames match
    # In a real implementation, we'd use the provenance log from T020c
    
    # Extract summaries
    summaries = []
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Try to extract URL from filename or content
            # This is a simplified approach - in production, use provenance log
            url = f"file://{html_file.name}"  # Placeholder
            summary = extract_summary_from_html(url, html_content, logger)
            if summary:
                summaries.append(summary)
        except Exception as e:
            logger.error(f"ERR-012: Error processing {html_file}: {str(e)}")
            continue
    
    # Write results
    if summaries:
        success = write_summaries_to_json(summaries, output_file, logger)
        if success:
            logger.info("Extraction completed successfully")
            return 0
        else:
            logger.error("Extraction failed to write output")
            return 1
    else:
        logger.error("ERR-013: No summaries extracted from any files")
        return 1


if __name__ == "__main__":
    exit(main())
