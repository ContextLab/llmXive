"""
Log parser for EnterpriseClawBench.

Reads raw logs from data/raw/, parses them, and extracts features.
Implements generator-based parsing to handle large files without memory overflow.
"""

import json
import os
import re
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List

from ..config import get_config

# Constants for pragmatic marker detection
ERROR_RECOVERY_PATTERNS = [
    r'retry', r'recover', r'fallback', r'exception.*handled',
    r'caught.*error', r'rollback', r'compensate', r'undo'
]

STATE_TRANSITION_PATTERNS = [
    r'state.*changed', r'transition.*to', r'enter.*state',
    r'exit.*state', r'current.*state', r'state.*update'
]

CHUNK_SIZE = 1024 * 1024  # 1MB chunks


def load_raw_logs(data_dir: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields parsed log entries from raw log files.
    
    Args:
        data_dir: Path to data/raw directory. If None, uses config.
        
    Yields:
        Dict with 'log_id', 'content', 'status' (success/failure), and raw text.
        
    Raises:
        FileNotFoundError: If no log files found in data_dir.
        ValueError: If log format is invalid.
    """
    config = get_config()
    raw_dir = Path(data_dir) if data_dir else Path(config['paths']['raw_data'])
    
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
        
    log_files = list(raw_dir.glob("*.log")) + list(raw_dir.glob("*.jsonl"))
    
    if not log_files:
        raise FileNotFoundError(f"No log files found in {raw_dir}")
        
    for log_file in log_files:
        log_id = log_file.stem
        
        if log_file.suffix == '.jsonl':
            yield from _parse_jsonl_log(log_file, log_id)
        else:
            yield from _parse_text_log(log_file, log_id)

def _parse_jsonl_log(file_path: Path, log_id: str) -> Generator[Dict[str, Any], None, None]:
    """Parse JSONL log file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                entry = json.loads(line)
                # Ensure required fields
                if 'content' not in entry:
                    raise ValueError(f"Missing 'content' field at line {line_num}")
                
                # Infer status if not present
                status = entry.get('status', 'unknown')
                if status not in ['success', 'failure', 'unknown']:
                    # Heuristic: check for error keywords
                    content_lower = entry['content'].lower()
                    if any(kw in content_lower for kw in ['error', 'fail', 'exception', 'traceback']):
                        status = 'failure'
                    elif any(kw in content_lower for kw in ['success', 'completed', 'done']):
                        status = 'success'
                
                yield {
                    'log_id': f"{log_id}_{line_num}",
                    'content': entry['content'],
                    'status': status,
                    'metadata': entry.get('metadata', {})
                }
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num}: {e}")

def _parse_text_log(file_path: Path, log_id: str) -> Generator[Dict[str, Any], None, None]:
    """Parse text log file, yielding chunks as individual entries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        # Try to detect entry boundaries
        # Common patterns: timestamp-based, log level-based
        entry_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[^\n]*)\n',
            re.MULTILINE
        )
        
        content = f.read()
        entries = entry_pattern.split(content)
        
        # Process pairs (timestamp, content)
        for i in range(0, len(entries) - 1, 2):
            timestamp = entries[i].strip()
            entry_content = entries[i + 1].strip()
            
            if not entry_content:
                continue
                
            # Infer status
            entry_lower = entry_content.lower()
            if any(kw in entry_lower for kw in ['error', 'fail', 'exception', 'traceback']):
                status = 'failure'
            elif any(kw in entry_lower for kw in ['success', 'completed', 'done']):
                status = 'success'
            else:
                status = 'unknown'
            
            yield {
                'log_id': f"{log_id}_{i//2}",
                'content': entry_content,
                'status': status,
                'metadata': {'timestamp': timestamp} if timestamp else {}
            }

def extract_features(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract features from a single log entry.
    
    Args:
        log_entry: Parsed log entry with 'content' and 'status'.
        
    Returns:
        Dict with extracted features.
    """
    content = log_entry['content']
    
    features = {
        'log_id': log_entry['log_id'],
        'status': log_entry['status'],
        'syntax_tree_depth': calculate_syntax_tree_depth(content),
        'token_frequency': calculate_token_frequency(content),
        'pragmatic_markers': detect_pragmatic_markers(content),
        'length': len(content),
        'line_count': content.count('\n') + 1
    }
    
    return features

