"""
Data Quantities Documentation Generator

Generates concrete data quantities documentation for reproducibility records.
Documents knot counts per crossing number, total records, and null percentages.
Per marie-curie-simulated review requirement for "concrete numbers".
"""
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime
from reproducibility.logs import log_operation, get_logger
from data_quality import calculate_null_percentages, generate_data_quality_report
from dataset_counts import load_cleaned_knots, count_knots_per_crossing_number

logger = get_logger(__name__)

def load_cleaned_knots_data(data_path: Path) -> List[Dict[str, Any]]:
    """Load cleaned knot data from CSV file."""
    if not data_path.exists():
        logger.error(f"Cleaned data file not found: {data_path}")
        return []
    
    knots = []
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            knots.append(row)
    return knots

def calculate_null_percentages_per_field(knots: List[Dict[str, Any]], fields: List[str]) -> Dict[str, float]:
    """Calculate null percentage for each specified field."""
    if not knots:
        return {field: 0.0 for field in fields}
    
    null_counts = defaultdict(int)
    for knot in knots:
        for field in fields:
            value = knot.get(field, '')
            if value is None or value == '' or value == 'nan' or value == 'NaN':
                null_counts[field] += 1
    
    total = len(knots)
    return {field: (null_counts[field] / total * 100) if total > 0 else 0.0 for field in fields}

def generate_data_quantities_report(knots: List[Dict[str, Any]], 
                                    counts_per_crossing: Dict[int, int],
                                    null_percentages: Dict[str, float],
                                    total_records: int,
                                    hyperbolic_count: Optional[int] = None,
                                    excluded_count: Optional[int] = None) -> Dict[str, Any]:
    """Generate comprehensive data quantities report."""
    return {
        'generated_at': datetime.now().isoformat(),
        'total_records': total_records,
        'knots_per_crossing_number': {str(k): v for k, v in sorted(counts_per_crossing.items())},
        'null_percentages': null_percentages,
        'hyperbolic_knots': hyperbolic_count,
        'excluded_knots': excluded_count,
        'crossing_number_range': {
            'min': min(counts_per_crossing.keys()) if counts_per_crossing else None,
            'max': max(counts_per_crossing.keys()) if counts_per_crossing else None
        }
    }

def write_data_quantities_report_md(report: Dict[str, Any], output_path: Path) -> None:
    """Write data quantities report to markdown file."""
    lines = []
    lines.append("# Data Quantities Report")
    lines.append("")
    lines.append(f"**Generated:** {report['generated_at']}")
    lines.append("")
    lines.append("## Dataset Overview")
    lines.append("")
    lines.append(f"- **Total Records:** {report['total_records']}")
    lines.append(f"- **Crossing Number Range:** {report['crossing_number_range']['min']} to {report['crossing_number_range']['max']}")
    
    if report.get('hyperbolic_knots') is not None:
        lines.append(f"- **Hyperbolic Knots:** {report['hyperbolic_knots']}")
    if report.get('excluded_knots') is not None:
        lines.append(f"- **Excluded Knots:** {report['excluded_knots']}")
    
    lines.append("")
    lines.append("## Knot Counts per Crossing Number")
    lines.append("")
    lines.append("| Crossing Number | Count |")
    lines.append("|-----------------|-------|")
    
    for crossing_num in sorted(report['knots_per_crossing_number'].keys(), key=int):
        count = report['knots_per_crossing_number'][crossing_num]
        lines.append(f"| {crossing_num} | {count} |")
    
    lines.append("")
    lines.append("## Null Percentages by Field")
    lines.append("")
    lines.append("| Field | Null Percentage |")
    lines.append("|-------|-----------------|")
    
    for field, percentage in sorted(report['null_percentages'].items()):
        lines.append(f"| {field} | {percentage:.2f}% |")
    
    lines.append("")
    lines.append("## Data Quality Summary")
    lines.append("")
    max_null_pct = max(report['null_percentages'].values()) if report['null_percentages'] else 0.0
    if max_null_pct <= 5.0:
        lines.append(f"✓ All fields have null percentage ≤ 5% (maximum: {max_null_pct:.2f}%)")
    else:
        lines.append(f"⚠ Some fields exceed 5% null threshold (maximum: {max_null_pct:.2f}%)")
    
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("This report documents concrete data quantities as required for reproducibility.")
    lines.append("Data derived from Knot Atlas for prime knots with crossing number ≤ 13.")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    """Main entry point for data quantities documentation generation."""
    project_root = Path(__file__).parent.parent.parent
    data_path = project_root / 'data' / 'processed' / 'knots_cleaned.csv'
    output_path = project_root / 'docs' / 'reproducibility' / 'data_quantities.md'
    
    log_operation('data_quantities', 'generate_report', str(data_path), str(output_path), {}, 'started')
    
    # Load cleaned knots
    knots = load_cleaned_knots_data(data_path)
    total_records = len(knots)
    
    if total_records == 0:
        logger.error("No cleaned knot data found. Cannot generate data quantities report.")
        log_operation('data_quantities', 'generate_report', str(data_path), str(output_path), {}, 'failed')
        return 1
    
    logger.info(f"Loaded {total_records} cleaned knot records")
    
    # Count knots per crossing number
    counts_per_crossing = count_knots_per_crossing_number(knots)
    
    # Define key fields to check for null values
    key_fields = [
        'knot_id',
        'crossing_number',
        'braid_index',
        'hyperbolic_volume',
        'is_alternating',
        'dt_code',
        'braid_word'
    ]
    
    # Calculate null percentages
    null_percentages = calculate_null_percentages_per_field(knots, key_fields)
    
    # Get hyperbolic and excluded counts if available
    hyperbolic_count = None
    excluded_count = None
    excluded_log_path = project_root / 'docs' / 'reproducibility' / 'excluded_knots.md'
    if excluded_log_path.exists():
        with open(excluded_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'Exclusion Count:' in content:
                try:
                    excluded_count = int(content.split('Exclusion Count:')[1].strip().split()[0])
                except (IndexError, ValueError):
                    pass
    
    # Generate report
    report = generate_data_quantities_report(
        knots=knots,
        counts_per_crossing=counts_per_crossing,
        null_percentages=null_percentages,
        total_records=total_records,
        hyperbolic_count=hyperbolic_count,
        excluded_count=excluded_count
    )
    
    # Write markdown report
    write_data_quantities_report_md(report, output_path)
    
    logger.info(f"Data quantities report written to {output_path}")
    log_operation('data_quantities', 'generate_report', str(data_path), str(output_path), 
                 {'total_records': total_records}, 'completed')
    
    return 0

if __name__ == '__main__':
    exit(main())
