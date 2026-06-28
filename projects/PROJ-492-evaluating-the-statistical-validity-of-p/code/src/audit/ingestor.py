"""URL ingestion and deduplication module for A/B test audit pipeline.

This module reads URLs from an input CSV file, deduplicates them,
and writes the deduplicated list to an output CSV file.
"""

import csv
import os
from pathlib import Path
from typing import List, Set, Tuple, Optional
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.utils.helpers import domain_from_url


def read_urls_from_csv(input_path: str) -> List[str]:
    """Read URLs from a CSV file.

    Args:
        input_path: Path to the input CSV file containing URLs.

    Returns:
        List of URLs read from the CSV file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the CSV format is invalid.
    """
    logger = get_default_logger()
    logger.info(f"Reading URLs from {input_path}")

    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}", error_code="ERR-001")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    urls = []
    with open(input_file, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        # Check if 'url' column exists
        if reader.fieldnames is None or 'url' not in reader.fieldnames:
            logger.error(f"Invalid CSV format: missing 'url' column", error_code="ERR-002")
            raise ValueError("CSV must contain a 'url' column")

        for row_num, row in enumerate(reader, start=2):
            url = row['url'].strip()
            if url:  # Skip empty URLs
                urls.append(url)

    logger.info(f"Read {len(urls)} URLs from {input_path}")
    return urls


def deduplicate_urls(urls: List[str], case_insensitive: bool = True) -> Tuple[List[str], int]:
    """Deduplicate a list of URLs.

    Args:
        urls: List of URLs to deduplicate.
        case_insensitive: If True, treat URLs as case-insensitive for deduplication.

    Returns:
        Tuple of (deduplicated URL list, count of duplicates removed).
    """
    logger = get_default_logger()

    seen: Set[str] = set()
    deduplicated: List[str] = []
    duplicates_removed = 0

    for url in urls:
        if case_insensitive:
            key = url.lower()
        else:
            key = url

        if key not in seen:
            seen.add(key)
            deduplicated.append(url)
        else:
            duplicates_removed += 1
            logger.debug(f"Duplicate URL removed: {url}")

    logger.info(f"Deduplicated {len(urls)} URLs -> {len(deduplicated)} unique URLs ({duplicates_removed} duplicates removed)")
    return deduplicated, duplicates_removed


def write_urls_to_csv(urls: List[str], output_path: str, metadata: Optional[dict] = None) -> None:
    """Write deduplicated URLs to a CSV file.

    Args:
        urls: List of URLs to write.
        output_path: Path to the output CSV file.
        metadata: Optional metadata to include in the CSV.
    """
    logger = get_default_logger()
    logger.info(f"Writing {len(urls)} URLs to {output_path}")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'domain'])
        writer.writeheader()

        for url in urls:
            domain = domain_from_url(url)
            writer.writerow({
                'url': url,
                'domain': domain if domain else ''
            })

    logger.info(f"Wrote {len(urls)} URLs to {output_path}")


def ingest_and_deduplicate(input_path: str, output_path: str) -> dict:
    """Main entry point for URL ingestion and deduplication.

    Reads URLs from input CSV, deduplicates them, and writes to output CSV.

    Args:
        input_path: Path to input CSV file.
        output_path: Path to output CSV file.

    Returns:
        Dictionary with ingestion statistics.
    """
    logger = get_default_logger()
    logger.info("Starting URL ingestion and deduplication")

    # Read URLs
    urls = read_urls_from_csv(input_path)

    # Deduplicate
    deduplicated_urls, duplicates_removed = deduplicate_urls(urls)

    # Write output
    write_urls_to_csv(deduplicated_urls, output_path)

    stats = {
        'input_file': input_path,
        'output_file': output_path,
        'total_urls_read': len(urls),
        'unique_urls': len(deduplicated_urls),
        'duplicates_removed': duplicates_removed
    }

    logger.info(f"URL ingestion complete: {stats}")
    return stats


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description='Ingest and deduplicate A/B test URLs')
    parser.add_argument('--input', '-i', default='input/urls.csv',
                      help='Input CSV file path (default: input/urls.csv)')
    parser.add_argument('--output', '-o', default='output/urls_deduped.csv',
                      help='Output CSV file path (default: output/urls_deduped.csv)')

    args = parser.parse_args()

    stats = ingest_and_deduplicate(args.input, args.output)
    print(f"Ingestion complete: {stats}")

    return 0


if __name__ == '__main__':
    exit(main())
