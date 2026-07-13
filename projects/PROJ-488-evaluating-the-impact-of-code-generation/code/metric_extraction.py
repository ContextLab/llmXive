import os
import json
import logging
import ast
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import radon.complexity
import radon.metrics
from radon.complexity import cc_visit
from radon.metrics import h_visit
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from io import StringIO
import sys

from logging_config import setup_logger, get_logger
from data_model import MetricResult

# Initialize logger
logger = get_logger(__name__)

def extract_radon_metrics(code: str, snippet_id: str) -> Dict[str, Any]:
    """
    Extract radon metrics (cyclomatic complexity, LOC, maintainability index) for a code snippet.
    
    Args:
        code: The source code string to analyze.
        snippet_id: The unique identifier for the snippet.
        
    Returns:
        Dictionary containing radon metrics.
    """
    try:
        # Cyclomatic Complexity
        complexity_results = cc_visit(code)
        cc_values = [r.complexity for r in complexity_results]
        max_cc = max(cc_values) if cc_values else 0
        avg_cc = sum(cc_values) / len(cc_values) if cc_values else 0.0
        
        # Halstead Metrics
        halstead_results = h_visit(code)
        h_metrics = halstead_results[0] if halstead_results else None
        
        # Maintainability Index (radon calculates this based on lines, complexity, etc.)
        # Note: radon doesn't have a direct "maintainability index" function in newer versions,
        # but we can approximate or use raw metrics.
        # We'll calculate lines of code (LOC)
        lines = code.splitlines()
        loc = len(lines)
        non_empty_loc = len([l for l in lines if l.strip()])
        
        # Calculate Maintainability Index (approximation)
        # MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(LOC)
        # Where V is Halstead Volume, G is Cyclomatic Complexity, LOC is lines of code
        # This is a simplified version. Radon's raw metrics are often used directly.
        # We will store the raw metrics and let downstream handle MI if needed.
        
        metrics = {
            "snippet_id": snippet_id,
            "max_cc": max_cc,
            "avg_cc": avg_cc,
            "num_functions": len(cc_values),
            "loc": loc,
            "non_empty_loc": non_empty_loc,
            "halstead_volume": h_metrics.volume if h_metrics else 0.0,
            "halstead_difficulty": h_metrics.difficulty if h_metrics else 0.0,
            "halstead_effort": h_metrics.effort if h_metrics else 0.0,
        }
        
        return metrics
    except Exception as e:
        logger.error(f"Error extracting radon metrics for {snippet_id}: {e}")
        return {
            "snippet_id": snippet_id,
            "max_cc": None,
            "avg_cc": None,
            "num_functions": 0,
            "loc": 0,
            "non_empty_loc": 0,
            "halstead_volume": None,
            "halstead_difficulty": None,
            "halstead_effort": None,
            "error": str(e)
        }

def extract_pylint_metrics(code: str, snippet_id: str) -> Dict[str, Any]:
    """
    Extract pylint bug-indicator metrics (potential bugs, style issues, convention violations)
    for a code snippet.
    
    Args:
        code: The source code string to analyze.
        snippet_id: The unique identifier for the snippet.
        
    Returns:
        Dictionary containing pylint metrics categorized by type.
    """
    try:
        # Create a temporary file to run pylint on
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code)
            tmp_path = tmp_file.name
        
        try:
            # Configure pylint to run without loading any config files
            # and capture output in memory
            output_buffer = StringIO()
            reporter = TextReporter(output_buffer)
            
            # Run pylint with specific options
            # --disable=all to disable all checks first, then enable only the ones we care about?
            # No, we want to run all and then filter. Or enable specific ones.
            # Let's run with default checks but capture all messages.
            # We'll filter for 'bug', 'warning', 'error', 'convention' related issues.
            
            # To avoid side effects, we create a minimal argv
            old_argv = sys.argv
            sys.argv = ['pylint', tmp_path, '--output-format=text', '--reports=no', '--score=no']
            
            try:
                # Run pylint
                # We need to catch SystemExit if pylint exits with a code
                try:
                    Run(sys.argv[1:], reporter=reporter, exit=False)
                except SystemExit:
                    pass # Pylint might call sys.exit
                
                output = output_buffer.getvalue()
                
            finally:
                sys.argv = old_argv
            
            # Parse the output
            # Pylint output format: filename:line:col: [message_type] message (symbol)
            # Example: /tmp/tmp123.py:10:0: [W0612(unused-variable), ] Unused variable 'x'
            
            messages = []
            lines = output.splitlines()
            
            for line in lines:
                if not line.strip():
                    continue
                # Basic parsing of pylint output
                # We look for message types: E (Error), W (Warning), C (Convention), R (Refactor)
                # We are interested in potential bugs (often E or W) and style issues (C, R)
                
                # Simple heuristic: check for common symbols or message types
                # A more robust way would be to use pylint's message checker, but that's complex.
                # We'll parse the text output.
                
                parts = line.split(':')
                if len(parts) >= 4:
                    # Try to extract message type
                    # Format: file:line:col: [type(symbol)] message
                    # Or: file:line:col: type(symbol): message
                    msg_part = ':'.join(parts[3:])
                    if '[' in msg_part and ']' in msg_part:
                        bracket_content = msg_part[msg_part.find('[')+1:msg_part.find(']')]
                        msg_type_code = bracket_content.split(',')[0].strip() # e.g. 'W0612'
                        symbol = bracket_content.split(',')[-1].strip() if ',' in bracket_content else ''
                        
                        # Determine category
                        category = "unknown"
                        if msg_type_code.startswith('E'):
                            category = "potential_bug"
                        elif msg_type_code.startswith('W'):
                            category = "potential_bug" # Warnings often indicate bugs
                        elif msg_type_code.startswith('C'):
                            category = "style_issue"
                        elif msg_type_code.startswith('R'):
                            category = "style_issue" # Refactor suggestions
                        
                        messages.append({
                            "line": parts[1],
                            "type_code": msg_type_code,
                            "symbol": symbol,
                            "message": msg_part.split(']')[-1].strip() if ']' in msg_part else msg_part,
                            "category": category
                        })
                
            # Aggregate counts
            bug_count = sum(1 for m in messages if m["category"] in ["potential_bug"])
            style_count = sum(1 for m in messages if m["category"] in ["style_issue"])
            total_count = len(messages)
            
            # Extract specific high-priority bug indicators if needed
            # For now, we aggregate by category
            
            metrics = {
                "snippet_id": snippet_id,
                "total_issues": total_count,
                "potential_bugs": bug_count,
                "style_issues": style_count,
                "error_count": sum(1 for m in messages if m["type_code"].startswith('E')),
                "warning_count": sum(1 for m in messages if m["type_code"].startswith('W')),
                "convention_count": sum(1 for m in messages if m["type_code"].startswith('C')),
                "refactor_count": sum(1 for m in messages if m["type_code"].startswith('R')),
            }
            
            return metrics
            
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
                
    except Exception as e:
        logger.error(f"Error extracting pylint metrics for {snippet_id}: {e}")
        return {
            "snippet_id": snippet_id,
            "total_issues": 0,
            "potential_bugs": 0,
            "style_issues": 0,
            "error_count": 0,
            "warning_count": 0,
            "convention_count": 0,
            "refactor_count": 0,
            "error": str(e)
        }

