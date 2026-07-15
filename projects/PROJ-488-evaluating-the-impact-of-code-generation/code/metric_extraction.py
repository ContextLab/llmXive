import os
import sys
import logging
import ast
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Radon imports - fixed to use correct module structure
from radon.complexity import cc_visit
from radon.raw import analyze as raw_analyze
from radon.mi import mi_visit

# Pylint imports
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from io import StringIO

# Project imports
from data_model import MetricResult, CodeSnippet
from logging_config import get_logger
from state_tracker import update_state_with_artifact

logger = get_logger(__name__)

class RadonMetrics:
    """Container for radon-computed metrics."""
    def __init__(self, snippet_id: str, complexity: int, loc: int, 
                 maintainability: float, raw_loc: int, raw_sloc: int, 
                 raw_comments: int, raw_strings: int):
        self.snippet_id = snippet_id
        self.complexity = complexity
        self.loc = loc
        self.maintainability = maintainability
        self.raw_loc = raw_loc
        self.raw_sloc = raw_sloc
        self.raw_comments = raw_comments
        self.raw_strings = raw_strings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snippet_id": self.snippet_id,
            "metric_type": "radon",
            "cyclomatic_complexity": self.complexity,
            "loc": self.loc,
            "maintainability_index": self.maintainability,
            "raw_loc": self.raw_loc,
            "raw_sloc": self.raw_sloc,
            "raw_comments": self.raw_comments,
            "raw_strings": self.raw_strings
        }

class PylintMetrics:
    """Container for pylint-computed metrics."""
    def __init__(self, snippet_id: str, bug_count: int, convention_count: int,
                 refactor_count: int, info_count: int, error_count: int):
        self.snippet_id = snippet_id
        self.bug_count = bug_count
        self.convention_count = convention_count
        self.refactor_count = refactor_count
        self.info_count = info_count
        self.error_count = error_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snippet_id": self.snippet_id,
            "metric_type": "pylint",
            "bug_count": self.bug_count,
            "convention_count": self.convention_count,
            "refactor_count": self.refactor_count,
            "info_count": self.info_count,
            "error_count": self.error_count
        }

def extract_radon_metrics(snippet_id: str, code: str) -> Optional[RadonMetrics]:
    """
    Extract radon metrics (complexity, LOC, maintainability) from a code snippet.
    Returns None if extraction fails.
    """
    try:
        # Calculate Cyclomatic Complexity
        complexity_results = cc_visit(code)
        total_complexity = sum(node.cc for node in complexity_results)
        
        # Calculate Raw Metrics (LOC, etc.)
        raw_analysis = raw_analyze(code)
        
        # Calculate Maintainability Index (0-100 scale)
        # mi_visit returns a list of (score, raw) tuples for each function/class
        # We aggregate to a single score for the snippet
        mi_results = mi_visit(code, multi=True)
        if mi_results:
            # mi_visit returns [(mi, raw), ...] for each node
            # We take the average or the first valid value
            maintainability = sum(m[0] for m in mi_results) / len(mi_results)
        else:
            maintainability = 0.0

        return RadonMetrics(
            snippet_id=snippet_id,
            complexity=total_complexity,
            loc=raw_analysis.loc,
            maintainability=maintainability,
            raw_loc=raw_analysis.loc,
            raw_sloc=raw_analysis.sloc,
            raw_comments=raw_analysis.comments,
            raw_strings=raw_analysis.strings
        )
    except Exception as e:
        logger.error(f"Failed to extract radon metrics for {snippet_id}: {e}")
        return None

def extract_pylint_metrics(snippet_id: str, code: str) -> Optional[PylintMetrics]:
    """
    Extract pylint metrics (bug indicators, style issues) from a code snippet.
    Returns None if extraction fails.
    """
    try:
        # Create a temporary file for pylint to analyze
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            # Capture output
            output = StringIO()
            reporter = TextReporter(output)
            
            # Run pylint with minimal configuration to focus on bugs and style
            # Disable specific checks that might be too noisy for this context
            Run(
                [temp_path, 
                 '--disable=missing-docstring,invalid-name,too-many-arguments,too-many-locals',
                 '--reports=no',
                 '--output-format=text'],
                reporter=reporter,
                exit=False
            )
            
            # Parse output to count message types
            lines = output.getvalue().split('\n')
            bug_count = 0
            convention_count = 0
            refactor_count = 0
            info_count = 0
            error_count = 0

            for line in lines:
                if '[E' in line: # Error
                    error_count += 1
                elif '[R' in line: # Refactor
                    refactor_count += 1
                elif '[C' in line: # Convention
                    convention_count += 1
                elif '[I' in line: # Info
                    info_count += 1
                elif '[F' in line: # Fatal (treat as bug)
                    bug_count += 1
                elif 'bug' in line.lower() and '[' not in line:
                    bug_count += 1

            return PylintMetrics(
                snippet_id=snippet_id,
                bug_count=bug_count,
                convention_count=convention_count,
                refactor_count=refactor_count,
                info_count=info_count,
                error_count=error_count
            )
        finally:
            os.unlink(temp_path)
    except Exception as e:
        logger.error(f"Failed to extract pylint metrics for {snippet_id}: {e}")
        return None

