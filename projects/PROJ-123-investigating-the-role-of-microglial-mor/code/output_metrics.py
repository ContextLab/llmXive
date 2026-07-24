import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from code.config import get_path, ensure_dirs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_processed_intermediates() -> pd.DataFrame:
    """Load processed intermediate data."""
    default_path = get_path('processed', 'morphological_metrics.csv')
    if os.path.exists(default_path):
        return pd.read_csv(default_path)
    else:
        raise FileNotFoundError(f"Processed data not found at {default_path}")

def format_sholl_vector(sholl_data: Any) -> str:
    """Format Sholl intersection data for CSV export."""
    if isinstance(sholl_data, list):
        return json.dumps({f"{i*5}um": val for i, val in enumerate(sholl_data)})
    elif isinstance(sholl_data, dict):
        return json.dumps(sholl_data)
    else:
        return str(sholl_data)

def aggregate_and_save_metrics(df: pd.DataFrame) -> str:
    """Aggregate and save morphological metrics to CSV."""
    output_path = get_path('processed', 'morphological_metrics.csv')
    ensure_dirs(output_path)
    
    # Format Sholl data
    if 'sholl_intersections' in df.columns:
        df['sholl_intersections'] = df['sholl_intersections'].apply(format_sholl_vector)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Morphological metrics saved to {output_path}")
    
    return output_path

def run_output_pipeline(input_path: Optional[str] = None) -> str:
    """Run the output pipeline to generate final metrics CSV."""
    if input_path:
        df = pd.read_csv(input_path)
    else:
        try:
            df = load_processed_intermediates()
        except FileNotFoundError:
            logger.warning("No processed data found. Generating from synthetic data...")
            from code.synthetic_data import run_synthetic_pipeline
            synthetic_path = run_synthetic_pipeline()
            df = pd.read_csv(synthetic_path)
    
    output_path = aggregate_and_save_metrics(df)
    return output_path

def main():
    """Main entry point for output pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run output metrics pipeline')
    parser.add_argument('--input', type=str, help='Input CSV file path')
    
    args = parser.parse_args()
    
    run_output_pipeline(input_path=args.input)

if __name__ == '__main__':
    main()
