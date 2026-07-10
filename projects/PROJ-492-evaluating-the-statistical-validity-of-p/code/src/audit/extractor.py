"""
Extraction logic for A/B test summaries from fetched HTML.
Produces ABTestSummary objects (mapped to ABSummary in usage),
handles missing fields, and logs ERR-001 through ERR-099 codes.
"""
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup

from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Map of error codes to descriptions
ERROR_CODES = {
    "ERR-001": "Missing required field: title",
    "ERR-002": "Missing required field: domain",
    "ERR-003": "Missing required field: sample_size_control",
    "ERR-004": "Missing required field: sample_size_treatment",
    "ERR-005": "Missing required field: conversion_rate_control",
    "ERR-006": "Missing required field: conversion_rate_treatment",
    "ERR-007": "Missing required field: p_value",
    "ERR-008": "Malformed p-value format",
    "ERR-009": "Missing required field: effect_size",
    "ERR-010": "Malformed effect_size format",
    "ERR-011": "Missing required field: test_type",
    "ERR-012": "Missing required field: publication_year",
    "ERR-013": "Missing required field: confidence_interval",
    "ERR-014": "Malformed confidence_interval format",
    "ERR-015": "Missing required field: outcome_type",
    "ERR-016": "Inconsistent sample sizes (control vs treatment)",
    "ERR-017": "Invalid conversion rate value (out of bounds)",
    "ERR-018": "Invalid p-value (out of bounds)",
    "ERR-019": "Invalid effect size (out of bounds)",
    "ERR-020": "Missing URL in metadata",
    "ERR-021": "Missing fetch timestamp in metadata",
    "ERR-022": "Malformed HTML structure",
    "ERR-023": "Could not extract numeric value",
    "ERR-024": "Conflicting sample sizes detected",
    "ERR-025": "Missing baseline conversion rate",
    "ERR-026": "Missing treatment conversion rate",
    "ERR-027": "Missing control conversion rate",
    "ERR-028": "Missing p-value reported",
    "ERR-029": "Missing effect size reported",
    "ERR-030": "Missing test type reported",
    "ERR-031": "Missing publication year",
    "ERR-032": "Missing confidence interval",
    "ERR-033": "Missing outcome type",
    "ERR-034": "Malformed numeric value for sample_size_control",
    "ERR-035": "Malformed numeric value for sample_size_treatment",
    "ERR-036": "Malformed numeric value for conversion_rate_control",
    "ERR-037": "Malformed numeric value for conversion_rate_treatment",
    "ERR-038": "Malformed numeric value for p_value",
    "ERR-039": "Malformed numeric value for effect_size",
    "ERR-040": "Malformed numeric value for confidence_interval",
}

logger = get_default_logger(__name__)


def extract_single_float(text: str, error_code: str) -> Optional[float]:
    """Extract a single float from text, logging error if not found."""
    if not text:
        logger.warning(get_error_message(error_code))
        return None

    # Clean text: remove %, commas, whitespace
    cleaned = re.sub(r'[%,\s]', '', text.strip())

    try:
        value = float(cleaned)
        return value
    except ValueError:
        logger.warning(get_error_message(error_code))
        return None


def extract_single_int(text: str, error_code: str) -> Optional[int]:
    """Extract a single int from text, logging error if not found."""
    if not text:
        logger.warning(get_error_message(error_code))
        return None

    # Clean text: remove commas, whitespace
    cleaned = re.sub(r'[,\s]', '', text.strip())

    try:
        value = int(float(cleaned))  # Handle "100.0" cases
        return value
    except ValueError:
        logger.warning(get_error_message(error_code))
        return None


def extract_field_from_html(soup: BeautifulSoup, selectors: List[str], error_code: str) -> Optional[str]:
    """Extract field value from HTML using multiple possible selectors."""
    for selector in selectors:
        try:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        except Exception:
            continue

    logger.warning(get_error_message(error_code))
    return None


