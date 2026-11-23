import os
import json
import gzip
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator, Tuple
import sys

# Add project root to path for imports if running as script
if 'code' not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if code_root.name == 'code':
        sys.path.insert(0, str(code_root.parent))

from data.download import ensure_output_dir

class StreamingAggregator:
    """
    Memory-efficient aggregator for streaming large JSON/JSONL datasets.
    Processes data in chunks to stay within RAM constraints.
    """

    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size
        self.counters: Dict[str, int] = {}
        self.total_posts = 0
        self.processed_bytes = 0

    def update(self, record: Dict[str, Any]) -> None:
        """Update internal state with a single record."""
        tags = record.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split('|') if t.strip()]
        
        for tag in tags:
            tag = tag.lower().strip()
            if tag:
                self.counters[tag] = self.counters.get(tag, 0) + 1
                self.total_posts += 1

    def get_results(self) -> Dict[str, int]:
        """Return aggregated results."""
        return self.counters

def stream_jsonl_file(
    file_path: Path, 
    decompress: bool = False,
    chunk_size: int = 10000
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream a JSONL file (optionally gzipped) line by line.
    Yields parsed dictionaries one at a time.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    opener = gzip.open if decompress else open
    mode = 'rt' if decompress else 'r'
    
    with opener(file_path, mode, encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                yield record
            except json.JSONDecodeError as e:
                # Log error but continue processing
                sys.stderr.write(f"Warning: Skipping malformed JSON at line {line_num}: {e}\n")
                continue

def process_posts_streaming(
    input_path: Path,
    output_path: Path,
    decompress: bool = False,
    chunk_size: int = 10000
) -> Dict[str, Any]:
    """
    Process PostsTags dump in streaming fashion to aggregate tag frequencies.
    Outputs a JSON file with aggregated counts, avoiding loading entire dataset into memory.
    
    Args:
        input_path: Path to the raw JSONL (or gzipped JSONL) file
        output_path: Path to write the aggregated results
        decompress: Whether the input file is gzipped
        chunk_size: Number of records to process before yielding (for streaming)
    
    Returns:
        Dict with processing statistics
    """
    ensure_output_dir(output_path)
    
    aggregator = StreamingAggregator(chunk_size=chunk_size)
    processed_count = 0
    start_time = __import__('time').time()
    
    sys.stderr.write(f"Starting streaming processing of {input_path}...\n")
    
    for record in stream_jsonl_file(input_path, decompress=decompress):
        aggregator.update(record)
        processed_count += 1
        
        if processed_count % 100000 == 0:
            elapsed = __import__('time').time() - start_time
            sys.stderr.write(f"Processed {processed_count:,} records in {elapsed:.2f}s...\n")
    
    elapsed = __import__('time').time() - start_time
    results = aggregator.get_results()
    
    # Sort results by count descending for easier inspection
    sorted_results = dict(sorted(results.items(), key=lambda x: x[1], reverse=True))
    
    output_data = {
        "metadata": {
            "source_file": str(input_path),
            "total_posts_processed": aggregator.total_posts,
            "unique_tags": len(sorted_results),
            "processing_time_seconds": round(elapsed, 2),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        },
        "tag_counts": sorted_results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    sys.stderr.write(f"Completed processing {processed_count:,} records in {elapsed:.2f}s\n")
    sys.stderr.write(f"Output written to {output_path}\n")
    
    return output_data

def validate_streaming_output(
    output_path: Path,
    min_tags: int = 100,
    min_posts: int = 1000
) -> bool:
    """
    Validate that the streaming output file meets minimum quality thresholds.
    """
    if not output_path.exists():
        sys.stderr.write(f"Validation failed: Output file does not exist: {output_path}\n")
        return False
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "tag_counts" not in data:
            sys.stderr.write("Validation failed: Missing 'tag_counts' key\n")
            return False
        
        tag_count = len(data["tag_counts"])
        post_count = data.get("metadata", {}).get("total_posts_processed", 0)
        
        if tag_count < min_tags:
            sys.stderr.write(f"Validation failed: Only {tag_count} unique tags (min: {min_tags})\n")
            return False
        
        if post_count < min_posts:
            sys.stderr.write(f"Validation failed: Only {post_count} posts processed (min: {min_posts})\n")
            return False
        
        sys.stderr.write(f"Validation passed: {tag_count} tags, {post_count} posts\n")
        return True
        
    except (json.JSONDecodeError, KeyError) as e:
        sys.stderr.write(f"Validation failed: Invalid output format - {e}\n")
        return False

def main():
    """
    Main entry point for streaming data processing.
    Expects environment variables or command line arguments for paths.
    """
    # Default paths - can be overridden by environment or args
    input_file = os.environ.get('SO_DUMP_PATH', 'data/raw/posts_tags.jsonl.gz')
    output_file = os.environ.get('SO_AGGREGATED_PATH', 'data/processed/tag_counts_streaming.json')
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    # Check if input exists (for demo purposes, we might not have the real file yet)
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file not found: {input_path}\n")
        sys.stderr.write("This script requires the actual Stack Overflow dump to run.\n")
        sys.stderr.write("Set SO_DUMP_PATH environment variable to the correct path.\n")
        sys.exit(1)
    
    # Run streaming processing
    try:
        result = process_posts_streaming(
            input_path=input_path,
            output_path=output_path,
            decompress=input_file.endswith('.gz')
        )
        
        # Validate output
        if validate_streaming_output(output_path):
            sys.stderr.write("Streaming processing completed successfully.\n")
        else:
            sys.stderr.write("Streaming processing completed but validation failed.\n")
            sys.exit(1)
            
    except Exception as e:
        sys.stderr.write(f"Error during streaming processing: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
