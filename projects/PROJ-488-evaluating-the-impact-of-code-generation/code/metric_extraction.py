"""
Metric Extraction Module.
Extracts static analysis metrics (Radon, Pylint) from code snippets.
"""
import os
import sys
import logging
import ast
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from radon.complexity import cc_visit
from radon.raw import analyze as raw_analyze
from radon.mi import mi_visit
from pylint.lint import Run
from pylint.reporters.text import TextReporter
import io

from logging_config import setup_logger, get_logger
from data_model import MetricResult

def extract_radon_metrics(code: str) -> Dict[str, float]:
    """Extract Radon complexity metrics."""
    try:
        # Cyclomatic Complexity
        cc_results = cc_visit(code)
        max_cc = max([r.complexity for r in cc_results], default=0)
        avg_cc = sum([r.complexity for r in cc_results]) / len(cc_results) if cc_results else 0.0
        
        # Raw Metrics (LOC, etc.)
        raw = raw_analyze(code)
        loc = raw.loc
        lloc = raw.lloc
        
        # Maintainability Index
        mi_results = mi_visit(code, mi=True)
        mi_score = mi_results[0] if mi_results else 0.0
        
        return {
            "max_cc": max_cc,
            "avg_cc": avg_cc,
            "loc": loc,
            "lloc": lloc,
            "mi": mi_score
        }
    except Exception as e:
        logging.warning(f"Radon extraction failed: {e}")
        return {"max_cc": 0.0, "avg_cc": 0.0, "loc": 0, "lloc": 0, "mi": 0.0}

def extract_pylint_metrics(code: str) -> Dict[str, float]:
    """Extract Pylint bug indicator metrics."""
    try:
        # Run pylint on the code string
        # We use a temporary file to avoid issues with stdin
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Capture output
            output = io.StringIO()
            reporter = TextReporter(output)
            
            # Run pylint with specific options to get counts
            # We disable some checks to focus on bugs/errors
            # --disable=all --enable=E,W (Errors and Warnings)
            Run(
                [temp_path, "--disable=all", "--enable=E,W", "--output-format=text"],
                reporter=reporter,
                exit=False
            )
            
            pylint_output = output.getvalue()
            
            # Count specific patterns
            # This is a simplified heuristic. Real implementation might parse JSON output.
            bug_count = pylint_output.count("E:") # Errors
            warning_count = pylint_output.count("W:") # Warnings
            
            # Normalize by LOC if possible, or just use raw counts
            # For now, return raw counts as metrics
            return {
                "error_count": bug_count,
                "warning_count": warning_count,
                "total_issues": bug_count + warning_count
            }
        finally:
            os.unlink(temp_path)
    except Exception as e:
        logging.warning(f"Pylint extraction failed: {e}")
        return {"error_count": 0, "warning_count": 0, "total_issues": 0}

def process_snippets_for_metrics(snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process a list of snippets and extract metrics for each."""
    results = []
    logger = get_logger("metric_extraction")
    
    for snippet in snippets:
        snippet_id = snippet.get("id")
        code = snippet.get("code")
        source = snippet.get("source", "unknown")
        
        if not code:
            continue
            
        radon_metrics = extract_radon_metrics(code)
        pylint_metrics = extract_pylint_metrics(code)
        
        combined = {
            "snippet_id": snippet_id,
            "source": source,
            **radon_metrics,
            **pylint_metrics
        }
        results.append(combined)
        
        if len(results) % 100 == 0:
            logger.info(f"Processed {len(results)} snippets...")
            
    return results

def write_metrics_to_csv(results: List[Dict[str, Any]], output_dir: Path):
    """Write metrics to CSV files, one per metric type."""
    output_dir.mkdir(exist_ok=True)
    
    df = pd.DataFrame(results)
    
    # Separate by metric groups
    # Complexity metrics
    complexity_cols = ["snippet_id", "source", "max_cc", "avg_cc", "loc", "lloc", "mi"]
    complexity_df = df[[c for c in complexity_cols if c in df.columns]]
    complexity_df.to_csv(output_dir / "complexity_metrics.csv", index=False)
    
    # Pylint metrics
    pylint_cols = ["snippet_id", "source", "error_count", "warning_count", "total_issues"]
    pylint_df = df[[c for c in pylint_cols if c in df.columns]]
    pylint_df.to_csv(output_dir / "pylint_metrics.csv", index=False)
    
    logging.info(f"Wrote {len(complexity_df)} rows to complexity_metrics.csv")
    logging.info(f"Wrote {len(pylint_df)} rows to pylint_metrics.csv")

def run_metric_extraction(input_file: Path, output_dir: Path):
    """Main workflow for metric extraction."""
    logger = setup_logger("metric_extraction", log_file="results/metric_extraction.log")
    logger.info(f"Loading snippets from {input_file}")
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} not found.")
        sys.exit(1)
        
    import json
    with open(input_file, 'r') as f:
        snippets = json.load(f)
        
    if not isinstance(snippets, list):
        snippets = [snippets]
        
    logger.info(f"Processing {len(snippets)} snippets...")
    results = process_snippets_for_metrics(snippets)
    
    logger.info("Writing metrics to CSV...")
    write_metrics_to_csv(results, output_dir)
    logger.info("Metric extraction complete.")

def main():
    """Entry point for metric extraction script."""
    input_file = Path("data/processed/snippets_filtered.json")
    output_dir = Path("data/metrics")
    
    if not input_file.exists():
        logging.error(f"Input file {input_file} not found. Run data filtering first.")
        sys.exit(1)
        
    run_metric_extraction(input_file, output_dir)

if __name__ == "__main__":
    main()
