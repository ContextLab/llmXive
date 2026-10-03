import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class FailureCategory:
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    OOM = "out_of_memory"
    UNKNOWN = "unknown"

def classify_failure(log: str) -> str:
    """
    Classify a failure log into a specific failure category.
    
    Rules:
    - "missing context": log contains "file not found", "cannot locate", or references a file not in input context.
    - "reasoning error": file exists but logic fails.
    - "timeout": execution exceeded time limit.
    - "oom": out of memory.
    - "unknown": default if no pattern matches.
    """
    if not log:
        return FailureCategory.UNKNOWN
    
    log_lower = log.lower()
    
    # Check for timeout
    if "timeout" in log_lower or "timed out" in log_lower or "deadline exceeded" in log_lower:
        return FailureCategory.TIMEOUT
    
    # Check for OOM
    if "out of memory" in log_lower or "oom" in log_lower or "memory error" in log_lower:
        return FailureCategory.OOM
    
    # Check for missing context indicators
    missing_indicators = [
        "file not found", "cannot locate", "no such file", 
        "file does not exist", "import error", "module not found",
        "cannot import name"
    ]
    
    for indicator in missing_indicators:
        if indicator in log_lower:
            return FailureCategory.MISSING_CONTEXT
    
    # Check for reasoning errors (logic failures when files exist)
    reasoning_indicators = [
        "assertion error", "type error", "value error", 
        "logic error", "incorrect output", "failed to solve",
        "unit test failed", "expected", "but got"
    ]
    
    for indicator in reasoning_indicators:
        if indicator in log_lower:
            return FailureCategory.REASONING_ERROR
    
    return FailureCategory.UNKNOWN

def process_results(input_path: Path) -> List[Dict[str, Any]]:
    """
    Process a JSONL file and add failure classifications to each record.
    
    Args:
        input_path: Path to the input JSONL file
        
    Returns:
        List of processed records with added 'failure_category' field
    """
    results = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                log = record.get('log', '') or record.get('error', '') or ''
                
                if not log and record.get('status') != 'success':
                    # If status is not success but no log, assume unknown failure
                    log = "No error log provided"
                
                failure_category = classify_failure(log)
                record['failure_category'] = failure_category
                results.append(record)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                continue
            
            except Exception as e:
                logger.error(f"Error processing line {line_num}: {e}")
                continue
    
    return results