def extract_summary_from_html(html_content: str, url: str, metadata: Dict[str, Any]) -> Optional[ABTestSummary]:
    """
    Extract A/B test summary from HTML content.
    Returns ABTestSummary object or None if extraction fails completely.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        logger.error(f"ERR-022: Malformed HTML structure - {str(e)}")
        return None

    # Extract fields with appropriate selectors and error codes
    title = extract_field_from_html(soup, [
        'h1', 'h2', '.title', '.post-title', 'meta[property="og:title"]',
        'title'
    ], "ERR-001")

    domain = extract_field_from_html(soup, [
        'meta[property="og:site_name"]', '.domain', '.site-name'
    ], "ERR-002")
    if not domain and url:
        from code.src.utils.helpers import domain_from_url
        domain = domain_from_url(url)

    # Sample sizes
    sample_size_control = extract_field_from_html(soup, [
        'meta[name="sample-size-control"]', '.n-control', '.sample-control',
        '[data-sample-control]', 'p:contains("control group")',
        'p:contains("n=")'
    ], "ERR-003")
    n_control = extract_single_int(sample_size_control, "ERR-034") if sample_size_control else None

    sample_size_treatment = extract_field_from_html(soup, [
        'meta[name="sample-size-treatment"]', '.n-treatment', '.sample-treatment',
        '[data-sample-treatment]', 'p:contains("treatment group")',
        'p:contains("n=")'
    ], "ERR-004")
    n_treatment = extract_single_int(sample_size_treatment, "ERR-035") if sample_size_treatment else None

    # Conversion rates
    conversion_rate_control = extract_field_from_html(soup, [
        'meta[name="conversion-control"]', '.cr-control', '.rate-control',
        '[data-cr-control]', 'p:contains("control rate")',
        'p:contains("baseline")'
    ], "ERR-005")
    cr_control = extract_single_float(conversion_rate_control, "ERR-036") if conversion_rate_control else None

    conversion_rate_treatment = extract_field_from_html(soup, [
        'meta[name="conversion-treatment"]', '.cr-treatment', '.rate-treatment',
        '[data-cr-treatment]', 'p:contains("treatment rate")'
    ], "ERR-006")
    cr_treatment = extract_single_float(conversion_rate_treatment, "ERR-037") if conversion_rate_treatment else None

    # P-value
    p_value_str = extract_field_from_html(soup, [
        'meta[name="p-value"]', '.p-value', '.pval',
        '[data-p-value]', 'p:contains("p=")', 'p:contains("p-value")'
    ], "ERR-007")
    p_value = extract_single_float(p_value_str, "ERR-038") if p_value_str else None

    # Effect size
    effect_size_str = extract_field_from_html(soup, [
        'meta[name="effect-size"]', '.effect-size', '.es',
        '[data-effect-size]', 'p:contains("effect size")',
        'p:contains("lift")', 'p:contains("difference")'
    ], "ERR-009")
    effect_size = extract_single_float(effect_size_str, "ERR-039") if effect_size_str else None

    # Test type
    test_type = extract_field_from_html(soup, [
        'meta[name="test-type"]', '.test-type',
        '[data-test-type]', 'p:contains("z-test")',
        'p:contains("t-test")', 'p:contains("fisher")'
    ], "ERR-011")

    # Publication year
    pub_year_str = extract_field_from_html(soup, [
        'meta[name="publication-year"]', '.year', '.date',
        '[data-year]', 'time[datetime]', 'p:contains("20")'
    ], "ERR-012")
    pub_year = extract_single_int(pub_year_str, "ERR-041") if pub_year_str else None

    # Confidence interval
    ci_str = extract_field_from_html(soup, [
        'meta[name="confidence-interval"]', '.ci', '.confidence',
        '[data-ci]', 'p:contains("CI")', 'p:contains("confidence")'
    ], "ERR-013")

    # Outcome type
    outcome_type = extract_field_from_html(soup, [
        'meta[name="outcome-type"]', '.outcome-type',
        '[data-outcome-type]', 'p:contains("binary")',
        'p:contains("continuous")'
    ], "ERR-015")

    # Validate required fields and log specific errors
    errors = []
    if not title: errors.append("ERR-001")
    if not domain: errors.append("ERR-002")
    if n_control is None: errors.append("ERR-003")
    if n_treatment is None: errors.append("ERR-004")
    if cr_control is None: errors.append("ERR-005")
    if cr_treatment is None: errors.append("ERR-006")
    if p_value is None: errors.append("ERR-007")
    if effect_size is None: errors.append("ERR-009")
    if not test_type: errors.append("ERR-011")
    if not pub_year: errors.append("ERR-012")
    if not outcome_type: errors.append("ERR-015")

    # Log all errors
    for err_code in errors:
        logger.warning(get_error_message(err_code))

    # Check for sample size mismatch
    if n_control is not None and n_treatment is not None:
        if abs(n_control - n_treatment) > 0:
            logger.warning(get_error_message("ERR-016"))

    # Validate numeric ranges
    if cr_control is not None and (cr_control < 0 or cr_control > 1):
        logger.warning(get_error_message("ERR-017"))
    if cr_treatment is not None and (cr_treatment < 0 or cr_treatment > 1):
        logger.warning(get_error_message("ERR-017"))
    if p_value is not None and (p_value < 0 or p_value > 1):
        logger.warning(get_error_message("ERR-018"))
    if effect_size is not None and abs(effect_size) > 100:
        logger.warning(get_error_message("ERR-019"))

    # Create summary object even if some fields are missing
    # Missing fields will be None, which downstream components can handle
    summary = ABTestSummary(
      source_url=url,
      domain=domain,
      title=title,
      sample_size_control=n_control,
      sample_size_treatment=n_treatment,
      conversion_rate_control=cr_control,
      conversion_rate_treatment=cr_treatment,
      p_value=p_value,
      effect_size=effect_size,
      test_type=test_type,
      publication_year=pub_year,
      confidence_interval=ci_str,
      outcome_type=outcome_type,
      fetch_timestamp=metadata.get('fetch_timestamp'),
      repository_id=metadata.get('repository_id', 'unknown')
  )

    return summary


def extract_all(html_files: List[Path], urls: List[str], metadata_list: List[Dict[str, Any]]) -> List[ABTestSummary]:
    """
    Extract summaries from multiple HTML files.
    Returns list of ABTestSummary objects.
    """
    summaries = []
    for i, (html_file, url, metadata) in enumerate(zip(html_files, urls, metadata_list)):
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            summary = extract_summary_from_html(html_content, url, metadata)
            if summary:
                summaries.append(summary)
        except Exception as e:
            logger.error(f"Failed to extract from {html_file}: {str(e)}")
            # Create a minimal summary with error flags
            summary = ABTestSummary(
                source_url=url,
                domain=None,
                title=None,
                sample_size_control=None,
                sample_size_treatment=None,
                conversion_rate_control=None,
                conversion_rate_treatment=None,
                p_value=None,
                effect_size=None,
                test_type=None,
                publication_year=None,
                confidence_interval=None,
                outcome_type=None,
                fetch_timestamp=metadata.get('fetch_timestamp'),
                repository_id=metadata.get('repository_id', 'unknown')
            )
            summaries.append(summary)

    return summaries


def write_summaries_to_json(summaries: List[ABTestSummary], output_path: Path) -> None:
    """Write extracted summaries to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [summary.model_dump() for summary in summaries]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    logger.info(f"Extracted {len(summaries)} summaries to {output_path}")


