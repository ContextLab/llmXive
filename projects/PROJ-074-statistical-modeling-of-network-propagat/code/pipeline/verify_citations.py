"""
Citation verification module for llmXive research pipeline.

This script checks markdown files for:
1. Reachable URLs (HTTP status code 200)
2. Title token overlap >= 0.7 between citation text and fetched page title

Exit codes:
0 - All citations verified successfully
1 - One or more citations failed verification
"""
import argparse
import logging
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from pipeline.utils import set_global_seed, setup_logger

# Token overlap threshold
TOKEN_OVERLAP_THRESHOLD = 0.7

# HTTP timeout in seconds
HTTP_TIMEOUT = 10

# Maximum redirects to follow
MAX_REDIRECTS = 5


def normalize_tokens(text: str) -> set:
    """
    Normalize text to a set of lowercase alphanumeric tokens.

    Args:
        text: Input string to tokenize

    Returns:
        Set of normalized tokens
    """
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation and split on non-alphanumeric
    tokens = re.findall(r'[a-z0-9]+', text)
    # Filter out very short tokens and common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'it', 'this', 'that'}
    return {t for t in tokens if len(t) > 1 and t not in stop_words}


def compute_token_overlap(title1: str, title2: str) -> float:
    """
    Compute Jaccard similarity between two titles.

    Args:
        title1: First title string
        title2: Second title string

    Returns:
        Jaccard similarity score (0.0 to 1.0)
    """
    tokens1 = normalize_tokens(title1)
    tokens2 = normalize_tokens(title2)

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union if union > 0 else 0.0


def fetch_page_title(url: str, logger: logging.Logger) -> tuple:
    """
    Fetch the HTML title from a URL.

    Args:
        url: URL to fetch
        logger: Logger instance

    Returns:
        Tuple of (success: bool, title: str or None, error: str or None)
    """
    try:
        response = requests.get(
            url,
            timeout=HTTP_TIMEOUT,
            allow_redirects=True,
            max_redirects=MAX_REDIRECTS,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; CitationVerifier/1.0)'
            }
        )

        # Check if request was successful
        if response.status_code != 200:
            return False, None, f"HTTP {response.status_code}"

        # Parse HTML and extract title
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')

        if title_tag and title_tag.string:
            return True, title_tag.string.strip(), None
        else:
            return False, None, "No title tag found"

    except requests.exceptions.RequestException as e:
        return False, None, str(e)
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"


def extract_citations_from_markdown(file_path: Path, logger: logging.Logger) -> list:
    """
    Extract citation URLs and their titles from a markdown file.

    Args:
        file_path: Path to markdown file
        logger: Logger instance

    Returns:
        List of tuples (url, citation_title, line_number)
    """
    citations = []

    # Pattern for markdown links: [title](url)
    link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                matches = link_pattern.findall(line)
                for title, url in matches:
                    # Skip internal references
                    if not url.startswith(('http://', 'https://')):
                        continue
                    citations.append((url, title.strip(), line_num))

    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")

    return citations


def verify_citation(url: str, citation_title: str, line_num: int, logger: logging.Logger) -> tuple:
    """
    Verify a single citation.

    Args:
        url: URL to verify
        citation_title: Title from the markdown citation
        line_num: Line number in the source file
        logger: Logger instance

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check URL reachability and fetch page title
    success, page_title, error = fetch_page_title(url, logger)

    if not success:
        return False, f"URL unreachable at line {line_num}: {error}"

    # Compute token overlap
    overlap = compute_token_overlap(citation_title, page_title)

    if overlap < TOKEN_OVERLAP_THRESHOLD:
        return False, (
            f"Low title overlap ({overlap:.2f} < {TOKEN_OVERLAP_THRESHOLD}) at line {line_num}: "
            f"Citation: '{citation_title[:50]}...', Page: '{page_title[:50]}...'"
        )

    logger.debug(
        f"Citation verified at line {line_num}: overlap={overlap:.2f}, "
        f"citation='{citation_title[:30]}...', page='{page_title[:30]}...'"
    )

    return True, "OK"


def verify_all_citations(markdown_dir: Path, logger: logging.Logger) -> bool:
    """
    Verify all citations in markdown files within a directory.

    Args:
        markdown_dir: Directory containing markdown files
        logger: Logger instance

    Returns:
        True if all citations verified successfully, False otherwise
    """
    all_passed = True

    # Find all markdown files
    markdown_files = list(markdown_dir.glob('**/*.md'))

    if not markdown_files:
        logger.warning(f"No markdown files found in {markdown_dir}")
        return True

    logger.info(f"Found {len(markdown_files)} markdown files to verify")

    for md_file in markdown_files:
        logger.info(f"Verifying citations in {md_file}")
        citations = extract_citations_from_markdown(md_file, logger)

        if not citations:
            logger.debug(f"No citations found in {md_file}")
            continue

        for url, title, line_num in citations:
            success, message = verify_citation(url, title, line_num, logger)

            if success:
                logger.info(f"✓ {md_file.name}:{line_num} - {message}")
            else:
                logger.error(f"✗ {md_file.name}:{line_num} - {message}")
                all_passed = False

    return all_passed


def main():
    """Main entry point for citation verification."""
    parser = argparse.ArgumentParser(
        description='Verify citations in markdown files'
    )
    parser.add_argument(
        '--dir',
        type=Path,
        default=Path('.'),
        help='Directory containing markdown files (default: current directory)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=12345,
        help='Random seed for reproducibility (default: 12345)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Set global seed
    set_global_seed(args.seed)

    # Setup logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger('verify_citations', log_level=log_level)

    logger.info("Starting citation verification")
    logger.info(f"Scanning directory: {args.dir.absolute()}")

    # Verify all citations
    all_passed = verify_all_citations(args.dir, logger)

    if all_passed:
        logger.info("All citations verified successfully")
        sys.exit(0)
    else:
        logger.error("Citation verification failed - one or more citations did not pass")
        sys.exit(1)


if __name__ == '__main__':
    main()
