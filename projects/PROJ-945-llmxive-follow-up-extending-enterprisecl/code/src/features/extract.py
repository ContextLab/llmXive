"""
Feature extraction module for EnterpriseClawBench logs.
Implements syntax tree depth calculation, token frequency, and pragmatic markers.
"""
import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator

import networkx as nx

# Pragmatic marker patterns (error recovery, state transitions)
PRAGMATIC_PATTERNS = [
    r'\bretry\b',
    r'\bfallback\b',
    r'\bstate\s*transit(ion)?\b',
    r'\berror\s*recovery\b',
    r'\bexception\s*caught\b',
    r'\brollback\b',
    r'\bcompensat(e|ion)?\b',
    r'\brecover\b',
    r'\brestart\b',
]

def calculate_syntax_tree_depth(code_snippet: str) -> int:
    """
    Calculate the maximum depth of the syntax tree for a given code snippet.
    Uses Python's AST module and NetworkX to build and traverse the tree.
    
    Args:
        code_snippet: The code string to analyze.
        
    Returns:
        int: The maximum depth of the syntax tree. Returns 0 if parsing fails.
    """
    if not code_snippet or not code_snippet.strip():
        return 0
    
    try:
        tree = ast.parse(code_snippet)
    except SyntaxError:
        # If the snippet is not valid Python, try to parse as a minimal expression
        # or return 0 to indicate failure to parse.
        return 0

    # Build a graph representation of the AST
    G = nx.DiGraph()
    G.add_node(0, type=tree.__class__.__name__)
    
    def add_nodes(node, parent_id, depth=0):
        node_id = id(node)
        # Ensure unique IDs for nodes if they are reused (though AST nodes are usually unique)
        # We use a counter or the object id. Since object id is unique per run, it's fine.
        G.add_node(node_id, type=node.__class__.__name__, depth=depth)
        if parent_id is not None:
            G.add_edge(parent_id, node_id)
        
        max_child_depth = depth
        for child in ast.iter_child_nodes(node):
            child_depth = add_nodes(child, node_id, depth + 1)
            if child_depth > max_child_depth:
                max_child_depth = child_depth
        return max_child_depth

    # Root node ID is 0 (arbitrary mapping for the root)
    # We need to map the actual root object to our graph ID
    root_id = id(tree)
    G = nx.DiGraph()
    G.add_node(root_id, type=tree.__class__.__name__, depth=0)
    
    def build_graph(node, parent_node_id):
        current_id = id(node)
        if parent_node_id is not None:
            G.add_edge(parent_node_id, current_id)
        
        max_depth = 0
        for child in ast.iter_child_nodes(node):
            child_max = build_graph(child, current_id)
            if child_max + 1 > max_depth:
                max_depth = child_max + 1
        return max_depth

    if tree:
        return build_graph(tree, None) + 1 # +1 because root is depth 1 usually, or 0 if empty
    return 0

def calculate_token_frequency(code_snippet: str) -> Dict[str, int]:
    """
    Calculate the frequency distribution of tokens in the code snippet.
    
    Args:
        code_snippet: The code string to analyze.
        
    Returns:
        Dict[str, int]: A dictionary mapping token strings to their counts.
    """
    if not code_snippet:
        return {}
    
    # Simple tokenization: split by whitespace and punctuation, filter empty
    # In a real scenario, use `tokenize` module for accurate Python tokenization
    tokens = re.findall(r'\w+|[^\s\w]', code_snippet)
    tokens = [t.lower() for t in tokens if t.strip()]
    return dict(Counter(tokens))

def detect_pragmatic_markers(log_text: str) -> List[str]:
    """
    Detect pragmatic markers indicating error recovery or state transitions.
    
    Args:
        log_text: The log text to analyze.
        
    Returns:
        List[str]: A list of detected pragmatic markers found in the text.
    """
    if not log_text:
        return []
    
    found_markers = []
    text_lower = log_text.lower()
    
    for pattern in PRAGMATIC_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            # Extract the matched string itself for reporting
            full_matches = re.findall(pattern, text_lower, re.IGNORECASE)
            found_markers.extend(full_matches)
    
    return list(set(found_markers))

def extract_features_from_log(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract a feature vector from a single log entry.
    
    Args:
        log_entry: A dictionary containing log data, expected to have 'code' and 'log_text' keys.
        
    Returns:
        Dict[str, Any]: A dictionary containing the extracted features.
    """
    code = log_entry.get('code', '')
    log_text = log_entry.get('log_text', '')
    status = log_entry.get('status', 'unknown')
    
    syntax_depth = calculate_syntax_tree_depth(code)
    token_freq = calculate_token_frequency(code)
    pragmatic_markers = detect_pragmatic_markers(log_text)
    
    return {
        'syntax_tree_depth': syntax_depth,
        'token_frequency': token_freq,
        'pragmatic_markers': pragmatic_markers,
        'status': status,
        'original_entry': log_entry # Keep reference if needed
    }

def process_logs_streaming(logs_path: Path, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
    """
    Generator that processes logs in chunks to prevent memory overflow.
    
    Args:
        logs_path: Path to the raw logs file (JSONL or JSON).
        chunk_size: Number of entries to process per chunk.
        
    Yields:
        List[Dict[str, Any]]: A list of processed log entries with features.
    """
    if not logs_path.exists():
        raise FileNotFoundError(f"Log file not found: {logs_path}")
    
    # Determine file format
    entries = []
    with open(logs_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
    if content.startswith('['):
        # JSON array
        try:
            all_logs = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in log file.")
    else:
        # JSONL
        all_logs = []
        for line in content.split('\n'):
            if line.strip():
                all_logs.append(json.loads(line))
    
    for i in range(0, len(all_logs), chunk_size):
        chunk = all_logs[i:i+chunk_size]
        processed_chunk = [extract_features_from_log(entry) for entry in chunk]
        yield processed_chunk

def main():
    """
    Main entry point for feature extraction.
    Reads raw logs, extracts features, and saves to processed output.
    """
    import sys
    
    # Default paths
    input_path = Path("data/raw/enterprise_claw_bench.jsonl")
    output_path = Path("data/processed/features.jsonl")
    
    # Allow override via command line
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
        
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        sys.exit(1)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing logs from {input_path}...")
    processed_count = 0
    
    with open(output_path, 'w', encoding='utf-8') as out_f:
        for chunk in process_logs_streaming(input_path):
            for entry in chunk:
                out_f.write(json.dumps(entry) + '\n')
                processed_count += 1
                
    print(f"Successfully extracted features for {processed_count} entries.")
    print(f"Output saved to {output_path}")

if __name__ == "__main__":
    main()