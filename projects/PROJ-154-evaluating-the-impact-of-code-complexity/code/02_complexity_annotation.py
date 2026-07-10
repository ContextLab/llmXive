import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import ast
from radon.complexity import cc_visit
from radon.raw import analyze as radon_raw_analyze
from radon.mi import mi_visit
import numpy as np

# Import from sibling utils as per API surface
from utils.logging_config import setup_deterministic_logging, get_logger
from utils.memory_guard import MemoryGuard, load_config, check_and_abort_or_downsample

# Setup logging
logger = get_logger(__name__)

class ComplexityMetrics:
    """Container for complexity calculation logic."""
    
    @staticmethod
    def calculate_cyclomatic_complexity(code: str) -> float:
        """Calculate Cyclomatic Complexity using radon."""
        try:
            results = cc_visit(code)
            if not results:
                return 0.0
            # Return the max complexity found in the file
            return float(max(r.complexity for r in results))
        except Exception as e:
            logger.warning(f"Failed to calculate cyclomatic complexity: {e}")
            return -1.0

    @staticmethod
    def calculate_halstead_volume(code: str) -> float:
        """Calculate Halstead Volume using radon."""
        try:
            raw = radon_raw_analyze(code)
            return float(raw.v)
        except Exception as e:
            logger.warning(f"Failed to calculate Halstead volume: {e}")
            return -1.0

    @staticmethod
    def calculate_maintainability_index(code: str) -> float:
        """Calculate Maintainability Index using radon."""
        try:
            # mi_visit returns a list of MI scores per block
            mi_scores = mi_visit(code, multi=True)
            if not mi_scores:
                return 100.0 # Default high maintainability if empty
            return float(np.mean(mi_scores))
        except Exception as e:
            logger.warning(f"Failed to calculate Maintainability Index: {e}")
            return -1.0

def calculate_metrics(code: str) -> Dict[str, float]:
    """Calculate all complexity metrics for a code snippet."""
    return {
        'cyclomatic_complexity': ComplexityMetrics.calculate_cyclomatic_complexity(code),
        'halstead_volume': ComplexityMetrics.calculate_halstead_volume(code),
        'maintainability_index': ComplexityMetrics.calculate_maintainability_index(code)
    }

def process_snippet(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single row from the raw dataset.
    Returns a dictionary with code, ground truth, and metrics, or None if invalid.
    """
    code = row.get('code', '')
    if not code:
        return None

    try:
        # Validate syntax by attempting to parse
        ast.parse(code)
    except SyntaxError as e:
        logger.warning(f"Skipping snippet due to syntax error: {e}")
        return None
    
    metrics = calculate_metrics(code)
    
    # Check for calculation failures (returned -1.0)
    if any(v < 0 for v in metrics.values()):
        logger.warning(f"Skipping snippet due to metric calculation failure.")
        return None

    return {
        'snippet_id': row.get('id', 'unknown'),
        'raw_code': code,
        'ground_truth': row.get('docstring', ''),
        'cyclomatic_complexity': metrics['cyclomatic_complexity'],
        'halstead_volume': metrics['halstead_volume'],
        'maintainability_index': metrics['maintainability_index']
    }

def main():
    """
    Main entry point for complexity annotation and data saving.
    Loads processed data from intermediate state (or re-processes if needed),
    saves to annotated_metrics.csv, and updates metadata.json.
    """
    # Setup logging
    setup_deterministic_logging()
    logger.info("Starting Complexity Annotation and Data Saving (T015)")

    # Load configuration
    config = load_config()
    memory_guard = MemoryGuard(config.get('memory_threshold_percent', 80))

    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / 'data'
    processed_dir = data_dir / 'processed'
    raw_dir = data_dir / 'raw'
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Input file (intermediate JSON or CSV from T013/T014 logic)
    # Since T013/T014 are completed, we assume the raw data is available in data/raw/
    # We will re-process the raw dataset to ensure we have the cleanest output
    # matching the spec. The raw dataset is expected to be in a standard format
    # (e.g., JSONL or CSV) from T012.
    # Assuming T012 produced a JSONL file in data/raw/ named 'codesearchnet_python.jsonl'
    # or similar. Let's look for the most recent large JSON file in raw/.
    
    raw_files = list(raw_dir.glob('*.jsonl')) + list(raw_dir.glob('*.json'))
    if not raw_files:
        # Fallback: try to find any json file
        raw_files = list(raw_dir.glob('*.*'))
    
    if not raw_files:
        logger.error("No raw data files found in data/raw/. Please run T012 first.")
        sys.exit(1)
    
    # Sort by size descending to pick the largest dataset
    raw_files.sort(key=lambda p: p.stat().st_size, reverse=True)
    input_file = raw_files[0]
    
    logger.info(f"Processing raw data from: {input_file}")
    
    # Check memory before processing
    check_and_abort_or_downsample(memory_guard, 0)

    all_results = []
    total_raw = 0
    total_valid = 0
    excluded_count = 0

    # Read and process line by line to handle large files
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    row = json.loads(line)
                    total_raw += 1
                    
                    # Check memory periodically
                    if total_raw % 1000 == 0:
                        check_and_abort_or_downsample(memory_guard, total_raw)

                    result = process_snippet(row)
                    if result:
                        all_results.append(result)
                        total_valid += 1
                    else:
                        excluded_count += 1
                
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON line: {e}")
                    total_raw += 1
                    excluded_count += 1
                
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    logger.info(f"Processing complete. Total raw: {total_raw}, Valid: {total_valid}, Excluded: {excluded_count}")

    # Save annotated_metrics.csv
    output_csv_path = processed_dir / 'annotated_metrics.csv'
    df = pd.DataFrame(all_results)
    df.to_csv(output_csv_path, index=False)
    logger.info(f"Saved annotated metrics to: {output_csv_path}")

    # Update metadata.json
    metadata_path = processed_dir / 'metadata.json'
    metadata = {}
    
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    
    metadata['total_raw_snippets'] = total_raw
    metadata['total_valid_snippets'] = total_valid
    metadata['excluded_snippets'] = excluded_count
    metadata['output_file'] = str(output_csv_path.name)
    metadata['last_updated'] = str(pd.Timestamp.now())
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Updated metadata at: {metadata_path}")

    # Log binning boundaries for future tasks (T017) as a placeholder note
    # Actual binning calculation happens in T017, but we log here that data is ready.
    logger.info("Data ready for binning strategy (T017).")

    logger.info("T015 Completed Successfully.")

if __name__ == "__main__":
    main()