"""
Metric Extraction Module (T020, T021)

Implements extraction of:
- Radon metrics: Cyclomatic Complexity, LOC, Maintainability Index
- Pylint metrics: Bug indicators, style issues

Outputs are written to data/metrics/ as CSVs conforming to MetricResult schema.
"""
import os
import sys
import logging
import ast
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict, dataclass
from datetime import datetime

# Radon imports
try:
    from radon.complexity import cc_visit
    from radon.raw import analyze as radon_analyze_raw
    from radon.mi import mi_visit
except ImportError:
    raise ImportError(
        "ERROR: radon library is not installed. Please install it via pip install radon."
    )

# Pylint imports
try:
    from pylint.lint import Run
    from pylint.reporters.text import TextReporter
    from pylint.checkers import BaseChecker
except ImportError:
    raise ImportError(
        "ERROR: pylint library is not installed. Please install it via pip install pylint."
    )

from data_model import MetricResult
from logging_config import get_logger
from state_tracker import update_state_with_artifact
from cpu_guard import enforce_cpu_only

# Ensure we are on CPU only (T025)
enforce_cpu_only()

logger = get_logger(__name__)

@dataclass
class RadonMetrics:
    """Container for Radon analysis results."""
    snippet_id: str
    cyclomatic_complexity: float
    loc: int
    maintainability_index: float
    source: str
    
@dataclass
class PylintMetrics:
    """Container for Pylint analysis results."""
    snippet_id: str
    bug_count: int
    style_count: int
    convention_count: int
    refactoring_count: int
    total_issue_count: int
    source: str
    
def extract_radon_metrics(code_snippet: str, snippet_id: str) -> Optional[RadonMetrics]:
    """
    Extracts cyclomatic complexity, LOC, and maintainability index from a code snippet.
    
    Args:
        code_snippet: The Python code string.
        snippet_id: Unique identifier for the snippet.
        
    Returns:
        RadonMetrics object or None if parsing fails.
    """
    if not code_snippet or not code_snippet.strip():
        logger.warning(f"Empty snippet for ID {snippet_id}, skipping radon analysis.")
        return None
        
    try:
        # 1. Cyclomatic Complexity (CC)
        # cc_visit returns a list of complexity results for each function/class
        complexity_results = cc_visit(code_snippet)
        if not complexity_results:
            # If no functions/classes found, treat as 1 (single block) or 0? 
            # Standard is often 1 for the module itself if empty, but let's use 1 for safety if no functions
            total_cc = 1 
        else:
            # Sum of complexities of all functions/classes found
            total_cc = sum(res.complexity for res in complexity_results)
        
        # 2. Raw Metrics (LOC, etc.)
        raw_results = radon_analyze_raw(code_snippet)
        loc = raw_results.loc
        
        # 3. Maintainability Index (MI)
        # mi_visit returns a list of MI values for each function/class
        mi_results = mi_visit(code_snippet, multi=True)
        if not mi_results:
            # If no functions, calculate for the whole module? 
            # mi_visit without args calculates for the whole file if passed as string
            mi_results = mi_visit(code_snippet, multi=False)
            mi = mi_results if mi_results else 0.0
        else:
            # Average MI of all functions/classes
            mi = sum(mi_results) / len(mi_results) if mi_results else 0.0
            
        # Ensure MI is within valid range (0-171 usually, but can be negative for very complex code)
        # We clamp to a reasonable range for visualization if needed, but store raw
        
        return RadonMetrics(
            snippet_id=snippet_id,
            cyclomatic_complexity=float(total_cc),
            loc=int(loc),
            maintainability_index=float(mi),
            source="radon"
        )
    except SyntaxError as e:
        logger.error(f"SyntaxError in radon analysis for {snippet_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in radon analysis for {snippet_id}: {e}")
        return None

def extract_pylint_metrics(code_snippet: str, snippet_id: str) -> Optional[PylintMetrics]:
    """
    Extracts bug indicators and style issues from a code snippet using Pylint.
    
    Args:
        code_snippet: The Python code string.
        snippet_id: Unique identifier for the snippet.
        
    Returns:
        PylintMetrics object or None if analysis fails.
    """
    if not code_snippet or not code_snippet.strip():
        logger.warning(f"Empty snippet for ID {snippet_id}, skipping pylint analysis.")
        return None
        
    try:
        # Create a temporary file for pylint to analyze
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code_snippet)
            tmp_path = tmp_file.name
        
        try:
            # Run pylint
            # We capture output in a TextReporter
            reporter = TextReporter()
            # Disable specific checks that might be noisy or irrelevant for snippets (e.g., missing docstring)
            # But we want bug and style checks
            # --disable=all --enable=bugger,style,convention,refactoring
            # Actually, let's just run standard and count by message type
            
            # We need to parse the output to count issues
            # Using Run with reporter
            Run(
                [tmp_path, '--disable=all', '--enable=bugger,style,convention,refactoring,error,warning', '--output-format=text'],
                reporter=reporter,
                exit=False
            )
            
            output = reporter.out.getvalue()
            
            # Parse output to count categories
            # Format: filename:line:col: [message_type] message
            bug_count = 0
            style_count = 0
            convention_count = 0
            refactoring_count = 0
            
            for line in output.splitlines():
                if 'bugger' in line.lower() or 'error' in line.lower():
                    # Pylint 'bug' messages are often categorized under 'bugger' or specific error codes
                    # We'll count lines that indicate a bug or error
                    if 'bugger' in line.lower():
                        bug_count += 1
                    elif 'error' in line.lower() and 'bugger' not in line.lower():
                        # Sometimes errors are separate
                        # Let's be conservative: only count explicit bugger or specific error codes if we can parse them
                        # For now, let's rely on the message type if available
                        pass
                elif 'style' in line.lower():
                    style_count += 1
                elif 'convention' in line.lower():
                    convention_count += 1
                elif 'refactor' in line.lower():
                    refactoring_count += 1
                    
                # A more robust way is to check the message type in the output if available
                # But standard text output is hard to parse reliably without a structured reporter.
                # Let's use a simpler heuristic based on the message type string if present.
                # Re-running with a custom approach:
                pass
                
            # Since parsing text output is brittle, let's try a different approach:
            # Use the Message object if we can access the internal state, but that's private.
            # Let's stick to the text parsing but be more specific about the prefix.
            # Pylint output: "filename:line: [type] message"
            
            # Reset and parse again more carefully
            bug_count = 0
            style_count = 0
            convention_count = 0
            refactoring_count = 0
            
            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Look for the pattern [type]
                if '[bugger]' in line.lower():
                    bug_count += 1
                elif '[style]' in line.lower():
                    style_count += 1
                elif '[convention]' in line.lower():
                    convention_count += 1
                elif '[refactor]' in line.lower():
                    refactoring_count += 1
                # Sometimes errors are [error] or [fatal]
                elif '[error]' in line.lower():
                    bug_count += 1 # Treat errors as bugs
                    
            total_issues = bug_count + style_count + convention_count + refactoring_count
            
            return PylintMetrics(
                snippet_id=snippet_id,
                bug_count=bug_count,
                style_count=style_count,
                convention_count=convention_count,
                refactoring_count=refactoring_count,
                total_issue_count=total_issues,
                source="pylint"
            )
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        logger.error(f"Unexpected error in pylint analysis for {snippet_id}: {e}")
        return None

