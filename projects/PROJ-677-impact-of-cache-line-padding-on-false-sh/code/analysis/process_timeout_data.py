"""
process_timeout_data.py - Filter and analyze benchmark results excluding timeout entries.

This script loads the raw benchmark CSV, filters out rows with status 'TIMEOUT',
and prepares clean data for statistical analysis. It also generates a summary
report of excluded data.
"""

import pandas as pd
import sys
from pathlib import Path
import json

def process_benchmark_results(input_path: str, output_path: str, summary_path: str) -> dict:
    """
    Load benchmark results, filter out timeout entries, and save clean data.

    Args:
        input_path: Path to raw benchmark CSV
        output_path: Path to save filtered CSV
        summary_path: Path to save JSON summary of filtering

    Returns:
        Dictionary with filtering statistics
    """
    # Load raw data
    df = pd.read_csv(input_path)

    # Validate required columns
    required_cols = ['thread_count', 'configuration', 'iteration_count', 'wall_clock_time_ms', 'status']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Count total rows
    total_rows = len(df)

    # Filter out TIMEOUT and ERROR entries
    valid_mask = df['status'].isin(['OK'])
    filtered_df = df[valid_mask].copy()
    timeout_df = df[~valid_mask].copy()

    # Clean data
    # Convert wall_clock_time_ms to numeric, coercing errors to NaN then dropping
    filtered_df['wall_clock_time_ms'] = pd.to_numeric(filtered_df['wall_clock_time_ms'], errors='coerce')
    filtered_df = filtered_df.dropna(subset=['wall_clock_time_ms'])

    # Calculate statistics on filtered data
    stats = {
        'total_raw_rows': total_rows,
        'valid_rows': len(filtered_df),
        'excluded_rows': len(timeout_df),
        'exclusion_rate': len(timeout_df) / total_rows if total_rows > 0 else 0,
        'excluded_by_status': timeout_df['status'].value_counts().to_dict() if not timeout_df.empty else {}
    }

    # Save filtered data
    filtered_df.to_csv(output_path, index=False)

    # Save summary
    summary_data = {
        'input_file': input_path,
        'output_file': output_path,
        'filtering_timestamp': pd.Timestamp.now().isoformat(),
        'statistics': stats
    }
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)

    print(f"Processed {total_rows} rows:")
    print(f"  Valid: {stats['valid_rows']}")
    print(f"  Excluded: {stats['excluded_rows']} ({stats['exclusion_rate']:.1%})")
    if timeout_df['status'].value_counts().to_dict():
        print(f"  Excluded by status: {timeout_df['status'].value_counts().to_dict()}")

    return stats

def main():
    """Main entry point for command line usage."""
    # Default paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    raw_data_dir = project_root / 'data' / 'raw'
    processed_data_dir = project_root / 'data' / 'processed'

    # Ensure processed directory exists
    processed_data_dir.mkdir(parents=True, exist_ok=True)

    input_file = raw_data_dir / 'benchmark_results.csv'
    output_file = processed_data_dir / 'benchmark_results_clean.csv'
    summary_file = processed_data_dir / 'timeout_filter_summary.json'

    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        print("Please run run_benchmarks.sh first to generate raw data.")
        sys.exit(1)

    print(f"Loading data from: {input_file}")
    try:
        stats = process_benchmark_results(
            str(input_file),
            str(output_file),
            str(summary_file)
        )
        print(f"Clean data saved to: {output_file}")
        print(f"Summary saved to: {summary_file}")
    except Exception as e:
        print(f"ERROR: Processing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()