def aggregate_failure_modes(input_paths: List[Path], output_path: Path) -> Dict[str, Any]:
    """
    Aggregate failure modes across multiple input files and generate a summary report.
    
    Args:
        input_paths: List of paths to input JSONL files
        output_path: Path to write the summary report (JSON)
        
    Returns:
        Dictionary containing the aggregated failure statistics
    """
    # Structure: {strategy: {model: {category: count}}}
    aggregated = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    total_counts = defaultdict(int)
    grand_total = 0
    
    for input_path in input_paths:
        if not input_path.exists():
            logger.warning(f"Input file not found: {input_path}, skipping")
            continue
        
        logger.info(f"Processing {input_path}")
        records = process_results(input_path)
        
        # Infer strategy and model from filename if not in record
        # Expected patterns: baseline_run.jsonl, hf_run_1b_*.jsonl, hf_run_7b_*.jsonl
        filename = input_path.stem
        inferred_strategy = "baseline" if "baseline" in filename else "high_fidelity"
        inferred_model = "1B" if "1b" in filename.lower() else ("7B" if "7b" in filename.lower() else "unknown")
        
        # Extract strategy from filename more precisely
        if "_tfidf" in filename:
            inferred_strategy = "tfidf"
        elif "_diff" in filename or "_diff_aware" in filename:
            inferred_strategy = "diff_aware"
        elif "_summ" in filename or "_summarization" in filename:
            inferred_strategy = "summarization"
        elif "baseline" in filename:
            inferred_strategy = "baseline"
        
        # Extract model from filename
        if "1b" in filename.lower():
            inferred_model = "1B"
        elif "7b" in filename.lower():
            inferred_model = "7B"
        
        for record in records:
            # Use record values if available, otherwise use inferred
            strategy = record.get('strategy', inferred_strategy)
            model = record.get('model_size', record.get('model', inferred_model))
            category = record.get('failure_category', classify_failure(record.get('log', '')))
            
            aggregated[strategy][model][category] += 1
            total_counts[category] += 1
            grand_total += 1
    
    # Calculate percentages
    summary = {
        "total_records": grand_total,
        "by_strategy": {},
        "by_model": {},
        "overall": {}
    }
    
    # Overall percentages
    for category, count in total_counts.items():
        pct = (count / grand_total * 100) if grand_total > 0 else 0
        summary["overall"][category] = {
            "count": count,
            "percentage": round(pct, 2)
        }
    
    # By strategy
    for strategy, models in aggregated.items():
        strategy_total = sum(sum(counts.values()) for counts in models.values())
        summary["by_strategy"][strategy] = {
            "total": strategy_total,
            "by_model": {},
            "by_category": {}
        }
        
        strategy_counts = defaultdict(int)
        for model, categories in models.items():
            model_total = sum(categories.values())
            summary["by_strategy"][strategy]["by_model"][model] = {
                "total": model_total,
                "categories": {}
            }
            
            for category, count in categories.items():
                pct = (count / strategy_total * 100) if strategy_total > 0 else 0
                summary["by_strategy"][strategy]["by_model"][model]["categories"][category] = {
                    "count": count,
                    "percentage": round(pct, 2)
                }
                strategy_counts[category] += count
        
        for category, count in strategy_counts.items():
            pct = (count / strategy_total * 100) if strategy_total > 0 else 0
            summary["by_strategy"][strategy]["by_category"][category] = {
                "count": count,
                "percentage": round(pct, 2)
            }
    
    # Write summary to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Failure mode summary written to {output_path}")
    return summary

def main():
    """
    Main entry point for failure mode aggregation.
    
    Usage:
        python code/analysis/failure_classifier.py --input 'data/intermediate/*.jsonl' --output data/intermediate/failure_summary.json
    """
    parser = argparse.ArgumentParser(description='Aggregate failure modes from execution results')
    parser.add_argument('--input', nargs='+', required=True, 
                      help='Input JSONL files (glob patterns supported)')
    parser.add_argument('--output', required=True,
                      help='Output JSON file for failure summary')
    parser.add_argument('--log-level', default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Expand glob patterns
    input_paths = []
    for pattern in args.input:
        path = Path(pattern)
        if '*' in pattern:
            # Handle glob patterns
            parent = path.parent
            if not str(parent) or parent == Path('.'):
                parent = Path('.')
            matches = list(parent.glob(path.name))
            input_paths.extend(matches)
        else:
            input_paths.append(path)
    
    if not input_paths:
        logger.error("No input files found matching the provided patterns")
        sys.exit(1)
    
    # Validate output path
    output_path = Path(args.output)
    if not output_path.suffix == '.json':
        logger.warning("Output file does not have .json extension, adding it")
        output_path = output_path.with_suffix('.json')
    
    # Run aggregation
    try:
        summary = aggregate_failure_modes(input_paths, output_path)
        
        # Print summary to console
        logger.info(f"\n=== Failure Mode Summary ===")
        logger.info(f"Total records processed: {summary['total_records']}")
        logger.info(f"\nOverall distribution:")
        for category, stats in summary['overall'].items():
            logger.info(f"  {category}: {stats['count']} ({stats['percentage']}%)")
        
        logger.info(f"\nDetailed breakdown by strategy:")
        for strategy, data in summary['by_strategy'].items():
            logger.info(f"  {strategy} (total: {data['total']}):")
            for category, stats in data['by_category'].items():
                logger.info(f"    {category}: {stats['count']} ({stats['percentage']}%)")
        
        logger.info(f"\nReport saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to aggregate failure modes: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()