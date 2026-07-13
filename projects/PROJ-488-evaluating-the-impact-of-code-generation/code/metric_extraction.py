import os
import json
import logging
import ast
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

from radon.complexity import cc_visit
from radon.raw import analyze
from radon.metrics import h_visit
import pylint.lint
from pylint.reporters.text import TextReporter
from pylint.message import Message

from data_model import MetricResult
from logging_config import get_logger
from state_tracker import register_artifact_hash, update_state_timestamp

logger = get_logger(__name__)

def extract_radon_metrics(code_snippet: str) -> Dict[str, Any]:
    """
    Extract cyclomatic complexity, raw metrics (LOC, etc), and maintainability index.
    """
    try:
        # Cyclomatic Complexity
        complexity_results = cc_visit(code_snippet)
        total_cc = sum(r.complexity for r in complexity_results)
        max_cc = max([r.complexity for r in complexity_results], default=0)
        avg_cc = total_cc / len(complexity_results) if complexity_results else 0.0

        # Raw Metrics
        raw_analysis = analyze(code_snippet)
        loc = raw_analysis.loc
        lloc = raw_analysis.lloc
        sloc = raw_analysis.sloc
        comments = raw_analysis.comments
        multi = raw_analysis.multi
        blank = raw_analysis.blank
        code = raw_analysis.code

        # Maintainability Index
        h_results = h_visit(code_snippet)
        mi = h_results[0].mi if h_results else 0.0

        return {
            "cyclomatic_complexity_total": total_cc,
            "cyclomatic_complexity_max": max_cc,
            "cyclomatic_complexity_avg": avg_cc,
            "loc": loc,
            "lloc": lloc,
            "sloc": sloc,
            "comments": comments,
            "multi": multi,
            "blank": blank,
            "code_lines": code,
            "maintainability_index": mi
        }
    except Exception as e:
        logger.error(f"Error extracting radon metrics: {e}")
        return {
            "cyclomatic_complexity_total": None,
            "cyclomatic_complexity_max": None,
            "cyclomatic_complexity_avg": None,
            "loc": None,
            "lloc": None,
            "sloc": None,
            "comments": None,
            "multi": None,
            "blank": None,
            "code_lines": None,
            "maintainability_index": None
        }

def extract_pylint_metrics(code_snippet: str) -> Dict[str, Any]:
    """
    Extract potential bug indicators and style issues using pylint.
    Returns counts of specific message types.
    """
    # Pylint runs best on files, so we write to a temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code_snippet)
        temp_path = f.name

    try:
        # Configure pylint to only report errors and warnings (bugs) and convention/style
        # We use a custom reporter to capture output
        reporter = TextReporter()
        
        # Run pylint
        # Disable specific checks that might be too noisy or irrelevant for raw snippets
        # e.g., missing docstring, missing-module-docstring
        options = [
            '--disable=C0114,C0115,C0116', # Disable missing docstring warnings
            '--msg-template={msg_id}:{symbol}:{line}:{column}:{msg}',
            '--reports=no',
            '--score=no',
            '--errors-only', # Only errors
            '--warnings-only' # Only warnings
        ]
        
        # We need to capture both errors and warnings specifically for "bugs" and "style"
        # Pylint categories:
        # E: Error (potential bugs)
        # W: Warning (conventions/style issues)
        # R: Refactor (convention/style)
        # C: Convention (style)
        
        # Re-run to capture all relevant categories
        # We will parse the output manually
        all_messages = []
        
        # Use a custom reporter to capture messages
        class CustomReporter(TextReporter):
            def __init__(self):
                super().__init__()
                self.messages = []
            
            def handle_message(self, msg: Message):
                self.messages.append(msg)
                super().handle_message(msg)

        custom_reporter = CustomReporter()
        
        # Run pylint with specific categories: E (Error), W (Warning), C (Convention), R (Refactor)
        # We exclude I (Info) as it's usually noise
        try:
            pylint.lint.Run(
                [temp_path, '--disable=missing-module-docstring,missing-class-docstring,missing-function-docstring'],
                reporter=custom_reporter,
                do_exit=False
            )
        except SystemExit:
            pass

        # Categorize messages
        error_count = 0
        warning_count = 0
        convention_count = 0
        refactor_count = 0
        bug_indicators = []
        style_issues = []

        for msg in custom_reporter.messages:
            if msg.symbol:
                if msg.msg_id.startswith('E'):
                    error_count += 1
                    bug_indicators.append(msg.symbol)
                elif msg.msg_id.startswith('W'):
                    warning_count += 1
                    bug_indicators.append(msg.symbol) # Warnings can be potential bugs
                elif msg.msg_id.startswith('C'):
                    convention_count += 1
                    style_issues.append(msg.symbol)
                elif msg.msg_id.startswith('R'):
                    refactor_count += 1
                    style_issues.append(msg.symbol)

        return {
            "pylint_error_count": error_count,
            "pylint_warning_count": warning_count,
            "pylint_convention_count": convention_count,
            "pylint_refactor_count": refactor_count,
            "total_potential_bugs": error_count + warning_count,
            "total_style_issues": convention_count + refactor_count,
            "bug_indicator_symbols": list(set(bug_indicators)),
            "style_issue_symbols": list(set(style_issues))
        }

    except Exception as e:
        logger.error(f"Error extracting pylint metrics for snippet: {e}")
        return {
            "pylint_error_count": None,
            "pylint_warning_count": None,
            "pylint_convention_count": None,
            "pylint_refactor_count": None,
            "total_potential_bugs": None,
            "total_style_issues": None,
            "bug_indicator_symbols": [],
            "style_issue_symbols": []
        }
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

