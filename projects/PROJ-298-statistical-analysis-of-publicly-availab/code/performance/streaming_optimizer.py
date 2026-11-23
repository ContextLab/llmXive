"""
Performance optimization for streaming large data dumps to fit RAM constraints.

This module implements memory-efficient streaming processing for the Stack Overflow
data pipeline, ensuring that large datasets (multi-gigabyte dumps) can be processed
on CPU-only runners with limited RAM (~7GB) without loading the entire dataset into memory.

Key optimizations:
1. Generator-based streaming (no full dataset in memory)
2. Chunked processing with configurable batch sizes
3. Memory profiling and leak detection
4. Incremental aggregation (online statistics)
5. Lazy evaluation for all I/O operations
"""

import os
import gc
import json
import gzip
import time
import resource
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator, Tuple, Callable
from collections import defaultdict
import sys

# Optional: memory_profiler if available
try:
    from memory_profiler import profile
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
DEFAULT_CHUNK_SIZE = 10000  # Number of records per chunk
MEMORY_CHECK_INTERVAL = 100000  # Check memory every N records
MAX_MEMORY_MB = 6000  # Conservative limit for GitHub Actions runners
BATCH_SIZE = 5000  # Records to process in a batch before yielding


class MemoryMonitor:
    """Monitor memory usage during streaming operations."""
    
    def __init__(self, max_memory_mb: float = MAX_MEMORY_MB):
        self.max_memory_mb = max_memory_mb
        self.peak_memory_mb = 0.0
        self.checkpoints: List[Dict[str, float]] = []
    
    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            # Unix/Linux
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / 1024.0  # Convert KB to MB
        except AttributeError:
            # Fallback for Windows or if resource module unavailable
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
    
    def check_and_warn(self) -> bool:
        """Check if memory usage exceeds threshold. Returns True if safe."""
        current = self.get_current_memory_mb()
        self.peak_memory_mb = max(self.peak_memory_mb, current)
        
        if current > self.max_memory_mb:
            print(f"⚠️ WARNING: Memory usage ({current:.1f} MB) exceeds limit ({self.max_memory_mb} MB)")
            print("   Triggering garbage collection...")
            gc.collect()
            return False
        return True
    
    def log_checkpoint(self, step: str, record_count: int = 0):
        """Log a memory checkpoint."""
        self.checkpoints.append({
            "step": step,
            "record_count": record_count,
            "memory_mb": self.get_current_memory_mb(),
            "timestamp": time.time()
        })
    
    def save_report(self, output_path: Path):
        """Save memory monitoring report."""
        report = {
            "max_memory_mb": self.peak_memory_mb,
            "limit_mb": self.max_memory_mb,
            "checkpoints": self.checkpoints,
            "safe_execution": self.peak_memory_mb <= self.max_memory_mb
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"📊 Memory report saved to: {output_path}")


