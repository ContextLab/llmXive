import os
import sys
import logging
import ast
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json

# Radon imports
from radon.complexity import cc_visit
from radon.mi import mi_visit
from radon.visitors import ComplexityVisitor
from radon.raw import RawVisitor

# Pylint imports
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from pylint.checkers import BaseChecker
import io

# Local imports
from data_model import MetricResult
from logging_config import get_logger, setup_logger
from state_tracker import update_state_with_artifact

logger = get_logger(__name__)

def extract_radon_metrics(code_snippet: str, snippet_id: str) -> Dict[str, Any]:
    """
    Extract cyclomatic complexity, LOC, and maintainability index from a code snippet using radon.
    
    Args:
        code_snippet: The source code string
        snippet_id: Unique identifier for the snippet
        
    Returns:
        Dictionary containing:
            - cc_max: Maximum cyclomatic complexity
            - cc_avg: Average cyclomatic complexity
            - cc_total: Total cyclomatic complexity
            - loc: Lines of code
            - mi: Maintainability index
            - snippet_id: The input snippet_id
            - status: 'success' or 'error'
            - error_message: If status is error
    """
    try:
        # Parse for complexity
        raw_visit = RawVisitor(code_snippet)
        raw_visit.visit(ast.parse(code_snippet))
        
        cc_visit_result = cc_visit(code_snippet)
        if cc_visit_result:
            cc_max = max(node.complexity for node in cc_visit_result)
            cc_avg = sum(node.complexity for node in cc_visit_result) / len(cc_visit_result)
            cc_total = sum(node.complexity for node in cc_visit_result)
        else:
            cc_max = 0
            cc_avg = 0.0
            cc_total = 0
        
        # Calculate Maintainability Index
        mi_results = mi_visit(code_snippet, multi=True)
        mi = mi_results[0] if mi_results else 0.0
        
        return {
            'snippet_id': snippet_id,
            'cc_max': cc_max,
            'cc_avg': round(cc_avg, 2),
            'cc_total': cc_total,
            'loc': raw_visit.raw.ncloc,
            'mi': round(mi, 2),
            'status': 'success'
        }
        
    except SyntaxError as e:
        logger.warning(f"Syntax error in snippet {snippet_id}: {e}")
        return {
            'snippet_id': snippet_id,
            'cc_max': None,
            'cc_avg': None,
            'cc_total': None,
            'loc': None,
            'mi': None,
            'status': 'error',
            'error_message': f"SyntaxError: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error processing snippet {snippet_id}: {e}")
        return {
            'snippet_id': snippet_id,
            'cc_max': None,
            'cc_avg': None,
            'cc_total': None,
            'loc': None,
            'mi': None,
            'status': 'error',
            'error_message': str(e)
        }

