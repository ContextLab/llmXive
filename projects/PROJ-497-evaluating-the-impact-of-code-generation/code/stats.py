import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from config import get_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_task_id_from_path(file_path: str) -> str:
    """
    Extract task_id from a file path like:
    data/generated/StarCoder/HumanEval/0/samples/000.py -> '0'
    data/human/HumanEval/0.py -> '0'
    """
    parts = Path(file_path).parts
    # Strategy: Look for 'samples' or end of path to identify task folder
    if 'samples' in parts:
        idx = parts.index('samples')
        if idx > 0:
            return parts[idx - 1]
    # Fallback for human data: last part without extension
    if len(parts) >= 2:
        return Path(parts[-1]).stem
    return "unknown"

def extract_source_type(file_path: str) -> str:
    """
    Extract source type (LLM or Human) from path.
    data/generated/... -> LLM
    data/human/... -> Human
    """
    parts = Path(file_path).parts
    if 'generated' in parts:
        return 'LLM'
    elif 'human' in parts:
        return 'Human'
    return 'Unknown'

def count_lines_of_code(file_path: str) -> int:
    """Count non-empty, non-comment lines in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        count = 0
        in_multiline_string = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Simple toggle for multiline strings
                if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                    in_multiline_string = not in_multiline_string
                continue
            if in_multiline_string:
                continue
            if stripped.startswith('#'):
                continue
            count += 1
        return count
    except Exception as e:
        logger.warning(f"Could not count lines in {file_path}: {e}")
        return 0

def parse_vulnerability_report(report_path: str) -> List[Dict[str, Any]]:
    """
    Parse the structured vulnerability report (from T013b).
    Returns list of dicts: {file_path, cwe_id, severity, line_number}
    """
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        # Handle if wrapped in a key
        if isinstance(data, dict):
            if 'vulnerabilities' in data:
                return data['vulnerabilities']
            if 'results' in data:
                return data['results']
        return []
    except Exception as e:
        logger.error(f"Failed to parse vulnerability report {report_path}: {e}")
        return []

def calculate_per_sample_stats(input_path: str, output_path: str) -> None:
    """
    T014 Implementation: Calculate LOC and vuln count per sample file.
    Input: data/processed/vulnerability_reports.json
    Output: data/processed/raw_vulnerability_counts.csv
    """
    logger.info(f"Calculating per-sample stats from {input_path}")
    reports = parse_vulnerability_report(input_path)
    
    # Aggregate vulns by file
    file_vulns = {}
    for vuln in reports:
        fp = vuln.get('file_path')
        if fp:
            file_vulns[fp] = file_vulns.get(fp, 0) + 1
    
    rows = []
    for file_path, vuln_count in file_vulns.items():
        # Determine task_id and source_type from path
        task_id = extract_task_id_from_path(file_path)
        source_type = extract_source_type(file_path)
        loc = count_lines_of_code(file_path)
        
        rows.append({
            'task_id': task_id,
            'source_type': source_type,
            'file_path': file_path,
            'lines_of_code': loc,
            'vulnerability_count': vuln_count
        })
    
    df = pd.DataFrame(rows)
    if df.empty:
        logger.warning("No vulnerability data found to process.")
        df = pd.DataFrame(columns=['task_id', 'source_type', 'file_path', 'lines_of_code', 'vulnerability_count'])
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved per-sample stats to {output_path} ({len(df)} rows)")

def aggregate_analysis_dataset(input_path: str, output_path: str) -> None:
    """
    T015 Implementation: Aggregate raw counts to task level.
    
    Logic:
    - Input: data/processed/raw_vulnerability_counts.csv (one row per file)
    - For LLM (source_type='LLM'): Calculate MEAN vulnerability count per task_id.
      (Since we have multiple samples per task, we average the vuln counts).
    - For Human (source_type='Human'): Calculate SINGLE count per task_id.
      (Usually 1 file per task, so just take the value. If multiple, average or sum? 
       Spec says 'single count', implying one observation per task. We will take the mean 
       if multiple exist to be safe, but logically it should be 1 row).
    - Output: data/processed/aggregated_analysis_dataset.csv
      Columns: task_id, source_type, benchmark (inferred), avg_vulnerability_count, sample_count (for LLM), lines_of_code (avg)
    """
    logger.info(f"Aggregating analysis dataset from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T014 first.")
    
    df = pd.read_csv(input_path)
    
    # Infer benchmark from file_path if not present, or assume based on task_id patterns if known.
    # Since raw CSV has file_path, we can extract benchmark from there if needed.
    # Let's add a benchmark column by parsing file_path if it's not in the CSV.
    # Assuming path format: data/generated/{model}/{benchmark}/{task_id}/samples/...
    def get_benchmark(path_str):
        parts = Path(path_str).parts
        if 'generated' in parts:
            try:
                idx = parts.index('generated')
                # generated / Model / Benchmark / Task ...
                if idx + 2 < len(parts):
                    return parts[idx + 2]
            except:
                pass
        elif 'human' in parts:
            try:
                idx = parts.index('human')
                if idx + 1 < len(parts):
                    return parts[idx + 1]
            except:
                pass
        return 'Unknown'
    
    df['benchmark'] = df['file_path'].apply(get_benchmark)
    
    # Group by task_id, source_type, benchmark
    # For LLM: mean of vuln_count, mean of LOC, count of samples
    # For Human: mean of vuln_count (should be single value), mean of LOC, count of samples (should be 1)
    
    aggregated = df.groupby(['task_id', 'source_type', 'benchmark']).agg(
        avg_vulnerability_count=('vulnerability_count', 'mean'),
        avg_lines_of_code=('lines_of_code', 'mean'),
        sample_count=('file_path', 'count')
    ).reset_index()
    
    # Round floats for cleaner output
    aggregated['avg_vulnerability_count'] = aggregated['avg_vulnerability_count'].round(4)
    aggregated['avg_lines_of_code'] = aggregated['avg_lines_of_code'].round(2)
    
    # Sort for readability
    aggregated = aggregated.sort_values(['source_type', 'task_id'])
    
    aggregated.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated dataset to {output_path} ({len(aggregated)} rows)")

def main():
    """
    Main entry point for stats module.
    Supports running T014 (per-sample) or T015 (aggregation) via args.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Vulnerability Statistics Module")
    parser.add_argument('--mode', type=str, choices=['per_sample', 'aggregate'], required=True,
                        help="Mode: 'per_sample' (T014) or 'aggregate' (T015)")
    parser.add_argument('--input', type=str, required=True, help="Input file path")
    parser.add_argument('--output', type=str, required=True, help="Output file path")
    
    args = parser.parse_args()
    
    paths = get_paths()
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    if args.mode == 'per_sample':
        calculate_per_sample_stats(args.input, args.output)
    elif args.mode == 'aggregate':
        aggregate_analysis_dataset(args.input, args.output)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == '__main__':
    main()