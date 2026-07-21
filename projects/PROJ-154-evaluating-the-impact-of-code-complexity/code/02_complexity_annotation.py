import os
import sys
import json
import logging
import traceback
from pathlib import Path

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_deterministic_logging, set_seed
from utils.memory_guard import MemoryGuard, load_config
import pandas as pd
import csv
from radon.complexity import cc_visit
from radon.halstead import halstead_visit
from radon.mi import mi_visit
from radon.raw import analyze

# Setup logging
logger = setup_deterministic_logging()
set_seed(42)

class ComplexityMetrics:
    """Helper class to calculate various complexity metrics."""
    
    @staticmethod
    def calculate_cyclomatic_complexity(code: str) -> float:
        """Calculate Cyclomatic Complexity using radon."""
        try:
            results = cc_visit(code)
            if not results:
                return 0.0
            # Return max CC for the file (or sum if preferred, but max is standard for function-level)
            return float(max(r.complexity for r in results))
        except Exception as e:
            logger.warning(f"Failed to calculate CC: {e}")
            return 0.0

    @staticmethod
    def calculate_halstead_volume(code: str) -> float:
        """Calculate Halstead Volume using radon."""
        try:
            results = halstead_visit(code)
            if not results:
                return 0.0
            # Return max volume
            return float(max(r.volume for r in results))
        except Exception as e:
            logger.warning(f"Failed to calculate Halstead: {e}")
            return 0.0

    @staticmethod
    def calculate_maintainability_index(code: str) -> float:
        """Calculate Maintainability Index using radon."""
        try:
            results = mi_visit(code, multi=True)
            if not results:
                return 0.0
            # Return average MI
            return float(sum(results) / len(results))
        except Exception as e:
            logger.warning(f"Failed to calculate MI: {e}")
            return 0.0

def calculate_metrics(code: str) -> dict:
    """Calculate all complexity metrics for a code snippet."""
    metrics = ComplexityMetrics()
    return {
        'cyclomatic_complexity': metrics.calculate_cyclomatic_complexity(code),
        'halstead_volume': metrics.calculate_halstead_volume(code),
        'maintainability_index': metrics.calculate_maintainability_index(code)
    }

def process_snippet(row: dict) -> dict:
    """Process a single row from the dataset, calculating metrics and handling errors."""
    snippet_id = row.get('snippet_id', row.get('path', 'unknown'))
    code = row.get('code', '')
    ground_truth = row.get('docstring', '')
    
    if not code or not isinstance(code, str):
        return None, f"Empty or invalid code for snippet {snippet_id}"
    
    try:
        # Validate syntax by attempting to parse (radon does this implicitly, but explicit check is safer)
        compile(code, '<string>', 'exec')
        
        metrics = calculate_metrics(code)
        
        result = {
            'snippet_id': snippet_id,
            'code': code,
            'ground_truth': ground_truth,
            'cyclomatic_complexity': metrics['cyclomatic_complexity'],
            'halstead_volume': metrics['halstead_volume'],
            'maintainability_index': metrics['maintainability_index']
        }
        return result, None
    except SyntaxError as e:
        return None, f"SyntaxError in snippet {snippet_id}: {e}"
    except Exception as e:
        return None, f"Unexpected error in snippet {snippet_id}: {e}"

def main():
    """Main entry point for complexity annotation and saving processed data."""
    logger.info("Starting complexity annotation and data saving process (T015).")
    
    # Paths
    base_dir = Path(__file__).parent.parent
    raw_data_path = base_dir / "data" / "raw" / "codesearchnet_python_processed.csv"
    processed_dir = base_dir / "data" / "processed"
    output_csv_path = processed_dir / "annotated_metrics.csv"
    metadata_path = processed_dir / "metadata.json"
    exclusions_log_path = processed_dir / "exclusions.log"
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load config for memory guard (optional but good practice)
    config = load_config()
    memory_guard = MemoryGuard(config)
    memory_guard.start_monitoring()
    
    # Check if raw data exists
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found at {raw_data_path}. Please run 01_data_acquisition.py first.")
        sys.exit(1)
    
    # Read raw data
    logger.info(f"Loading raw data from {raw_data_path}")
    try:
        df = pd.read_csv(raw_data_path)
        total_raw_snippets = len(df)
        logger.info(f"Loaded {total_raw_snippets} raw snippets.")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        sys.exit(1)
    
    # Process snippets
    processed_rows = []
    exclusions = []
    
    logger.info("Processing snippets and calculating complexity metrics...")
    
    for idx, row in df.iterrows():
        # Check memory periodically
        if idx % 1000 == 0:
            memory_guard.check_memory()
        
        result, error = process_snippet(row)
        if result:
            processed_rows.append(result)
        else:
            exclusions.append({
                'index': idx,
                'snippet_id': row.get('snippet_id', row.get('path', 'unknown')),
                'error': error
            })
            logger.warning(f"Skipping snippet {row.get('snippet_id', 'unknown')}: {error}")
    
    total_valid_snippets = len(processed_rows)
    logger.info(f"Processing complete. Valid snippets: {total_valid_snippets}, Excluded: {len(exclusions)}")
    
    # Write exclusions log
    with open(exclusions_log_path, 'w') as f:
        for exc in exclusions:
            f.write(f"Index: {exc['index']}, ID: {exc['snippet_id']}, Error: {exc['error']}\n")
    logger.info(f"Exclusions written to {exclusions_log_path}")
    
    # Save processed data to CSV
    logger.info(f"Saving processed data to {output_csv_path}")
    if processed_rows:
        df_processed = pd.DataFrame(processed_rows)
        # Ensure specific column order
        columns = ['snippet_id', 'code', 'ground_truth', 'cyclomatic_complexity', 'halstead_volume', 'maintainability_index']
        # Filter columns to only those present (in case some are missing, though they shouldn't be)
        existing_cols = [c for c in columns if c in df_processed.columns]
        df_processed = df_processed[existing_cols]
        df_processed.to_csv(output_csv_path, index=False)
        logger.info(f"Saved {total_valid_snippets} rows to {output_csv_path}")
    else:
        logger.warning("No valid snippets to save. Creating empty CSV.")
        pd.DataFrame(columns=columns).to_csv(output_csv_path, index=False)
    
    # Update metadata.json
    logger.info(f"Updating metadata at {metadata_path}")
    metadata = {}
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except json.JSONDecodeError:
            metadata = {}
    
    metadata['total_raw_snippets'] = total_raw_snippets
    metadata['total_valid_snippets'] = total_valid_snippets
    metadata['total_excluded_snippets'] = len(exclusions)
    metadata['last_annotation_run'] = str(pd.Timestamp.now())
    metadata['annotation_status'] = 'completed'
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info("Metadata updated successfully.")
    logger.info("Task T015 completed successfully.")

if __name__ == "__main__":
    main()