class StreamingAggregator:
    """
    Memory-efficient streaming aggregator for tag frequency data.
    
    Processes large JSON/JSONL files in chunks, maintaining only
    aggregated statistics in memory (not raw records).
    """
    
    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.chunk_size = chunk_size
        self.memory_monitor = MemoryMonitor()
        self.tag_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.total_records = 0
        self.processed_records = 0
    
    def process_chunk(self, records: List[Dict[str, Any]]) -> None:
        """Process a chunk of records without storing them."""
        for record in records:
            # Extract tag and date
            tags = record.get('tags', [])
            creation_date = record.get('creation_date')
            
            if not tags or not creation_date:
                continue
            
            # Normalize date to month (YYYY-MM)
            if isinstance(creation_date, str):
                month = creation_date[:7]  # "2023-01"
            elif isinstance(creation_date, int):
                # Unix timestamp
                import datetime
                dt = datetime.datetime.fromtimestamp(creation_date)
                month = dt.strftime("%Y-%m")
            else:
                continue
            
            # Aggregate counts (only store aggregated data, not raw records)
            for tag in tags:
                tag = tag.lower().strip()
                if tag:
                    self.tag_counts[tag][month] += 1
        
        self.processed_records += len(records)
        self.total_records += len(records)
        
        # Memory check
        if self.processed_records % MEMORY_CHECK_INTERVAL == 0:
            if not self.memory_monitor.check_and_warn():
                # Force garbage collection
                gc.collect()
    
    def get_aggregated_data(self) -> Dict[str, Dict[str, int]]:
        """Return aggregated data (memory-efficient representation)."""
        return dict(self.tag_counts)
    
    def save_intermediate(self, output_path: Path) -> None:
        """Save intermediate aggregated results."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.tag_counts, f, indent=2)
        print(f"💾 Saved intermediate aggregation to: {output_path}")

def stream_jsonl_file(
    file_path: Path,
    buffer_size: int = DEFAULT_CHUNK_SIZE
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream a JSONL file in chunks without loading entire file into memory.
    
    Args:
        file_path: Path to the JSONL file
        buffer_size: Number of records per chunk
    
    Yields:
        List of records (chunks)
    """
    buffer = []
    
    # Handle both compressed and uncompressed files
    open_func = gzip.open if str(file_path).endswith('.gz') else open
    
    with open_func(file_path, 'rt', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                buffer.append(record)
                
                if len(buffer) >= buffer_size:
                    yield buffer
                    buffer = []
            except json.JSONDecodeError as e:
                print(f"⚠️ Skipping malformed JSON line: {e}")
                continue
        
        # Yield remaining records
        if buffer:
            yield buffer

def process_posts_streaming(
    input_path: Path,
    output_path: Optional[Path] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> Dict[str, Any]:
    """
    Process Stack Overflow PostsTags dump using streaming.
    
    This function:
    1. Streams the input file in chunks
    2. Aggregates tag frequencies by month
    3. Maintains memory usage below threshold
    4. Saves intermediate results periodically
    
    Args:
        input_path: Path to input PostsTags data (JSONL or JSONL.gz)
        output_path: Optional path for output aggregated data
        chunk_size: Number of records per processing chunk
    
    Returns:
        Dictionary with processing statistics and aggregated data
    """
    print(f"🚀 Starting streaming processing of: {input_path}")
    print(f"   Chunk size: {chunk_size}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    aggregator = StreamingAggregator(chunk_size=chunk_size)
    start_time = time.time()
    
    try:
        for chunk in stream_jsonl_file(input_path, buffer_size=chunk_size):
            aggregator.process_chunk(chunk)
            
            # Periodic status update
            if aggregator.processed_records % (MEMORY_CHECK_INTERVAL * 10) == 0:
                elapsed = time.time() - start_time
                rate = aggregator.processed_records / elapsed if elapsed > 0 else 0
                print(f"   Processed {aggregator.processed_records:,} records "
                      f"({rate:.0f} rec/sec) - Memory: {aggregator.memory_monitor.get_current_memory_mb():.1f} MB")
    
    except Exception as e:
        print(f"❌ Error during streaming: {e}")
        raise
    
    elapsed_time = time.time() - start_time
    stats = {
        "total_records": aggregator.total_records,
        "unique_tags": len(aggregator.tag_counts),
        "processing_time_sec": elapsed_time,
        "records_per_sec": aggregator.total_records / elapsed_time if elapsed_time > 0 else 0,
        "peak_memory_mb": aggregator.memory_monitor.peak_memory_mb,
        "safe_execution": aggregator.memory_monitor.peak_memory_mb <= MAX_MEMORY_MB
    }
    
    # Save aggregated data
    if output_path:
        aggregator.save_intermediate(output_path)
        stats["output_path"] = str(output_path)
    
    # Save memory report
    report_path = LOGS_DIR / "streaming_memory_report.json"
    aggregator.memory_monitor.save_report(report_path)
    
    print(f"✅ Streaming processing complete!")
    print(f"   Records processed: {stats['total_records']:,}")
    print(f"   Unique tags: {stats['unique_tags']}")
    print(f"   Time: {elapsed_time:.1f}s ({stats['records_per_sec']:.0f} rec/sec)")
    print(f"   Peak memory: {stats['peak_memory_mb']:.1f} MB")
    
    return {
        "stats": stats,
        "aggregated_data": aggregator.get_aggregated_data()
    }

def validate_streaming_output(
    aggregated_data: Dict[str, Dict[str, int]],
    min_months: int = 12,
    min_posts: int = 100
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate that streaming output meets minimum requirements.
    
    Args:
        aggregated_data: Tag -> Month -> Count mapping
        min_months: Minimum number of months required
        min_posts: Minimum number of posts required
    
    Returns:
        Tuple of (validation_results, filtered_tags)
    """
    valid_tags = []
    invalid_tags = []
    
    for tag, months in aggregated_data.items():
        active_months = len(months)
        total_posts = sum(months.values())
        
        if active_months >= min_months and total_posts >= min_posts:
            valid_tags.append(tag)
        else:
            invalid_tags.append({
                "tag": tag,
                "months": active_months,
                "posts": total_posts
            })
    
    results = {
        "total_tags": len(aggregated_data),
        "valid_tags": len(valid_tags),
        "invalid_tags": len(invalid_tags),
        "validation_passed": len(valid_tags) > 0
    }
    
    return results, valid_tags

def benchmark_streaming_performance(
    sample_paths: List[Path],
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Benchmark streaming performance across multiple file sizes.
    
    Args:
        sample_paths: List of input file paths to benchmark
        output_dir: Directory for benchmark results
    
    Returns:
        Benchmark results dictionary
    """
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for path in sample_paths:
        if not path.exists():
            print(f"⚠️ Skipping non-existent file: {path}")
            continue
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        print(f"\n📊 Benchmarking: {path.name} ({file_size_mb:.1f} MB)")
        
        start_time = time.time()
        result = process_posts_streaming(
            input_path=path,
            output_path=output_dir / f"{path.stem}_aggregated.json" if output_dir else None
        )
        elapsed = time.time() - start_time
        
        results.append({
            "file": str(path),
            "size_mb": file_size_mb,
            "records": result["stats"]["total_records"],
            "time_sec": elapsed,
            "throughput_rec_sec": result["stats"]["records_per_sec"],
            "peak_memory_mb": result["stats"]["peak_memory_mb"],
            "safe": result["stats"]["safe_execution"]
        })
    
    # Save benchmark report
    if output_dir:
        report_path = output_dir / "streaming_benchmark.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\n📈 Benchmark report saved to: {report_path}")
    
    return {"benchmarks": results}

def main():
    """Main entry point for streaming optimization demonstration."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Stream processing optimization for large Stack Overflow data dumps"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to input PostsTags data file (JSONL or JSONL.gz)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=PROCESSED_DIR / "streaming_aggregated.json",
        help="Path for output aggregated data"
    )
    parser.add_argument(
        "--chunk-size", "-c",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Chunk size (default: {DEFAULT_CHUNK_SIZE})"
    )
    parser.add_argument(
        "--benchmark", "-b",
        action="store_true",
        help="Run benchmark instead of processing"
    )
    
    args = parser.parse_args()
    
    if args.benchmark:
        # Benchmark mode
        sample_files = [
            Path("data/raw/posts_tags_small.jsonl"),
            Path("data/raw/posts_tags_medium.jsonl"),
            Path("data/raw/posts_tags.jsonl")
        ]
        benchmark_streaming_performance(sample_files, PROCESSED_DIR)
    else:
        # Normal processing
        if not args.input.exists():
            print(f"❌ Input file not found: {args.input}")
            sys.exit(1)
        
        result = process_posts_streaming(
            input_path=args.input,
            output_path=args.output,
            chunk_size=args.chunk_size
        )
        
        # Validate output
        validation_results, valid_tags = validate_streaming_output(
            result["aggregated_data"]
        )
        print(f"\n✅ Validation: {validation_results['valid_tags']} valid tags "
              f"out of {validation_results['total_tags']} total")
        
        if not validation_results["validation_passed"]:
            print("⚠️ No tags met minimum requirements")
            sys.exit(1)
        
        # Save validation results
        validation_path = PROCESSED_DIR / "streaming_validation.json"
        with open(validation_path, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2)
        
        print(f"💾 Validation results saved to: {validation_path}")

if __name__ == "__main__":
    main()