def main():
    """Main entry point for extraction."""
    import argparse
    from code.src.audit.fetcher import fetch_html_to_file

    parser = argparse.ArgumentParser(description='Extract A/B test summaries from fetched HTML')
    parser.add_argument('--input-dir', type=Path, default=Path('data/raw'),
                      help='Directory containing fetched HTML files')
    parser.add_argument('--output', type=Path, default=Path('data/extracted_summaries.json'),
                      help='Output JSON file for extracted summaries')
    parser.add_argument('--urls-file', type=Path, default=Path('input/urls.csv'),
                      help='CSV file containing URLs')
    args = parser.parse_args()

    # Read URLs
    urls = []
    if args.urls_file.exists():
        import csv
        with open(args.urls_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                urls.append(row['url'])

    # Find HTML files
    html_files = sorted(args.input_dir.glob('*.html'))
    if not html_files:
        logger.error("No HTML files found in input directory")
        return 1

    # Prepare metadata
    from datetime import datetime
    metadata_list = []
    for i, html_file in enumerate(html_files):
        metadata_list.append({
            'fetch_timestamp': datetime.now().isoformat(),
            'repository_id': f'repo_{i:04d}'
        })

    # Extract summaries
    summaries = extract_all(html_files, urls[:len(html_files)], metadata_list)

    # Write output
    write_summaries_to_json(summaries, args.output)

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