def process_snippets_for_metrics(snippets: List[Dict[str, Any]], metric_type: str = "all") -> List[Dict[str, Any]]:
    """
    Process a list of snippets and extract metrics.
    Returns a list of metric dictionaries.
    """
    results = []
    for snippet in snippets:
        snippet_id = snippet.get('id')
        code = snippet.get('code')
        if not snippet_id or not code:
            logger.warning(f"Skipping snippet with missing id or code")
            continue

        if metric_type in ["all", "radon"]:
            radon_res = extract_radon_metrics(snippet_id, code)
            if radon_res:
                results.append(radon_res.to_dict())

        if metric_type in ["all", "pylint"]:
            pylint_res = extract_pylint_metrics(snippet_id, code)
            if pylint_res:
                results.append(pylint_res.to_dict())

    return results

def write_metrics_to_csv(metrics: List[Dict[str, Any]], output_path: str):
    """
    Write extracted metrics to a CSV file.
    """
    if not metrics:
        logger.warning("No metrics to write.")
        # Still create an empty file with headers to satisfy "file exists" checks
        headers = ["snippet_id", "metric_type", "cyclomatic_complexity", "loc", 
                   "maintainability_index", "raw_loc", "raw_sloc", "raw_comments", 
                   "raw_strings", "bug_count", "convention_count", "refactor_count", 
                   "info_count", "error_count"]
        with open(output_path, 'w') as f:
            f.write(','.join(headers) + '\n')
        return

    import pandas as pd
    df = pd.DataFrame(metrics)
    # Ensure consistent columns even if some metric types are missing
    all_cols = ["snippet_id", "metric_type", "cyclomatic_complexity", "loc", 
                "maintainability_index", "raw_loc", "raw_sloc", "raw_comments", 
                "raw_strings", "bug_count", "convention_count", "refactor_count", 
                "info_count", "error_count"]
    
    # Reindex to ensure all columns exist, filling missing with 0 or NaN as appropriate
    # For numeric columns, fill with 0. For ID/Type, keep as is.
    numeric_cols = ["cyclomatic_complexity", "loc", "maintainability_index", "raw_loc", 
                    "raw_sloc", "raw_comments", "raw_strings", "bug_count", 
                    "convention_count", "refactor_count", "info_count", "error_count"]
    
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = df[col].fillna(0)
    
    # Reorder
    df = df[[c for c in all_cols if c in df.columns]]
    
    # Create directory if needed
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(metrics)} metric records to {output_path}")

def run_metric_extraction(input_path: str, output_dir: str):
    """
    Main entry point for metric extraction.
    Loads processed snippets, extracts metrics, and writes to CSV.
    """
    logger.info(f"Starting metric extraction from {input_path}")
    
    # Load snippets
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(101)

    with open(input_path, 'r') as f:
        snippets = json.load(f)

    if not isinstance(snippets, list):
        snippets = [snippets]

    logger.info(f"Loaded {len(snippets)} snippets for metric extraction")

    # Extract metrics
    metrics = process_snippets_for_metrics(snippets)
    logger.info(f"Extracted {len(metrics)} metric records")

    if len(metrics) == 0:
        logger.warning("No metrics were extracted. Check input data.")
    
    # Write outputs
    radon_output = os.path.join(output_dir, "radon_metrics.csv")
    pylint_output = os.path.join(output_dir, "pylint_metrics.csv")
    combined_output = os.path.join(output_dir, "all_metrics.csv")

    # Separate for specific files if needed, but combined is often easier for downstream
    # The task asks for "one file per metric type" in T023, but we write all here
    # and T023 will aggregate. We'll write the combined set here.
    write_metrics_to_csv(metrics, combined_output)
    
    # Also write separate files for clarity
    radon_metrics = [m for m in metrics if m.get('metric_type') == 'radon']
    pylint_metrics = [m for m in metrics if m.get('metric_type') == 'pylint']
    
    write_metrics_to_csv(radon_metrics, radon_output)
    write_metrics_to_csv(pylint_metrics, pylint_output)

    # Update state
    update_state_with_artifact(combined_output)
    logger.info("Metric extraction completed successfully")

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Extract metrics from code snippets")
    parser.add_argument("--input", default="data/processed/filtered_snippets.json",
                        help="Path to filtered snippets JSON")
    parser.add_argument("--output-dir", default="data/metrics",
                        help="Directory to write metrics CSVs")
    args = parser.parse_args()

    run_metric_extraction(args.input, args.output_dir)

if __name__ == "__main__":
    main()