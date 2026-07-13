"""
Extractor module for A/B test summaries.
Extracts metrics from fetched HTML files and produces ABTestSummary objects.
"""
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup

from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.utils.helpers import safe_float, parse_inequality_p

logger = get_default_logger(__name__)
audit_logger = AuditLogger()


def extract_single_float(text: Optional[str], field_name: str) -> Optional[float]:
    """
    Extract a single float value from text.
    Handles various formats like '0.05', '5%', '<0.001', '>0.1'.
    Returns None if extraction fails.
    """
    if text is None or text.strip() == "":
        audit_logger.log_warning(f"Missing {field_name} in source text")
        return None

    text = text.strip()

    # Handle inequality p-values
    if text.startswith('<') or text.startswith('>'):
        return parse_inequality_p(text)

    # Remove percentage signs and convert
    if '%' in text:
        text = text.replace('%', '')
        try:
            val = float(text) / 100.0
            return val
        except ValueError:
            audit_logger.log_error("ERR-002", f"Invalid percentage format for {field_name}: {text}")
            return None

    # Standard float extraction
    try:
        return float(text)
    except ValueError:
        # Try to extract number from text like "p = 0.05"
        match = re.search(r'[\d.]+', text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                audit_logger.log_error("ERR-003", f"Failed to parse {field_name} from: {text}")
                return None

        audit_logger.log_error("ERR-003", f"Failed to parse {field_name} from: {text}")
        return None


def extract_single_int(text: Optional[str], field_name: str) -> Optional[int]:
    """
    Extract a single integer value from text.
    Returns None if extraction fails.
    """
    if text is None or text.strip() == "":
        audit_logger.log_warning(f"Missing {field_name} in source text")
        return None

    text = text.strip()

    # Remove common non-numeric characters
    text = re.sub(r'[,\s]', '', text)

    try:
        return int(float(text))  # Handle "100.0" style
    except ValueError:
        # Try to extract first number from text
        match = re.search(r'\d+', text)
        if match:
            try:
                return int(match.group())
            except ValueError:
                audit_logger.log_error("ERR-004", f"Failed to parse {field_name} from: {text}")
                return None

        audit_logger.log_error("ERR-004", f"Failed to parse {field_name} from: {text}")
        return None


def extract_field_from_html(soup: BeautifulSoup, selectors: List[str], field_name: str) -> Optional[str]:
    """
    Extract text from HTML using a list of CSS selectors.
    Returns the first non-empty match.
    """
    for selector in selectors:
        try:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Selector {selector} failed for {field_name}: {e}")
            continue

    audit_logger.log_error("ERR-001", f"Failed to extract {field_name} from HTML using selectors: {selectors}")
    return None


def extract_summary_from_html(html_path: Path, url: str) -> Optional[ABTestSummary]:
    """
    Extract A/B test summary from a single HTML file.
    Returns ABTestSummary object or None if extraction fails completely.
    """
    try:
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    except Exception as e:
        audit_logger.log_error("ERR-005", f"Failed to read HTML file {html_path}: {e}")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')

    # Define selectors for common patterns
    selectors_map = {
        'baseline_rate': [
            'span[data-testid="baseline-rate"]',
            'td.baseline-rate',
            '.baseline-rate',
            '[class*="baseline"]',
            'td:contains("Control")',
            'td:contains("Baseline")',
        ],
        'treatment_rate': [
            'span[data-testid="treatment-rate"]',
            'td.treatment-rate',
            '.treatment-rate',
            '[class*="treatment"]',
            'td:contains("Variant")',
            'td:contains("Treatment")',
        ],
        'sample_size_control': [
            'span[data-testid="control-n"]',
            'td.control-n',
            '.control-n',
            '[class*="control"]',
            'td:contains("Control") ~ td',
        ],
        'sample_size_treatment': [
            'span[data-testid="treatment-n"]',
            'td.treatment-n',
            '.treatment-n',
            '[class*="treatment"]',
            'td:contains("Variant") ~ td',
        ],
        'p_value': [
            'span[data-testid="p-value"]',
            'td.p-value',
            '.p-value',
            '[class*="p-value"]',
            'td:contains("p-value")',
            'td:contains("p=")',
            'td:contains("P-value")',
        ],
        'effect_size': [
            'span[data-testid="effect-size"]',
            'td.effect-size',
            '.effect-size',
            '[class*="effect"]',
            'td:contains("Effect")',
        ],
        'confidence_interval': [
            'span[data-testid="ci"]',
            'td.ci',
            '.ci',
            '[class*="confidence"]',
            'td:contains("CI")',
        ],
        'test_type': [
            'span[data-testid="test-type"]',
            'td.test-type',
            '.test-type',
            '[class*="test"]',
            'td:contains("Test")',
        ],
        'domain': [
            'meta[name="domain"]',
            'meta[property="og:domain"]',
            'span.domain',
            '.domain',
        ],
        'publication_year': [
            'meta[name="year"]',
            'meta[property="article:published_time"]',
            'span.year',
            '.year',
            'time',
        ],
    }

    # Extract fields
    raw_data = {}
    for field, selectors in selectors_map.items():
        raw_data[field] = extract_field_from_html(soup, selectors, field)

    # Convert to typed values
    baseline_rate = extract_single_float(raw_data.get('baseline_rate'), 'baseline_rate')
    treatment_rate = extract_single_float(raw_data.get('treatment_rate'), 'treatment_rate')
    sample_size_control = extract_single_int(raw_data.get('sample_size_control'), 'sample_size_control')
    sample_size_treatment = extract_single_int(raw_data.get('sample_size_treatment'), 'sample_size_treatment')
    p_value = extract_single_float(raw_data.get('p_value'), 'p_value')
    effect_size = extract_single_float(raw_data.get('effect_size'), 'effect_size')

    # Infer domain from URL if not found in HTML
    domain = raw_data.get('domain')
    if not domain:
        from code.src.utils.helpers import domain_from_url
        domain = domain_from_url(url)
        if domain:
            logger.info(f"Inferred domain '{domain}' from URL for {html_path}")

    # Infer publication year
    pub_year = extract_single_int(raw_data.get('publication_year'), 'publication_year')

    # Create summary object
    try:
        summary = ABTestSummary(
            url=url,
            domain=domain,
            baseline_rate=baseline_rate,
            treatment_rate=treatment_rate,
            sample_size_control=sample_size_control,
            sample_size_treatment=sample_size_treatment,
            p_value=p_value,
            effect_size=effect_size,
          confidence_interval=raw_data.get('confidence_interval'),
            test_type=raw_data.get('test_type'),
            publication_year=pub_year,
            raw_html_path=str(html_path),
            extraction_timestamp=None,  # Will be set by caller
        )
        return summary
    except Exception as e:
        audit_logger.log_error("ERR-006", f"Failed to create ABTestSummary from extracted data: {e}")
        return None


def extract_all(input_dir: Path, output_path: Path) -> List[ABTestSummary]:
    """
    Extract summaries from all HTML files in input directory.
    Writes results to output JSON file.
    """
    summaries = []
    html_files = list(input_dir.glob('*.html'))

    if not html_files:
        audit_logger.log_warning(f"No HTML files found in {input_dir}")
        # Create empty output file
        with open(output_path, 'w') as f:
            json.dump([], f, indent=2)
        return summaries

    logger.info(f"Found {len(html_files)} HTML files to process")

    for html_file in html_files:
        # Extract URL from filename (assuming format: {url_hash}.html or similar)
        url = html_file.stem  # Fallback if no URL in filename
        # Try to find URL in metadata or filename pattern
        if '_' in html_file.name:
            # Assume format: domain_url_hash.html or similar
            parts = html_file.stem.split('_')
            if len(parts) >= 2:
                url = parts[1]  # Take second part as URL

        summary = extract_summary_from_html(html_file, url)
        if summary:
            summary.extraction_timestamp = datetime.now().isoformat()
            summaries.append(summary)
            logger.info(f"Successfully extracted summary from {html_file.name}")
        else:
            logger.warning(f"Failed to extract summary from {html_file.name}")

    # Write to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([s.model_dump() for s in summaries], f, indent=2)

    logger.info(f"Wrote {len(summaries)} summaries to {output_path}")
    return summaries


def write_summaries_to_json(summaries: List[ABTestSummary], output_path: Path) -> None:
    """
    Write a list of ABTestSummary objects to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([s.model_dump() for s in summaries], f, indent=2)
    logger.info(f"Wrote {len(summaries)} summaries to {output_path}")


def main():
    """
    Entry point for extractor script.
    Usage: python -m code.src.audit.extractor --input data/raw --output data/processed/summaries.json
    """
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description='Extract A/B test summaries from HTML files')
    parser.add_argument('--input', type=Path, required=True, help='Input directory containing HTML files')
    parser.add_argument('--output', type=Path, required=True, help='Output JSON file path')
    args = parser.parse_args()

    logger.info(f"Starting extraction from {args.input} to {args.output}")
    summaries = extract_all(args.input, args.output)
    logger.info(f"Extraction complete. Found {len(summaries)} valid summaries.")


if __name__ == '__main__':
    main()
