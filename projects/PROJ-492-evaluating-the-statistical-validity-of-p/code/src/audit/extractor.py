"""
Extractor module for A/B test summaries.

This module extracts structured data from fetched HTML pages containing
A/B test summaries. It produces ABTestSummary objects, handles missing
fields gracefully, and logs appropriate error codes per FR-007.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup

from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Initialize logger
logger = get_default_logger(__name__)
audit_logger = AuditLogger()

# Regex patterns for extracting numeric values
FLOAT_PATTERN = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
INT_PATTERN = re.compile(r'\d+')

# Common field name variations in HTML
FIELD_VARIATIONS = {
    'baseline_rate': ['baseline_rate', 'control_rate', 'control_conversion', 'control_conversion_rate', 'baseline_conversion', 'baseline'],
    'treatment_rate': ['treatment_rate', 'variant_rate', 'treatment_conversion', 'treatment_conversion_rate', 'variant_conversion', 'variant'],
    'sample_size_baseline': ['sample_size_baseline', 'control_n', 'control_sample_size', 'n_baseline', 'n_control'],
    'sample_size_treatment': ['sample_size_treatment', 'variant_n', 'treatment_sample_size', 'n_treatment', 'n_variant'],
    'p_value': ['p_value', 'p-value', 'pvalue', 'significance', 'p_val'],
    'effect_size': ['effect_size', 'effect-size', 'effectsize', 'lift', 'relative_lift', 'absolute_lift'],
    'domain': ['domain', 'source_domain', 'website', 'url_domain'],
    'publication_year': ['publication_year', 'year', 'pub_year', 'date_year']
}

def extract_single_float(text: str, field_name: str) -> Optional[float]:
    """
    Extract a single float value from text.
    
    Args:
        text: The text to search in
        field_name: Name of the field (for logging)
        
    Returns:
        Float value if found, None otherwise
    """
    if not text:
        return None
    
    match = FLOAT_PATTERN.search(text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            audit_logger.log_warning(f"ERR-002: Failed to parse float for {field_name}: {text}")
            return None
    return None

def extract_single_int(text: str, field_name: str) -> Optional[int]:
    """
    Extract a single integer value from text.
    
    Args:
        text: The text to search in
        field_name: Name of the field (for logging)
        
    Returns:
        Integer value if found, None otherwise
    """
    if not text:
        return None
    
    match = INT_PATTERN.search(text)
    if match:
        try:
            return int(match.group())
        except ValueError:
            audit_logger.log_warning(f"ERR-003: Failed to parse int for {field_name}: {text}")
            return None
    return None

def extract_field_from_html(soup: BeautifulSoup, field_name: str, possible_names: List[str]) -> Optional[str]:
    """
    Extract a field value from HTML by searching for labels.
    
    Args:
        soup: BeautifulSoup object of the HTML
        field_name: Canonical field name
        possible_names: List of possible label variations
        
    Returns:
        Extracted text value or None
    """
    # Search for labels containing any of the possible names
    for label_text in possible_names:
        # Try finding by label text
        labels = soup.find_all(text=re.compile(re.escape(label_text), re.IGNORECASE))
        for label in labels:
            # Get parent element and find associated value
            parent = label.parent
            if parent:
                # Check siblings for value
                for sibling in parent.next_siblings:
                    if sibling and hasattr(sibling, 'strip'):
                        value = sibling.strip()
                        if value and not any(x in value.lower() for x in ['label', 'name', 'field']):
                            return value
                # Check for value in same element
                if parent.get_text(strip=True) and label_text.lower() in parent.get_text(strip=True).lower():
                    # Try to extract value from the same tag
                    text = parent.get_text()
                    # Remove the label text
                    value = text.replace(label, '').strip()
                    if value:
                        return value
    
    # Try finding by common HTML patterns
    # Look for patterns like "Label: Value" or "Label: <span>Value</span>"
    for pattern in FIELD_VARIATIONS.get(field_name, []):
        # Search for text containing the pattern
        for text in soup.find_all(string=re.compile(re.escape(pattern), re.IGNORECASE)):
            # Get the surrounding text
            parent = text.parent
            if parent:
                full_text = parent.get_text(separator=' ', strip=True)
                # Extract value after the pattern
                parts = re.split(re.escape(pattern), full_text, maxsplit=1)
                if len(parts) > 1:
                    value = parts[1].strip().strip(':').strip()
                    if value:
                        return value
    
    return None

def extract_summary_from_html(html_content: str, url: str) -> Optional[ABTestSummary]:
    """
    Extract an A/B test summary from HTML content.
    
    Args:
        html_content: The HTML content to parse
        url: The source URL (for provenance)
        
    Returns:
        ABTestSummary object if extraction succeeds, None otherwise
    """
    if not html_content:
        audit_logger.log_error("ERR-001: Empty HTML content provided")
        return None
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        audit_logger.log_error(f"ERR-004: Failed to parse HTML: {str(e)}")
        return None
    
    # Extract fields
    baseline_rate_str = extract_field_from_html(soup, 'baseline_rate', FIELD_VARIATIONS['baseline_rate'])
    treatment_rate_str = extract_field_from_html(soup, 'treatment_rate', FIELD_VARIATIONS['treatment_rate'])
    sample_size_baseline_str = extract_field_from_html(soup, 'sample_size_baseline', FIELD_VARIATIONS['sample_size_baseline'])
    sample_size_treatment_str = extract_field_from_html(soup, 'sample_size_treatment', FIELD_VARIATIONS['sample_size_treatment'])
    p_value_str = extract_field_from_html(soup, 'p_value', FIELD_VARIATIONS['p_value'])
    effect_size_str = extract_field_from_html(soup, 'effect_size', FIELD_VARIATIONS['effect_size'])
    domain_str = extract_field_from_html(soup, 'domain', FIELD_VARIATIONS['domain'])
    year_str = extract_field_from_html(soup, 'publication_year', FIELD_VARIATIONS['publication_year'])
    
    # Track missing fields
    missing_fields = []
    
    # Parse numeric values
    baseline_rate = extract_single_float(baseline_rate_str, 'baseline_rate') if baseline_rate_str else None
    if baseline_rate is None and baseline_rate_str:
        missing_fields.append('baseline_rate')
    elif baseline_rate is None:
        missing_fields.append('baseline_rate')
    
    treatment_rate = extract_single_float(treatment_rate_str, 'treatment_rate') if treatment_rate_str else None
    if treatment_rate is None and treatment_rate_str:
        missing_fields.append('treatment_rate')
    elif treatment_rate is None:
        missing_fields.append('treatment_rate')
    
    sample_size_baseline = extract_single_int(sample_size_baseline_str, 'sample_size_baseline') if sample_size_baseline_str else None
    if sample_size_baseline is None and sample_size_baseline_str:
        missing_fields.append('sample_size_baseline')
    elif sample_size_baseline is None:
        missing_fields.append('sample_size_baseline')
    
    sample_size_treatment = extract_single_int(sample_size_treatment_str, 'sample_size_treatment') if sample_size_treatment_str else None
    if sample_size_treatment is None and sample_size_treatment_str:
        missing_fields.append('sample_size_treatment')
    elif sample_size_treatment is None:
        missing_fields.append('sample_size_treatment')
    
    p_value = extract_single_float(p_value_str, 'p_value') if p_value_str else None
    if p_value is None and p_value_str:
        missing_fields.append('p_value')
    elif p_value is None:
        missing_fields.append('p_value')
    
    effect_size = extract_single_float(effect_size_str, 'effect_size') if effect_size_str else None
    if effect_size is None and effect_size_str:
        missing_fields.append('effect_size')
    elif effect_size is None:
        missing_fields.append('effect_size')
    
    # Extract domain from URL if not found in HTML
    domain = domain_str
    if not domain:
        try:
            from code.src.utils.helpers import domain_from_url
            domain = domain_from_url(url)
        except Exception:
            domain = 'unknown'
    
    # Extract year
    year = extract_single_int(year_str, 'publication_year') if year_str else None
    if year is None and year_str:
        missing_fields.append('publication_year')
    elif year is None:
        missing_fields.append('publication_year')
    
    # Log missing fields with appropriate error codes
    for field in missing_fields:
        error_code = f"ERR-01{len(missing_fields)}" if len(missing_fields) <= 9 else f"ERR-0{len(missing_fields)}"
        audit_logger.log_warning(f"{error_code}: Missing field '{field}' in extraction from {url}")
    
    # Check for critical missing fields
    if baseline_rate is None or treatment_rate is None:
        audit_logger.log_error("ERR-005: Critical fields (baseline_rate or treatment_rate) missing")
        return None
    
    if sample_size_baseline is None or sample_size_treatment is None:
        audit_logger.log_warning("ERR-006: Sample size fields missing - may affect statistical validity")
    
    if p_value is None:
        audit_logger.log_warning("ERR-007: P-value missing - cannot validate statistical significance")
    
    # Create summary object
    try:
        summary = ABTestSummary(
            url=url,
            domain=domain,
            publication_year=year,
            baseline_rate=baseline_rate,
            treatment_rate=treatment_rate,
            sample_size_baseline=sample_size_baseline,
            sample_size_treatment=sample_size_treatment,
            p_value=p_value,
            effect_size=effect_size,
            extraction_status='complete' if not missing_fields else 'partial',
            missing_fields=missing_fields
        )
        
        logger.info(f"Successfully extracted summary from {url}")
        return summary
        
    except Exception as e:
        audit_logger.log_error(f"ERR-008: Failed to create ABTestSummary object: {str(e)}")
        return None

def extract_all(url_list: List[str], output_dir: Path) -> List[ABTestSummary]:
    """
    Extract summaries from a list of URLs.
    
    Args:
        url_list: List of URLs to extract from
        output_dir: Directory to save extracted summaries
        
    Returns:
        List of extracted ABTestSummary objects
    """
    summaries = []
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for url in url_list:
        logger.info(f"Processing URL: {url}")
        
        # Try to load from cached HTML
        html_path = output_dir.parent / 'raw' / f"{hash(url)}.html"
        if html_path.exists():
            try:
                html_content = html_path.read_text(encoding='utf-8')
            except Exception as e:
                audit_logger.log_error(f"ERR-009: Failed to read cached HTML for {url}: {str(e)}")
                continue
        else:
            # Try alternative path
            html_path = output_dir.parent / 'raw' / f"{url.replace('://', '_').replace('/', '_')}.html"
            if html_path.exists():
                try:
                    html_content = html_path.read_text(encoding='utf-8')
                except Exception as e:
                    audit_logger.log_error(f"ERR-010: Failed to read cached HTML for {url}: {str(e)}")
                    continue
            else:
                audit_logger.log_error(f"ERR-011: No cached HTML found for {url}")
                continue
        
        summary = extract_summary_from_html(html_content, url)
        if summary:
            summaries.append(summary)
    
    return summaries

def write_summaries_to_json(summaries: List[ABTestSummary], output_path: Path) -> None:
    """
    Write extracted summaries to a JSON file.
    
    Args:
        summaries: List of ABTestSummary objects to write
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = [
        {
            'url': s.url,
            'domain': s.domain,
            'publication_year': s.publication_year,
            'baseline_rate': s.baseline_rate,
            'treatment_rate': s.treatment_rate,
            'sample_size_baseline': s.sample_size_baseline,
            'sample_size_treatment': s.sample_size_treatment,
            'p_value': s.p_value,
            'effect_size': s.effect_size,
            'extraction_status': s.extraction_status,
            'missing_fields': s.missing_fields
        }
        for s in summaries
    ]
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Wrote {len(summaries)} summaries to {output_path}")
    except Exception as e:
        audit_logger.log_error(f"ERR-012: Failed to write summaries to JSON: {str(e)}")
        raise

