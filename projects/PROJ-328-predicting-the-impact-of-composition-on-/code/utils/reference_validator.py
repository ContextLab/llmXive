"""
Reference Validator Module for Solder Hardness Prediction Pipeline.

This module provides functions to validate research sources, URLs, and citation formats.
It ensures that all references in research_verified.md are legitimate and accessible.
"""
import os
import re
import logging
import requests
from pathlib import Path
from typing import List, Optional, Tuple
from utils.error_handlers import SolderPipelineError

# Configure logger
logger = logging.getLogger(__name__)

class ConstitutionError(SolderPipelineError):
    """Raised when a citation or URL violates the constitution of valid references."""
    pass

def validate_url(url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Validate a URL by checking its format and attempting a HEAD request.

    Args:
        url: The URL to validate.
        timeout: Request timeout in seconds.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check URL format
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url_pattern.match(url):
        return False, f"Invalid URL format: {url}"

    # Check if URL is accessible
    try:
        if url.endswith('.pdf'):
            # For PDFs, we just check if we can get a 200 OK
            response = requests.head(url, timeout=timeout, allow_redirects=True)
        else:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 405:  # Method Not Allowed
                # Some servers don't support HEAD, try GET
                response = requests.get(url, timeout=timeout, allow_redirects=True)

        if response.status_code >= 400:
            return False, f"URL returned status code {response.status_code}: {url}"

        return True, None
    except requests.exceptions.RequestException as e:
        return False, f"Failed to access URL {url}: {str(e)}"

def validate_citation_format(citation: str) -> Tuple[bool, Optional[str]]:
    """
    Validate the format of a citation string.

    Expected format: "Author(s), Title, Journal/Source, Year, URL"
    or for books: "Author(s), Title, Publisher, Year"

    Args:
        citation: The citation string to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Basic pattern for citation validation
    # At minimum, should have some text and ideally a year
    citation_pattern = re.compile(
        r'.{10,}',  # At least 10 characters
        re.IGNORECASE
    )

    if not citation_pattern.match(citation):
        return False, "Citation is too short or malformed"

    # Check for common citation elements
    has_author = re.search(r'[A-Z][a-z]+,?\s+[A-Z]', citation)
    has_year = re.search(r'\b(19|20)\d{2}\b', citation)
    has_title = re.search(r'.{5,}', citation)

    if not (has_author or has_title):
        return False, "Citation missing author or title information"

    if not has_year:
        logger.warning(f"Citation may be missing year: {citation}")

    return True, None

def validate_research_md(input_path: str, output_path: str) -> bool:
    """
    Validate research sources from a markdown file and generate a verified version.

    Args:
        input_path: Path to the draft research.md file.
        output_path: Path to write the verified research_verified.md file.

    Returns:
        True if validation was successful, False otherwise.

    Raises:
        ConstitutionError: If critical validation fails.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise ConstitutionError(f"Input file not found: {input_path}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    verified_sources = []
    total_sources = 0
    valid_sources = 0
    invalid_sources = 0

    logger.info(f"Validating research sources from {input_path}")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise ConstitutionError(f"Failed to read input file: {str(e)}")

    current_section = ""
    current_citation = ""
    current_url = ""

    for line in lines:
        line = line.strip()

        # Detect section headers
        if line.startswith('#'):
            if current_citation and current_url:
                # Process the previous citation
                is_valid_url, url_error = validate_url(current_url)
                is_valid_citation, citation_error = validate_citation_format(current_citation)

                if is_valid_url and is_valid_citation:
                    verified_sources.append({
                        'section': current_section,
                        'citation': current_citation,
                        'url': current_url,
                        'status': 'verified'
                    })
                    valid_sources += 1
                else:
                    errors = []
                    if not is_valid_url:
                        errors.append(f"URL error: {url_error}")
                    if not is_valid_citation:
                        errors.append(f"Citation error: {citation_error}")
                    logger.warning(f"Invalid source: {current_citation} | {current_url} | {'; '.join(errors)}")
                    invalid_sources += 1

                current_citation = ""
                current_url = ""

            current_section = line
            continue

        # Parse citation and URL
        if line.startswith('- [x]') or line.startswith('- [ ]'):
            # This is a checklist item, likely a source
            if current_citation and current_url:
                # Process the previous citation first
                is_valid_url, url_error = validate_url(current_url)
                is_valid_citation, citation_error = validate_citation_format(current_citation)

                if is_valid_url and is_valid_citation:
                    verified_sources.append({
                        'section': current_section,
                        'citation': current_citation,
                        'url': current_url,
                        'status': 'verified'
                    })
                    valid_sources += 1
                else:
                    errors = []
                    if not is_valid_url:
                        errors.append(f"URL error: {url_error}")
                    if not is_valid_citation:
                        errors.append(f"Citation error: {citation_error}")
                    logger.warning(f"Invalid source: {current_citation} | {current_url} | {'; '.join(errors)}")
                    invalid_sources += 1

                current_citation = ""
                current_url = ""

            # Extract citation and URL from the line
            # Format: - [x] Citation text [URL]
            match = re.match(r'- \[(x| )\]\s+(.+?)\s+\[(https?://[^\]]+)\]', line)
            if match:
                current_citation = match.group(2).strip()
                current_url = match.group(3).strip()
                total_sources += 1
            elif re.match(r'- \[(x| )\]\s+(.+)', line):
                # No URL found, just citation
                current_citation = re.match(r'- \[(x| )\]\s+(.+)', line).group(2).strip()
                current_url = ""
                total_sources += 1

    # Process the last citation if exists
    if current_citation and current_url:
        is_valid_url, url_error = validate_url(current_url)
        is_valid_citation, citation_error = validate_citation_format(current_citation)

        if is_valid_url and is_valid_citation:
            verified_sources.append({
                'section': current_section,
                'citation': current_citation,
                'url': current_url,
                'status': 'verified'
            })
            valid_sources += 1
        else:
            errors = []
            if not is_valid_url:
                errors.append(f"URL error: {url_error}")
            if not is_valid_citation:
                errors.append(f"Citation error: {citation_error}")
            logger.warning(f"Invalid source: {current_citation} | {current_url} | {'; '.join(errors)}")
            invalid_sources += 1

    # Write verified sources to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Verified Research Sources\n\n")
            f.write(f"Total sources reviewed: {total_sources}\n")
            f.write(f"Verified sources: {valid_sources}\n")
            f.write(f"Invalid sources: {invalid_sources}\n\n")
            f.write("## Verification Details\n\n")

            current_section = ""
            for source in verified_sources:
                if source['section'] != current_section:
                    current_section = source['section']
                    f.write(f"### {current_section}\n\n")

                f.write(f"- [x] {source['citation']} [{source['url']}]\n")
                f.write(f"  - Status: {source['status']}\n\n")

        logger.info(f"Successfully wrote verified sources to {output_path}")
        logger.info(f"Summary: {valid_sources}/{total_sources} sources verified")

        # If no sources were verified, raise an error
        if valid_sources == 0:
            raise ConstitutionError("No valid research sources found. Verification failed.")

        return True

    except Exception as e:
        raise ConstitutionError(f"Failed to write output file: {str(e)}")

def main():
    """Main entry point for the reference validator."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate research sources and generate verified list.')
    parser.add_argument('--input', type=str, default='data/config/candidate_sources.txt',
                      help='Path to the draft research sources file')
    parser.add_argument('--output', type=str, default='specs/001-predict-solder-hardness/research_verified.md',
                      help='Path to write the verified research sources file')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        success = validate_research_md(args.input, args.output)
        if success:
            logger.info("Research source validation completed successfully.")
            return 0
        else:
            logger.error("Research source validation failed.")
            return 1
    except ConstitutionError as e:
        logger.error(f"Constitution error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
