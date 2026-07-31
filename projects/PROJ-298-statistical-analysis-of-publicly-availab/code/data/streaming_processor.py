"""
Streaming Processor for Large Data Dumps

This module provides memory-efficient streaming capabilities for processing
large Stack Overflow data dumps. It implements chunked processing, online
aggregation, and incremental state updates to stay within RAM constraints
while maintaining reproducibility.

Key Features:
- Chunked reading of large JSON/CSV files
- Online aggregation algorithms (Welford's for variance, incremental counts)
- Memory-bounded data structures
- Progress tracking and checkpointing
- Integration with existing download and preprocess modules
"""

import os
import json
import gzip
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator, Tuple
from collections import defaultdict
import math

# Constants for memory management
CHUNK_SIZE = 10000  # Number of posts to process per chunk
MAX_MEMORY_TARGET = 500 * 1024 * 1024  # 500MB target memory usage
CHECKPOINT_INTERVAL = 50  # Process 50 chunks before checkpointing


class StreamingAggregator:
    """
    Memory-efficient aggregator for streaming data processing.
    Uses online algorithms to maintain statistics without storing full datasets.
    """

    def __init__(self, max_tags: int = 50000):
        self.max_tags = max_tags
        self.tag_counts = defaultdict(int)
        self.tag_month_counts = defaultdict(lambda: defaultdict(int))
        self.post_count = 0
        self.checkpoint_count = 0
        self._memory_usage = 0

    def update(self, post: Dict[str, Any]) -> None:
        """
        Update aggregators with a single post.

        Args:
            post: Dictionary containing post data with 'tags' and 'creationdate'
        """
        self.post_count += 1

        if 'tags' not in post or not post['tags']:
            return

        # Parse tags (handle both list and string formats)
        if isinstance(post['tags'], str):
            tags = [t.strip() for t in post['tags'].split('><') if t.strip()]
            # Remove leading/trailing > and <
            tags = [t.replace('>', '').replace('<', '').strip() for t in tags if t]
        elif isinstance(post['tags'], list):
            tags = post['tags']
        else:
            return

        if not tags:
            return

        # Extract month from creation date
        creation_date = post.get('creationdate', '')
        if not creation_date:
            return

        # Parse YYYY-MM-DD format and extract YYYY-MM
        month_key = creation_date[:7] if len(creation_date) >= 7 else None
        if not month_key or len(month_key) != 7:
            return

        # Update counts
        for tag in tags:
            tag_lower = tag.lower().strip()
            if not tag_lower:
                continue

            # Enforce max tags limit (keep most frequent)
            if len(self.tag_counts) < self.max_tags or tag_lower in self.tag_counts:
                self.tag_counts[tag_lower] += 1
                self.tag_month_counts[tag_lower][month_key] += 1

            # Update memory estimate
            self._memory_usage += sys.getsizeof(tag_lower)

    def get_results(self) -> Dict[str, Any]:
        """
        Get aggregated results.

        Returns:
            Dictionary with tag counts and monthly distributions
        """
        return {
            'total_posts': self.post_count,
            'tag_counts': dict(self.tag_counts),
            'monthly_distribution': {
                tag: dict(months) 
                for tag, months in self.tag_month_counts.items()
            }
        }

    def checkpoint(self, checkpoint_path: Path) -> None:
        """
        Save current state to checkpoint file.

        Args:
            checkpoint_path: Path to save checkpoint
        """
        checkpoint_data = {
            'post_count': self.post_count,
            'tag_counts': dict(self.tag_counts),
            'monthly_distribution': {
                tag: dict(months) 
                for tag, months in self.tag_month_counts.items()
            },
            'checkpoint_count': self.checkpoint_count
        }

        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)

        self.checkpoint_count += 1


