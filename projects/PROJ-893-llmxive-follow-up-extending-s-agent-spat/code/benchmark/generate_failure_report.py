import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import from existing project modules
from config import Config
from benchmark.analyze_failures import analyze_failures, classify_failure

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def load_csv_as_dict(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load a CSV file into a dictionary keyed by scene_id."""
    import csv
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    data = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scene_id = row.get('scene_id')
            if scene_id:
                data[scene_id] = row
    return data

def generate_report(
    analysis_results: List[Dict[str, Any]],
    benchmark_results: Dict[str, Dict[str, Any]],
    exclusion_log: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate the Markdown failure analysis report.
    
    Args:
        analysis_results: List of dicts from analyze_failures (contains scene_id, failure_type, etc.)
        benchmark_results: Dict of scene_id -> metrics row
        exclusion_log: Optional dict containing exclusion counts and IDs
        
    Returns:
        Markdown string content for the report.
    """
    total_failures = len(analysis_results)
    
    if total_failures == 0:
        return "# Failure Analysis Report\n\nNo failures detected to analyze.\n"

    # Count failure types
    type_counts = {}
    for item in analysis_results:
        f_type = item.get('failure_type', 'Unknown')
        type_counts[f_type] = type_counts.get(f_type, 0) + 1

    # Calculate proportions
    proportions = {}
    for f_type, count in type_counts.items():
        proportions[f_type] = count / total_failures

    # Identify representative examples (up to 3 per type)
    examples_by_type = {}
    for f_type in type_counts:
        examples_by_type[f_type] = []
    
    for item in analysis_results:
        f_type = item.get('failure_type', 'Unknown')
        if len(examples_by_type[f_type]) < 3:
            examples_by_type[f_type].append(item)

    # Build Markdown
    lines = []
    lines.append("# Failure Analysis Report")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Total Failures Analyzed**: {total_failures}")
    
    if exclusion_log:
        lines.append(f"- **Excluded Scenes**: {exclusion_log.get('total_excluded', 0)}")
        lines.append(f"  - Invalid Geometry: {exclusion_log.get('invalid_geometry', 0)}")
        lines.append(f"  - Missing Constraints: {exclusion_log.get('missing_constraints', 0)}")
    
    lines.append("")
    lines.append("## Failure Distribution")
    lines.append("")
    lines.append("| Failure Type | Count | Proportion |")
    lines.append("| :--- | :--- | :--- |")
    
    for f_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        prop = proportions[f_type]
        lines.append(f"| {f_type} | {count} | {prop:.2%} |")
    
    lines.append("")
    lines.append("## Semantic Gap Analysis")
    lines.append("")
    semantic_gap_count = type_counts.get('Semantic Gap', 0)
    semantic_gap_prop = semantic_gap_count / total_failures if total_failures > 0 else 0.0
    
    lines.append(f"The proportion of failures attributable to **Semantic Gap** (disambiguation issues) is **{semantic_gap_prop:.2%}** ({semantic_gap_count} / {total_failures}).")
    lines.append("")
    lines.append("This metric quantifies the extent to which the symbolic solver underperforms due to ambiguity in natural language constraints that require world knowledge or context not explicitly encoded in the geometric constraints.")
    lines.append("")
    lines.append("## Representative Failure Examples")
    lines.append("")
    
    for f_type, examples in examples_by_type.items():
        lines.append(f"### {f_type}")
        lines.append("")
        for ex in examples:
            scene_id = ex.get('scene_id', 'Unknown')
            reason = ex.get('reason', 'No reason provided')
            lines.append(f"- **Scene ID**: `{scene_id}`")
            lines.append(f"  - **Reason**: {reason}")
            
            # Try to enrich with benchmark data if available
            if scene_id in benchmark_results:
                row = benchmark_results[scene_id]
                lines.append(f"  - **Symbolic Prediction**: {row.get('symbolic_prediction', 'N/A')}")
                lines.append(f"  - **Ground Truth**: {row.get('ground_truth', 'N/A')}")
                lines.append(f"  - **VLM Prediction**: {row.get('vlm_prediction', 'N/A')}")
            lines.append("")
    
    lines.append("---")
    lines.append("*Generated by llmXive automated science pipeline.*")
    
    return "\n".join(lines)

def main():
    """
    Main entry point to generate the failure analysis report.
    
    Reads:
    - data/derived/failure_analysis.jsonl (from T021)
    - data/results/benchmark_results.csv (from T019)
    - data/results/exclusion_log.json (from T013)
    
    Writes:
    - data/results/failure_analysis_report.md
    """
    config = Config()
    
    # Define paths
    analysis_path = config.DATA_DERIVED_PATH / "failure_analysis.jsonl"
    benchmark_path = config.DATA_RESULTS_PATH / "benchmark_results.csv"
    exclusion_path = config.DATA_RESULTS_PATH / "exclusion_log.json"
    output_path = config.DATA_RESULTS_PATH / "failure_analysis_report.md"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        analysis_data = load_jsonl(analysis_path)
    except FileNotFoundError as e:
        print(f"Error: Could not load failure analysis data. Ensure T021 has run. ({e})")
        sys.exit(1)
        
    try:
        benchmark_data = load_csv_as_dict(benchmark_path)
    except FileNotFoundError as e:
        print(f"Error: Could not load benchmark results. Ensure T019 has run. ({e})")
        sys.exit(1)
        
    exclusion_log = None
    if exclusion_path.exists():
        with open(exclusion_path, 'r', encoding='utf-8') as f:
            exclusion_log = json.load(f)
    
    # Generate report
    report_content = generate_report(analysis_data, benchmark_data, exclusion_log)
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    print(f"Failure analysis report generated: {output_path}")

if __name__ == "__main__":
    main()