def process_snippets_for_metrics(snippets: List[Dict[str, Any]], group_label: str) -> List[MetricResult]:
    """
    Process a list of snippets (dicts) and return a list of MetricResult objects.
    """
    results = []
    for idx, snippet in enumerate(snippets):
        snippet_id = snippet.get('id', f"unknown_{idx}")
        code = snippet.get('code', '')
        
        if not code:
            logger.warning(f"Skipping snippet {snippet_id} due to empty code.")
            continue

        radon_metrics = extract_radon_metrics(code)
        pylint_metrics = extract_pylint_metrics(code)

        # Construct MetricResult
        # We flatten the metrics into a single dict for the result
        # The schema in data_model.py expects: snippet_id, metric_type, score, timestamp
        # However, the task asks for extraction of multiple metrics.
        # We will create multiple MetricResult entries per snippet, one for each metric type.
        
        timestamp = datetime.now().isoformat()

        # Radon Metrics
        for key, value in radon_metrics.items():
            if value is not None:
                results.append(MetricResult(
                    snippet_id=snippet_id,
                    group_label=group_label,
                    metric_type=f"radon_{key}",
                    score=value,
                    timestamp=timestamp
                ))

        # Pylint Metrics
        for key, value in pylint_metrics.items():
            if value is not None and not isinstance(value, list):
                results.append(MetricResult(
                    snippet_id=snippet_id,
                    group_label=group_label,
                    metric_type=f"pylint_{key}",
                    score=value,
                    timestamp=timestamp
                ))
            elif isinstance(value, list) and len(value) > 0:
                # For lists of symbols, we store the count or a string representation
                # The schema expects a score (float/int). Let's store the count for lists
                results.append(MetricResult(
                    snippet_id=snippet_id,
                    group_label=group_label,
                    metric_type=f"pylint_{key}_count",
                    score=len(value),
                    timestamp=timestamp
                ))

    return results

def write_metrics_to_csv(all_results: List[MetricResult], output_dir: Path):
    """
    Write metrics to CSV files, one per metric type.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group by metric_type
    grouped = {}
    for res in all_results:
        if res.metric_type not in grouped:
            grouped[res.metric_type] = []
        grouped[res.metric_type].append(res)

    for metric_type, items in grouped.items():
        filename = f"{metric_type}.csv"
        filepath = output_dir / filename
        with open(filepath, 'w') as f:
            # Header
            f.write("snippet_id,group_label,metric_type,score,timestamp\n")
            for item in items:
                f.write(f"{item.snippet_id},{item.group_label},{item.metric_type},{item.score},{item.timestamp}\n")
        logger.info(f"Wrote {len(items)} records to {filepath}")

def run_metric_extraction(data_path: Path, output_dir: Path):
    """
    Main entry point for metric extraction.
    Expects data_path to contain processed snippets (e.g., JSON files).
    """
    logger.info(f"Starting metric extraction from {data_path}")
    
    all_results = []
    
    # Find all JSON files in data_path
    json_files = list(data_path.glob('*.json'))
    if not json_files:
        logger.error(f"No JSON files found in {data_path}")
        return

    for json_file in json_files:
        group_label = json_file.stem # Assuming filename indicates group
        with open(json_file, 'r') as f:
            try:
                data = json.load(f)
                # Assume data is a list of snippets or a dict with a 'snippets' key
                if isinstance(data, list):
                    snippets = data
                elif isinstance(data, dict) and 'snippets' in data:
                    snippets = data['snippets']
                else:
                    snippets = [data]
                
                logger.info(f"Processing {len(snippets)} snippets from {json_file}")
                results = process_snippets_for_metrics(snippets, group_label)
                all_results.extend(results)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON file: {json_file}")
                continue

    if all_results:
        write_metrics_to_csv(all_results, output_dir)
        logger.info(f"Metric extraction complete. Total records: {len(all_results)}")
    else:
        logger.warning("No metrics were extracted.")

def main():
    # Default paths
    data_dir = Path("data/processed")
    metrics_dir = Path("data/metrics")
    
    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} does not exist. Please run ingestion first.")
        return

    run_metric_extraction(data_dir, metrics_dir)

if __name__ == "__main__":
    main()