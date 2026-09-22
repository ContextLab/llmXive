import ast
import json
import re
import sys
import os
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator

from src.utils.resource_monitor import ResourceMonitor

# --- Existing API Surface (Preserved) ---

def calculate_syntax_tree_depth(code_snippet: str) -> int:
    """
    Calculate the maximum depth of the AST for a given code snippet.
    Returns 0 if parsing fails or snippet is empty.
    """
    if not code_snippet or not isinstance(code_snippet, str):
        return 0
    try:
        tree = ast.parse(code_snippet)
        return _get_depth(tree)
    except SyntaxError:
        return 0

def _get_depth(node: ast.AST) -> int:
    """Helper to recursively calculate AST depth."""
    if not hasattr(node, '_fields'):
        return 1
    max_child_depth = 0
    for field, value in ast.iter_fields(node):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, ast.AST):
                    max_child_depth = max(max_child_depth, _get_depth(item))
        elif isinstance(value, ast.AST):
            max_child_depth = max(max_child_depth, _get_depth(value))
    return 1 + max_child_depth

def calculate_token_frequency(code_snippet: str) -> Dict[str, int]:
    """
    Calculate token frequency distribution for a code snippet.
    Uses a simple regex-based tokenizer for demonstration.
    """
    if not code_snippet:
        return {}
    # Simple tokenization: split by non-alphanumeric, keep words
    tokens = re.findall(r'\b\w+\b', code_snippet.lower())
    return dict(Counter(tokens))

def detect_pragmatic_markers(code_snippet: str) -> List[str]:
    """
    Detect pragmatic markers such as error recovery attempts,
    state transitions, or specific comments indicating logic flow.
    """
    markers = []
    if not code_snippet:
        return markers

    # Patterns for pragmatic markers
    patterns = {
        'error_recovery': r'except\s+.*:|try:|finally:|recovery|fallback',
        'state_transition': r'state\s*=\s*|switch\s*\(|case\s*',
        'comment_flow': r'#\s*(TODO|FIXME|NOTE|HACK|BUG)',
        'loop_control': r'break\s*:|continue\s*:|pass\s*:|return\s*None'
    }

    for marker_type, pattern in patterns.items():
        if re.search(pattern, code_snippet, re.IGNORECASE):
            markers.append(marker_type)

    return markers

def extract_features_from_log(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract features from a single log entry.
    Expected log_entry keys: 'code', 'status', 'raw_text' (optional)
    """
    code = log_entry.get('code', '')
    status = log_entry.get('status', 'unknown')

    features = {
        'syntax_depth': calculate_syntax_tree_depth(code),
        'token_freq': calculate_token_frequency(code),
        'pragmatic_markers': detect_pragmatic_markers(code),
        'status': status,
        'raw_text_length': len(log_entry.get('raw_text', ''))
    }

    # Flatten token_freq for potential downstream use
    # (Keeping as dict in this version as per generic structure)
    return features

# --- New Implementation for T016: Generator-based Streaming Parser ---

def process_logs_streaming(
    input_path: str,
    output_path: str,
    chunk_size: int = 1000
) -> Iterator[Dict[str, Any]]:
    """
    Generator-based log parser that yields chunks of processed features.
    Reads raw logs line-by-line to prevent memory overflow on large files.
    Yields dictionaries containing a list of processed features (a chunk).

    Args:
        input_path: Path to the raw JSONL log file.
        output_path: Path to write the processed JSONL features file.
        chunk_size: Number of log entries to process before yielding a chunk.

    Yields:
        Dict containing 'chunk_id' and 'features' (list of feature dicts).
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input log file not found: {input_path}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Initialize Resource Monitor to track peak RSS
    monitor = ResourceMonitor()
    monitor.start()

    chunk = []
    chunk_id = 0
    processed_count = 0

    # Open output file in append mode to write chunks as they are processed
    with open(output_file, 'w', encoding='utf-8') as f_out:
        try:
            with open(input_file, 'r', encoding='utf-8') as f_in:
                for line_num, line in enumerate(f_in):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        log_entry = json.loads(line)
                        features = extract_features_from_log(log_entry)
                        chunk.append(features)
                        processed_count += 1

                        if len(chunk) >= chunk_size:
                            chunk_id += 1
                            chunk_data = {
                                'chunk_id': chunk_id,
                                'features': chunk,
                                'count': len(chunk)
                            }
                            # Write chunk to output file immediately
                            f_out.write(json.dumps(chunk_data) + '\n')
                            # Yield the chunk for external processing/monitoring
                            yield chunk_data
                            chunk = []
                    except json.JSONDecodeError as e:
                        # Log error but continue processing
                        sys.stderr.write(f"Warning: Skipping malformed line {line_num}: {e}\n")
                        continue

        except IOError as e:
            monitor.stop()
            raise RuntimeError(f"Failed to read input file {input_path}: {e}") from e

    # Yield any remaining items in the last chunk
    if chunk:
        chunk_id += 1
        chunk_data = {
            'chunk_id': chunk_id,
            'features': chunk,
            'count': len(chunk)
        }
        f_out.write(json.dumps(chunk_data) + '\n')
        yield chunk_data

    monitor.stop()
    peak_rss = monitor.get_peak_rss_mb()
    sys.stderr.write(f"Processing complete. Total entries: {processed_count}, Peak RSS: {peak_rss:.2f} MB\n")

    # Verify peak RSS constraint (7GB = 7168 MB)
    if peak_rss > 7168:
        raise MemoryError(f"Peak RSS {peak_rss:.2f} MB exceeded 7GB limit.")

def main():
    """
    Main entry point for the streaming log parser.
    Expects input_path and output_path as command line arguments or defaults.
    """
    # Default paths based on project structure
    default_input = "data/raw/enterprise_claw_bench.jsonl"
    default_output = "data/processed/features.jsonl"

    input_path = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_path = sys.argv[2] if len(sys.argv) > 2 else default_output

    print(f"Starting streaming extraction from {input_path} to {output_path}...")

    try:
        for chunk_data in process_logs_streaming(input_path, output_path):
            print(f"Processed chunk {chunk_data['chunk_id']} with {chunk_data['count']} entries.")
        print("Extraction completed successfully.")
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()