def extract_pylint_metrics(code_snippet: str, snippet_id: str) -> Dict[str, Any]:
    """
    Extract bug indicators and style issues from a code snippet using pylint.
    
    Args:
        code_snippet: The source code string
        snippet_id: Unique identifier for the snippet
        
    Returns:
        Dictionary containing:
            - bug_count: Number of potential bugs (E-level messages)
            - warning_count: Number of warnings (W-level messages)
            - convention_count: Number of convention violations (C-level messages)
            - refactor_count: Number of refactor suggestions (R-level messages)
            - info_count: Number of info messages (I-level messages)
            - total_issues: Total count of all issues
            - snippet_id: The input snippet_id
            - status: 'success' or 'error'
            - error_message: If status is error
    """
    try:
        # Create a temporary file for pylint
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code_snippet)
            temp_path = f.name
        
        try:
            # Run pylint with text reporter
            output = io.StringIO()
            reporter = TextReporter(output)
            
            # Run pylint with specific options to avoid config file issues
            Run(
                [temp_path, '--disable=all', 
                 '--enable=E,W,C,R,I',
                 '--output-format=text',
                 '--reports=no',
                 '--score=no',
                 '--persistent=no'],
                reporter=reporter,
                exit=False
            )
            
            # Parse the output
            pylint_output = output.getvalue()
            
            # Count issues by type
            bug_count = 0
            warning_count = 0
            convention_count = 0
            refactor_count = 0
            info_count = 0
            
            for line in pylint_output.split('\n'):
                if '[E' in line or '[E' in line:
                    bug_count += 1
                elif '[W' in line:
                    warning_count += 1
                elif '[C' in line:
                    convention_count += 1
                elif '[R' in line:
                    refactor_count += 1
                elif '[I' in line:
                    info_count += 1
            
            return {
                'snippet_id': snippet_id,
                'bug_count': bug_count,
                'warning_count': warning_count,
                'convention_count': convention_count,
                'refactor_count': refactor_count,
                'info_count': info_count,
                'total_issues': bug_count + warning_count + convention_count + refactor_count + info_count,
                'status': 'success'
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error processing snippet {snippet_id} with pylint: {e}")
        return {
            'snippet_id': snippet_id,
            'bug_count': None,
            'warning_count': None,
            'convention_count': None,
            'refactor_count': None,
            'info_count': None,
            'total_issues': None,
            'status': 'error',
            'error_message': str(e)
        }

def process_snippets_for_metrics(snippets: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process a list of code snippets to extract radon and pylint metrics.
    
    Args:
        snippets: List of dictionaries containing 'id' and 'code' keys
        
    Returns:
        Tuple of (radon_metrics_list, pylint_metrics_list)
    """
    radon_metrics = []
    pylint_metrics = []
    
    total = len(snippets)
    processed = 0
    
    for snippet in snippets:
        snippet_id = snippet.get('id', 'unknown')
        code = snippet.get('code', '')
        
        if not code:
            logger.warning(f"Skipping snippet {snippet_id} with empty code")
            continue
        
        # Extract radon metrics
        radon_result = extract_radon_metrics(code, snippet_id)
        radon_metrics.append(radon_result)
        
        # Extract pylint metrics
        pylint_result = extract_pylint_metrics(code, snippet_id)
        pylint_metrics.append(pylint_result)
        
        processed += 1
        if processed % 100 == 0:
            logger.info(f"Processed {processed}/{total} snippets")
    
    logger.info(f"Completed processing {processed} snippets")
    return radon_metrics, pylint_metrics

def write_metrics_to_csv(radon_metrics: List[Dict[str, Any]], pylint_metrics: List[Dict[str, Any]], output_dir: Path):
    """
    Write extracted metrics to CSV files.
    
    Args:
        radon_metrics: List of radon metric dictionaries
        pylint_metrics: List of pylint metric dictionaries
        output_dir: Directory to write output files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write radon metrics
    radon_file = output_dir / 'radon_metrics.csv'
    if radon_metrics:
        import pandas as pd
        df_radon = pd.DataFrame(radon_metrics)
        df_radon.to_csv(radon_file, index=False)
        logger.info(f"Wrote {len(radon_metrics)} radon metrics to {radon_file}")
    else:
        logger.warning("No radon metrics to write")
        # Write empty file with headers to maintain schema
        pd.DataFrame(columns=['snippet_id', 'cc_max', 'cc_avg', 'cc_total', 'loc', 'mi', 'status']).to_csv(radon_file, index=False)
    
    # Write pylint metrics
    pylint_file = output_dir / 'pylint_metrics.csv'
    if pylint_metrics:
        df_pylint = pd.DataFrame(pylint_metrics)
        df_pylint.to_csv(pylint_file, index=False)
        logger.info(f"Wrote {len(pylint_metrics)} pylint metrics to {pylint_file}")
    else:
        logger.warning("No pylint metrics to write")
        # Write empty file with headers to maintain schema
        pd.DataFrame(columns=['snippet_id', 'bug_count', 'warning_count', 'convention_count', 'refactor_count', 'info_count', 'total_issues', 'status']).to_csv(pylint_file, index=False)

def run_metric_extraction(input_file: Path, output_dir: Path):
    """
    Main function to run the metric extraction pipeline.
    
    Args:
        input_file: Path to the JSON file containing processed snippets
        output_dir: Directory to write output metrics
    """
    logger.info(f"Starting metric extraction from {input_file}")
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Load snippets
    with open(input_file, 'r') as f:
        snippets = json.load(f)
    
    logger.info(f"Loaded {len(snippets)} snippets")
    
    if len(snippets) == 0:
        logger.error("No snippets found in input file")
        raise ValueError("No snippets found in input file")
    
    # Process snippets
    radon_metrics, pylint_metrics = process_snippets_for_metrics(snippets)
    
    # Write results
    write_metrics_to_csv(radon_metrics, pylint_metrics, output_dir)
    
    # Update state
    update_state_with_artifact('metric_extraction', str(output_dir))
    
    logger.info("Metric extraction completed successfully")

def main():
    """Entry point for the metric extraction script."""
    # Setup logging
    setup_logger('metric_extraction', level=logging.INFO)
    
    # Define paths
    project_root = Path(__file__).parent.parent
    input_file = project_root / 'data' / 'processed' / 'filtered_snippets.json'
    output_dir = project_root / 'data' / 'metrics'
    
    try:
        run_metric_extraction(input_file, output_dir)
    except Exception as e:
        logger.error(f"Metric extraction failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()