def process_snippets_for_metrics(snippets: List[Dict[str, Any]]) -> Tuple[List[RadonMetrics], List[PylintMetrics]]:
    """
    Processes a list of code snippets and extracts metrics.
    
    Args:
        snippets: List of dicts with keys: 'id', 'code', 'source' (from data_ingestion)
        
    Returns:
        Tuple of (list of RadonMetrics, list of PylintMetrics)
    """
    radon_results = []
    pylint_results = []
    
    logger.info(f"Starting metric extraction for {len(snippets)} snippets.")
    
    for i, snippet in enumerate(snippets):
        snippet_id = snippet.get('id')
        code = snippet.get('code')
        source = snippet.get('source', 'unknown')
        
        if not snippet_id or not code:
            logger.warning(f"Skipping snippet {i}: missing id or code.")
            continue
            
        # Radon
        radon_metric = extract_radon_metrics(code, snippet_id)
        if radon_metric:
            radon_results.append(radon_metric)
            
        # Pylint
        pylint_metric = extract_pylint_metrics(code, snippet_id)
        if pylint_metric:
            pylint_results.append(pylint_metric)
            
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i+1}/{len(snippets)} snippets.")
            
    logger.info(f"Extraction complete. Radon: {len(radon_results)}, Pylint: {len(pylint_results)}")
    return radon_results, pylint_results

def write_metrics_to_csv(radon_metrics: List[RadonMetrics], pylint_metrics: List[PylintMetrics], output_dir: Path):
    """
    Writes extracted metrics to CSV files in the specified output directory.
    
    Args:
        radon_metrics: List of RadonMetrics objects.
        pylint_metrics: List of PylintMetrics objects.
        output_dir: Directory to write CSV files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write Radon metrics
    if radon_metrics:
        radon_path = output_dir / "radon_metrics.csv"
        with open(radon_path, 'w') as f:
            f.write("snippet_id,cyclomatic_complexity,loc,maintainability_index,source\n")
            for m in radon_metrics:
                f.write(f"{m.snippet_id},{m.cyclomatic_complexity},{m.loc},{m.maintainability_index},{m.source}\n")
        logger.info(f"Radon metrics written to {radon_path}")
        
        # Update state
        update_state_with_artifact(str(radon_path), "radon_metrics")
    else:
        logger.warning("No Radon metrics to write.")
        
    # Write Pylint metrics
    if pylint_metrics:
        pylint_path = output_dir / "pylint_metrics.csv"
        with open(pylint_path, 'w') as f:
            f.write("snippet_id,bug_count,style_count,convention_count,refactoring_count,total_issue_count,source\n")
            for m in pylint_metrics:
                f.write(f"{m.snippet_id},{m.bug_count},{m.style_count},{m.convention_count},{m.refactoring_count},{m.total_issue_count},{m.source}\n")
        logger.info(f"Pylint metrics written to {pylint_path}")
        
        # Update state
        update_state_with_artifact(str(pylint_path), "pylint_metrics")
    else:
        logger.warning("No Pylint metrics to write.")

def run_metric_extraction(input_path: str, output_dir: str):
    """
    Main entry point for running metric extraction.
    
    Args:
        input_path: Path to the processed snippets JSON file.
        output_dir: Path to the output directory for CSVs.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    logger.info(f"Loading snippets from {input_path}")
    with open(input_path, 'r') as f:
        snippets = json.load(f)
        
    if not isinstance(snippets, list):
        raise ValueError("Input JSON must be a list of snippets.")
        
    radon_metrics, pylint_metrics = process_snippets_for_metrics(snippets)
    write_metrics_to_csv(radon_metrics, pylint_metrics, output_dir)

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract metrics from code snippets.")
    parser.add_argument("--input", type=str, default="data/processed/processed_snippets.json",
                        help="Path to processed snippets JSON.")
    parser.add_argument("--output", type=str, default="data/metrics",
                        help="Path to output directory.")
                        
    args = parser.parse_args()
    
    run_metric_extraction(args.input, args.output)

if __name__ == "__main__":
    main()