def process_snippets_for_metrics(snippets: List[Dict[str, Any]], group_label: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Process a list of snippets to extract both radon and pylint metrics.
    
    Args:
        snippets: List of snippet dictionaries containing 'id' and 'code'.
        group_label: Label for the dataset group (e.g., 'human', 'llm').
        
    Returns:
        Tuple of (radon_metrics_list, pylint_metrics_list)
    """
    radon_results = []
    pylint_results = []
    
    for snippet in snippets:
        snippet_id = snippet.get('id')
        code = snippet.get('code')
        
        if not snippet_id or not code:
            logger.warning(f"Skipping snippet with missing id or code: {snippet}")
            continue
        
        radon_metrics = extract_radon_metrics(code, snippet_id)
        radon_metrics['group'] = group_label
        radon_results.append(radon_metrics)
        
        pylint_metrics = extract_pylint_metrics(code, snippet_id)
        pylint_metrics['group'] = group_label
        pylint_results.append(pylint_metrics)
        
    return radon_results, pylint_results

def write_metrics_to_csv(metrics: List[Dict], output_path: Path, metric_type: str) -> None:
    """
    Write a list of metrics dictionaries to a CSV file.
    
    Args:
        metrics: List of metric dictionaries.
        output_path: Path to the output CSV file.
        metric_type: Type of metric (e.g., 'radon', 'pylint') for logging.
    """
    if not metrics:
        logger.warning(f"No metrics to write for {metric_type}.")
        return
    
    df = pd.DataFrame(metrics)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(metrics)} {metric_type} metrics to {output_path}")

def run_metric_extraction(
    processed_data_path: Path,
    output_dir: Path,
    human_group: str = "human",
    llm_group: str = "llm"
) -> Dict[str, Path]:
    """
    Main function to run the metric extraction pipeline.
    Loads processed snippets, extracts radon and pylint metrics, and saves to CSV.
    
    Args:
        processed_data_path: Path to the JSON file containing processed snippets.
        output_dir: Directory to save the output CSV files.
        human_group: Label for the human-written group.
        llm_group: Label for the LLM-generated group.
        
    Returns:
        Dictionary mapping metric types to output file paths.
    """
    logger.info(f"Starting metric extraction from {processed_data_path}")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load processed data
    with open(processed_data_path, 'r') as f:
        data = json.load(f)
    
    human_snippets = data.get(human_group, [])
    llm_snippets = data.get(llm_group, [])
    
    logger.info(f"Found {len(human_snippets)} human snippets and {len(llm_snippets)} LLM snippets.")
    
    # Process human snippets
    human_radon, human_pylint = process_snippets_for_metrics(human_snippets, human_group)
    
    # Process LLM snippets
    llm_radon, llm_pylint = process_snippets_for_metrics(llm_snippets, llm_group)
    
    # Combine results
    all_radon = human_radon + llm_radon
    all_pylint = human_pylint + llm_pylint
    
    # Define output paths
    radon_output_path = output_dir / "radon_metrics.csv"
    pylint_output_path = output_dir / "pylint_metrics.csv"
    
    # Write to CSV
    write_metrics_to_csv(all_radon, radon_output_path, "radon")
    write_metrics_to_csv(all_pylint, pylint_output_path, "pylint")
    
    return {
        "radon": radon_output_path,
        "pylint": pylint_output_path
    }

def main():
    """Entry point for the metric extraction script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract metrics from code snippets.")
    parser.add_argument("--input", type=str, required=True, help="Path to processed snippets JSON file.")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to save output CSV files.")
    parser.add_argument("--human-group", type=str, default="human", help="Label for human group.")
    parser.add_argument("--llm-group", type=str, default="llm", help="Label for LLM group.")
    
    args = parser.parse_args()
    
    setup_logger(level=logging.INFO)
    
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    results = run_metric_extraction(
        processed_data_path=input_path,
        output_dir=output_dir,
        human_group=args.human_group,
        llm_group=args.llm_group
    )
    
    logger.info("Metric extraction completed successfully.")
    logger.info(f"Radon metrics: {results['radon']}")
    logger.info(f"Pylint metrics: {results['pylint']}")

if __name__ == "__main__":
    main()