def main() -> int:
    """
    Main entry point for the extractor script.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract A/B test summaries from fetched HTML')
    parser.add_argument('--input-dir', type=Path, default=Path('data/raw'),
                      help='Directory containing fetched HTML files')
    parser.add_argument('--output-file', type=Path, default=Path('data/extracted_summaries.json'),
                      help='Output JSON file for extracted summaries')
    parser.add_argument('--urls-file', type=Path, default=Path('input/urls.csv'),
                      help='CSV file containing URLs to process')
    
    args = parser.parse_args()
    
    # Read URLs
    try:
        import csv
        urls = []
        with open(args.urls_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'url' in row:
                    urls.append(row['url'])
        logger.info(f"Loaded {len(urls)} URLs from {args.urls_file}")
    except Exception as e:
        audit_logger.log_error(f"ERR-013: Failed to read URLs file: {str(e)}")
        return 1
    
    # Extract summaries
    summaries = extract_all(urls, args.input_dir)
    
    if not summaries:
        audit_logger.log_error("ERR-014: No summaries extracted - check HTML files and extraction logic")
        return 1
    
    # Write output
    write_summaries_to_json(summaries, args.output_file)
    
    # Log summary statistics
    complete_count = sum(1 for s in summaries if s.extraction_status == 'complete')
    partial_count = sum(1 for s in summaries if s.extraction_status == 'partial')
    logger.info(f"Extraction complete: {complete_count} complete, {partial_count} partial")
    
    return 0

if __name__ == '__main__':
    exit(main())