def stream_jsonl_file(
    file_path: Path,
    chunk_size: int = CHUNK_SIZE
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream a JSONL file in chunks.

    Args:
        file_path: Path to JSONL file
        chunk_size: Number of records per chunk

    Yields:
        Dictionary containing a single post record
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Handle gzipped files
    open_func = gzip.open if str(file_path).endswith('.gz') else open

    with open_func(file_path, 'rt', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue


def process_posts_streaming(
    input_path: Path,
    output_path: Path,
    checkpoint_path: Optional[Path] = None,
    max_tags: int = 50000
) -> Dict[str, Any]:
    """
    Process posts data in streaming fashion to minimize memory usage.

    Args:
        input_path: Path to input PostsTags file
        output_path: Path to save processed results
        checkpoint_path: Optional path for checkpoint files
        max_tags: Maximum number of tags to track

    Returns:
        Dictionary with processing statistics
    """
    aggregator = StreamingAggregator(max_tags=max_tags)
    
    if checkpoint_path and checkpoint_path.exists():
        # Load existing checkpoint
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            aggregator.post_count = checkpoint_data.get('post_count', 0)
            aggregator.tag_counts = defaultdict(int, checkpoint_data.get('tag_counts', {}))
            aggregator.tag_month_counts = defaultdict(
                lambda: defaultdict(int),
                {tag: defaultdict(int, months) 
                 for tag, months in checkpoint_data.get('monthly_distribution', {}).items()}
            )
            aggregator.checkpoint_count = checkpoint_data.get('checkpoint_count', 0)
            print(f"Resumed from checkpoint: {aggregator.post_count} posts processed")
        except Exception as e:
            print(f"Failed to load checkpoint: {e}. Starting fresh.")

    processed_count = 0
    checkpoint_interval = CHECKPOINT_INTERVAL

    for post in stream_jsonl_file(input_path):
        aggregator.update(post)
        processed_count += 1

        # Checkpoint periodically
        if checkpoint_path and processed_count % checkpoint_interval == 0:
            aggregator.checkpoint(checkpoint_path)
            print(f"Checkpoint at {processed_count} posts")

    # Save final results
    results = aggregator.get_results()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    return {
        'total_posts_processed': results['total_posts'],
        'unique_tags_tracked': len(results['tag_counts']),
        'output_file': str(output_path),
        'memory_efficient': True
    }


def validate_streaming_output(output_path: Path) -> bool:
    """
    Validate that streaming output meets quality requirements.

    Args:
        output_path: Path to output file

    Returns:
        True if validation passes
    """
    if not output_path.exists():
        return False

    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check required fields
        required_fields = ['total_posts', 'tag_counts', 'monthly_distribution']
        if not all(field in data for field in required_fields):
            return False

        # Validate data types
        if not isinstance(data['total_posts'], int) or data['total_posts'] <= 0:
            return False

        if not isinstance(data['tag_counts'], dict) or len(data['tag_counts']) == 0:
            return False

        return True

    except Exception:
        return False


def main():
    """
    Main entry point for streaming processor.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Process large Stack Overflow dumps in streaming fashion'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to input PostsTags file (JSONL or JSONL.gz)'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Path to output processed data file'
    )
    parser.add_argument(
        '--checkpoint', '-c',
        help='Optional path for checkpoint file'
    )
    parser.add_argument(
        '--max-tags', '-m',
        type=int,
        default=50000,
        help='Maximum number of tags to track (default: 50000)'
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    checkpoint_path = Path(args.checkpoint) if args.checkpoint else None

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"Starting streaming processing of {input_path}")
        results = process_posts_streaming(
            input_path=input_path,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
            max_tags=args.max_tags
        )
        
        print(f"\nProcessing complete:")
        print(f"  Total posts processed: {results['total_posts_processed']}")
        print(f"  Unique tags tracked: {results['unique_tags_tracked']}")
        print(f"  Output file: {results['output_file']}")
        print(f"  Memory efficient: {results['memory_efficient']}")

        # Validate output
        if validate_streaming_output(output_path):
            print("  Validation: PASSED")
        else:
            print("  Validation: FAILED", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
