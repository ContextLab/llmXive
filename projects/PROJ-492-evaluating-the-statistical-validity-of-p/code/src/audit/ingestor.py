"""
URL Ingestion and Deduplication Module (T018).

Reads a CSV file containing URLs, deduplicates them based on domain and path,
and writes the cleaned list back to a CSV file.
"""
import csv
import logging
from pathlib import Path
from typing import List, Set, Tuple, Optional

from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.utils.helpers import domain_from_url


def read_urls_from_csv(input_path: Path) -> List[Tuple[str, Optional[str]]]:
    """
    Reads URLs from a CSV file.

    Expected CSV format:
    - Header: 'url' or 'url,source_id'
    - If 'source_id' is missing, it defaults to None.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        List of tuples (url, source_id).

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the CSV format is invalid.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input URL file not found: {input_path}")

    logger = get_default_logger()
    urls = []

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'url' not in reader.fieldnames:
            raise ValueError(f"CSV must contain a 'url' column. Found: {reader.fieldnames}")

        for row_num, row in enumerate(reader, start=2):
            url = row['url'].strip()
            if not url:
                logger.warning(f"Row {row_num}: Empty URL skipped.")
                continue
            
            source_id = row.get('source_id', '').strip() or None
            
            # Basic validation
            if not url.startswith(('http://', 'https://')):
                logger.warning(f"Row {row_num}: URL '{url}' does not start with http(s), skipping.")
                continue

            urls.append((url, source_id))

    logger.info(f"Read {len(urls)} valid URLs from {input_path}.")
    return urls


def deduplicate_urls(urls: List[Tuple[str, Optional[str]]]) -> List[Tuple[str, Optional[str]]]:
    """
    Deduplicates a list of (url, source_id) tuples.

    Deduplication logic:
    1. Normalize URL: lowercase scheme and domain, remove trailing slashes.
    2. Keep the first occurrence of a unique URL.
    3. If a duplicate is found, log a warning.

    Args:
        urls: List of (url, source_id) tuples.

    Returns:
        List of unique (url, source_id) tuples.
    """
    logger = get_default_logger()
    seen_urls: Set[str] = set()
    unique_urls: List[Tuple[str, Optional[str]]] = []
    duplicates_count = 0

    for url, source_id in urls:
        # Normalize for comparison
        normalized = url.lower().rstrip('/')
        
        if normalized in seen_urls:
            duplicates_count += 1
            logger.debug(f"Duplicate URL detected: {url} (kept first occurrence)")
            continue

        seen_urls.add(normalized)
        unique_urls.append((url, source_id))

    if duplicates_count > 0:
        logger.warning(f"Removed {duplicates_count} duplicate URLs.")
    
    logger.info(f"Deduplication complete. {len(unique_urls)} unique URLs remaining.")
    return unique_urls


def write_urls_to_csv(urls: List[Tuple[str, Optional[str]]], output_path: Path) -> None:
    """
    Writes the list of URLs to a CSV file.

    Args:
        urls: List of (url, source_id) tuples.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'source_id'])
        for url, source_id in urls:
            # Handle None source_id by writing empty string
            sid = source_id if source_id is not None else ''
            writer.writerow([url, sid])

    logging.info(f"Wrote {len(urls)} URLs to {output_path}")


def ingest_and_deduplicate(input_path: Path, output_path: Path) -> List[Tuple[str, Optional[str]]]:
    """
    Main entry point for the ingestion and deduplication pipeline.

    1. Reads URLs from input_path.
    2. Deduplicates them.
    3. Writes results to output_path.

    Args:
        input_path: Path to the input CSV.
        output_path: Path to the output CSV.

    Returns:
        List of deduplicated (url, source_id) tuples.
    """
    logger = get_default_logger()
    logger.info(f"Starting ingestion from {input_path} to {output_path}")

    try:
        urls = read_urls_from_csv(input_path)
        unique_urls = deduplicate_urls(urls)
        write_urls_to_csv(unique_urls, output_path)
        logger.info("Ingestion and deduplication completed successfully.")
        return unique_urls
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise


def main() -> None:
    """
    CLI entry point for T018.
    Expects arguments: --input <path> --output <path>
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Ingest and deduplicate URLs for A/B test audit.")
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV with URLs')
    parser.add_argument('--output', type=str, required=True, help='Path to output CSV for deduplicated URLs')
    
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        ingest_and_deduplicate(input_path, output_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error during ingestion: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
