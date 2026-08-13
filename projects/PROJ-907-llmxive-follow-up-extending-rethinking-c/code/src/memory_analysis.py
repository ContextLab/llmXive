import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/memory_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_memory_log(log_path: str) -> List[Dict[str, Any]]:
    """
    Parse the memory profile log file (JSONL format).
    
    Args:
        log_path: Path to the memory profile log file (e.g., data/results/memory_profile_raw.jsonl)
        
    Returns:
        List of dictionaries containing memory usage data per image
    """
    records = []
    log_file = Path(log_path)
    
    if not log_file.exists():
        logger.warning(f"Memory log file not found: {log_path}")
        return records
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    # Ensure required fields exist
                    if 'image_index' in record and 'peak_memory_mb' in record:
                        records.append({
                            'image_index': record['image_index'],
                            'peak_memory_mb': float(record['peak_memory_mb']),
                            'timestamp': record.get('timestamp', ''),
                            'routing_shape': record.get('routing_shape', ''),
                            'oom_event': record.get('oom_event', False)
                        })
                    else:
                        logger.warning(f"Skipping malformed line {line_num}: missing required fields")
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
    except Exception as e:
        logger.error(f"Error reading memory log file: {e}")
        raise
    
    return records

def compute_memory_statistics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate memory statistics from parsed records.
    
    Args:
        records: List of memory usage records
        
    Returns:
        Dictionary containing statistical summary
    """
    if not records:
        return {
            'max_memory_mb': 0.0,
            'avg_memory_mb': 0.0,
            'min_memory_mb': 0.0,
            'oom_events': 0,
            'total_images': 0,
            'oom_rate': 0.0,
            'std_dev_mb': 0.0,
            'memory_efficiency': 'Unknown'
        }
    
    memory_values = [r['peak_memory_mb'] for r in records]
    oom_count = sum(1 for r in records if r.get('oom_event', False))
    
    stats = {
        'max_memory_mb': max(memory_values),
        'min_memory_mb': min(memory_values),
        'avg_memory_mb': statistics.mean(memory_values),
        'std_dev_mb': statistics.stdev(memory_values) if len(memory_values) > 1 else 0.0,
        'oom_events': oom_count,
        'total_images': len(records),
        'oom_rate': oom_count / len(records) if records else 0.0
    }
    
    # Determine OOM prevention efficacy
    if stats['oom_events'] == 0:
        stats['memory_efficiency'] = 'Optimal - No OOM events detected'
    elif stats['oom_rate'] < 0.05:
        stats['memory_efficiency'] = 'Good - Minimal OOM events (<5%)'
    elif stats['oom_rate'] < 0.20:
        stats['memory_efficiency'] = 'Moderate - Some OOM events (5-20%)'
    else:
        stats['memory_efficiency'] = 'Poor - High OOM rate (>20%)'
    
    return stats

def generate_markdown_report(records: List[Dict[str, Any]], stats: Dict[str, Any], output_path: str):
    """
    Generate a Markdown report with memory usage analysis.
    
    Args:
        records: List of memory usage records
        stats: Computed statistics
        output_path: Path to save the Markdown report
    """
    md_content = []
    md_content.append("# Memory Usage Report")
    md_content.append("")
    md_content.append("## Overview")
    md_content.append("")
    md_content.append(f"This report summarizes memory usage statistics from the tracing process.")
    md_content.append("")
    md_content.append("## Key Metrics")
    md_content.append("")
    md_content.append("| Metric | Value |")
    md_content.append("|--------|-------|")
    md_content.append(f"| Total Images Processed | {stats['total_images']} |")
    md_content.append(f"| Peak Memory (MB) | {stats['max_memory_mb']:.2f} |")
    md_content.append(f"| Average Memory (MB) | {stats['avg_memory_mb']:.2f} |")
    md_content.append(f"| Minimum Memory (MB) | {stats['min_memory_mb']:.2f} |")
    md_content.append(f"| Standard Deviation (MB) | {stats['std_dev_mb']:.2f} |")
    md_content.append(f"| OOM Events | {stats['oom_events']} |")
    md_content.append(f"| OOM Rate | {stats['oom_rate']:.2%} |")
    md_content.append(f"| Memory Efficiency | {stats['memory_efficiency']} |")
    md_content.append("")
    md_content.append("## Per-Image Memory Usage")
    md_content.append("")
    md_content.append("| Image Index | Peak Memory (MB) | OOM Event |")
    md_content.append("|-------------|------------------|-----------|")
    
    for record in records:
        oom_status = "Yes" if record.get('oom_event', False) else "No"
        md_content.append(f"| {record['image_index']} | {record['peak_memory_mb']:.2f} | {oom_status} |")
    
    md_content.append("")
    md_content.append("## Analysis Summary")
    md_content.append("")
    
    if stats['oom_events'] == 0:
        md_content.append("✅ **No Out-of-Memory events detected.** The memory management strategy (batch size 1 processing) successfully prevented OOM conditions.")
    else:
        md_content.append(f"⚠️ **{stats['oom_events']} OOM event(s) detected.** This indicates memory pressure exceeded available resources for some samples.")
    
    md_content.append("")
    md_content.append("### Recommendations")
    md_content.append("")
    
    if stats['max_memory_mb'] > 6.5:
        md_content.append("- **High Peak Memory:** Consider reducing batch size further or implementing more aggressive memory cleanup.")
    if stats['oom_rate'] > 0.1:
        md_content.append("- **High OOM Rate:** Review memory management logic and consider hardware upgrades or model optimization.")
    if stats['std_dev_mb'] > 100:
        md_content.append("- **High Variance:** Memory usage varies significantly across samples; investigate outlier cases.")
    
    md_content.append("")
    md_content.append("---")
    md_content.append(f"*Generated on: {stats.get('timestamp', 'N/A')}*")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    logger.info(f"Markdown report generated: {output_path}")

def save_json_profile(stats: Dict[str, Any], records: List[Dict[str, Any]], output_path: str):
    """
    Save memory profile statistics to JSON.
    
    Args:
        stats: Computed statistics
        records: List of memory usage records
        output_path: Path to save the JSON file
    """
    profile_data = {
        'max_memory_mb': stats['max_memory_mb'],
        'avg_memory_mb': stats['avg_memory_mb'],
        'min_memory_mb': stats['min_memory_mb'],
        'std_dev_mb': stats['std_dev_mb'],
        'oom_events': stats['oom_events'],
        'total_images': stats['total_images'],
        'oom_rate': stats['oom_rate'],
        'memory_efficiency': stats['memory_efficiency'],
        'per_image_data': [
            {
                'image_index': r['image_index'],
                'peak_memory_mb': r['peak_memory_mb'],
                'oom_event': r.get('oom_event', False)
            }
            for r in records
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, indent=2)
    
    logger.info(f"JSON profile saved: {output_path}")

def run_memory_analysis(log_path: str = 'data/results/memory_profile_raw.jsonl',
                        md_output: str = 'docs/memory_report.md',
                        json_output: str = 'data/results/memory_profile.json'):
    """
    Main entry point for memory analysis.
    
    Args:
        log_path: Path to the raw memory log file
        md_output: Path for the Markdown report output
        json_output: Path for the JSON profile output
    """
    logger.info(f"Starting memory analysis on: {log_path}")
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(md_output), exist_ok=True)
    os.makedirs(os.path.dirname(json_output), exist_ok=True)
    
    # Parse logs
    records = parse_memory_log(log_path)
    
    if not records:
        logger.warning("No valid records found in memory log. Generating empty report.")
        # Create empty stats for empty report
        stats = {
            'max_memory_mb': 0.0,
            'avg_memory_mb': 0.0,
            'min_memory_mb': 0.0,
            'std_dev_mb': 0.0,
            'oom_events': 0,
            'total_images': 0,
            'oom_rate': 0.0,
            'memory_efficiency': 'No data available'
        }
    else:
        # Compute statistics
        stats = compute_memory_statistics(records)
    
    # Generate outputs
    generate_markdown_report(records, stats, md_output)
    save_json_profile(stats, records, json_output)
    
    logger.info("Memory analysis completed successfully.")
    return stats

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze memory usage from tracing logs')
    parser.add_argument('--log', type=str, default='data/results/memory_profile_raw.jsonl',
                      help='Path to memory profile log file')
    parser.add_argument('--md-output', type=str, default='docs/memory_report.md',
                      help='Path for Markdown report output')
    parser.add_argument('--json-output', type=str, default='data/results/memory_profile.json',
                      help='Path for JSON profile output')
    
    args = parser.parse_args()
    
    stats = run_memory_analysis(args.log, args.md_output, args.json_output)
    
    print(f"\nMemory Analysis Summary:")
    print(f"  Peak Memory: {stats['max_memory_mb']:.2f} MB")
    print(f"  Average Memory: {stats['avg_memory_mb']:.2f} MB")
    print(f"  OOM Events: {stats['oom_events']}")
    print(f"  Efficiency: {stats['memory_efficiency']}")

if __name__ == '__main__':
    main()