def calculate_syntax_tree_depth(content: str) -> int:
    """
    Calculate approximate syntax tree depth based on indentation and brackets.
    
    Args:
        content: Log content string.
        
    Returns:
        Integer representing estimated tree depth.
    """
    if not content:
        return 0
        
    max_depth = 0
    current_depth = 0
    
    for line in content.split('\n'):
        # Count indentation (spaces or tabs)
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        
        # Estimate depth from indentation (assuming 4 spaces per level)
        indent_depth = indent // 4
        max_depth = max(max_depth, indent_depth)
        
        # Count bracket nesting
        for char in stripped:
            if char in '({[':
                current_depth += 1
            elif char in ')}]':
                current_depth = max(0, current_depth - 1)
        
        max_depth = max(max_depth, current_depth)
    
    return max_depth

def calculate_token_frequency(content: str) -> Dict[str, int]:
    """
    Calculate token frequency distribution.
    
    Args:
        content: Log content string.
        
    Returns:
        Dict mapping tokens to their frequencies.
    """
    if not content:
        return {}
        
    # Simple tokenization: split on whitespace and punctuation
    tokens = re.findall(r'\b\w+\b', content.lower())
    
    frequency = {}
    for token in tokens:
        frequency[token] = frequency.get(token, 0) + 1
        
    return frequency

def detect_pragmatic_markers(content: str) -> Dict[str, bool]:
    """
    Detect pragmatic markers indicating error recovery and state transitions.
    
    Args:
        content: Log content string.
        
    Returns:
        Dict with boolean flags for different marker types.
    """
    content_lower = content.lower()
    
    markers = {
        'error_recovery': False,
        'state_transition': False,
        'retry_attempt': False,
        'exception_handled': False
    }
    
    # Check for error recovery patterns
    for pattern in ERROR_RECOVERY_PATTERNS:
        if re.search(pattern, content_lower):
            markers['error_recovery'] = True
            break
    
    # Check for state transition patterns
    for pattern in STATE_TRANSITION_PATTERNS:
        if re.search(pattern, content_lower):
            markers['state_transition'] = True
            break
    
    # Specific checks
    if re.search(r'retry.*\d+', content_lower) or 'retry attempt' in content_lower:
        markers['retry_attempt'] = True
        
    if 'exception' in content_lower and ('handled' in content_lower or 'caught' in content_lower):
        markers['exception_handled'] = True
    
    return markers

def extract_all_features(data_dir: Optional[str] = None, output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract features from all raw logs and optionally save to file.
    
    Args:
        data_dir: Path to data/raw directory.
        output_path: Optional path to save features as JSONL.
        
    Returns:
        List of feature dictionaries.
    """
    features = []
    
    for log_entry in load_raw_logs(data_dir):
        feature_vector = extract_features(log_entry)
        features.append(feature_vector)
        
        # Optional: write incrementally to avoid memory buildup
        if output_path:
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(feature_vector) + '\n')
    
    return features

def main():
    """Main entry point for log feature extraction."""
    import sys
    
    config = get_config()
    raw_dir = Path(config['paths']['raw_data'])
    output_path = Path(config['paths']['processed_data']) / 'features.jsonl'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear existing output file
    if output_path.exists():
        output_path.unlink()
    
    print(f"Extracting features from {raw_dir}...")
    
    try:
        feature_count = 0
        for log_entry in load_raw_logs(str(raw_dir)):
            feature_vector = extract_features(log_entry)
            
            # Write incrementally
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(feature_vector) + '\n')
            
            feature_count += 1
            
            if feature_count % 100 == 0:
                print(f"Processed {feature_count} entries...")
        
        print(f"Successfully extracted features for {feature_count} log entries.")
        print(f"Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error during feature extraction: {e}", file=sys.stderr)
        raise

if __name__ == '__main__':
    main()