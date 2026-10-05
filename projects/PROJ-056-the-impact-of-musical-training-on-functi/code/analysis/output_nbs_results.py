import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from utils.logging import get_logger

logger = get_logger(__name__)

def load_nbs_results(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load NBS results from a CSV file.
    
    Args:
        input_path: Path to the NBS results CSV. If None, uses default path.
        
    Returns:
        DataFrame containing NBS results.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or has invalid format.
    """
    if input_path is None:
        input_path = "data/processed/nbs_raw_results.csv"
        
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"NBS results file not found: {input_path}")
        
    df = pd.read_csv(path)
    
    if df.empty:
        raise ValueError(f"NBS results file is empty: {input_path}")
        
    required_columns = ['component_id', 'size_edges', 'p_value_fwer']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"NBS results missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} NBS components from {input_path}")
    return df

def write_nbs_results(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Write NBS results to a CSV file.
    
    Args:
        df: DataFrame containing NBS results with columns:
            - component_id
            - size_edges
            - p_value_fwer
        output_path: Path to write the CSV. If None, uses default path.
        
    Returns:
        Path to the written file.
        
    Raises:
        ValueError: If DataFrame is missing required columns.
        IOError: If writing fails.
    """
    if output_path is None:
        output_path = "data/processed/nbs_results.csv"
        
    required_columns = ['component_id', 'size_edges', 'p_value_fwer']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"DataFrame missing required columns: {missing_cols}")
        
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} NBS components to {output_path}")
    return output_path

def process_nbs_output(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    sort_by: str = 'p_value_fwer'
) -> pd.DataFrame:
    """
    Process NBS results: load, sort, and write to output file.
    
    Args:
        input_path: Path to input NBS results CSV.
        output_path: Path to write processed results.
        sort_by: Column to sort by (default: 'p_value_fwer').
        
    Returns:
        Processed DataFrame.
    """
    logger.info("Processing NBS output...")
    
    # Load results
    df = load_nbs_results(input_path)
    
    # Sort by p-value (ascending)
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=True).reset_index(drop=True)
        logger.info(f"Sorted results by {sort_by}")
    
    # Write to output
    write_nbs_results(df, output_path)
    
    return df

def main():
    """Main entry point for NBS results processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process NBS results")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/nbs_raw_results.csv",
        help="Input NBS results CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/nbs_results.csv",
        help="Output processed NBS results CSV file"
    )
    parser.add_argument(
        "--sort-by",
        type=str,
        default="p_value_fwer",
        help="Column to sort results by"
    )
    
    args = parser.parse_args()
    
    try:
        df = process_nbs_output(
            input_path=args.input,
            output_path=args.output,
            sort_by=args.sort_by
        )
        logger.info(f"Successfully processed NBS results. Output: {args.output}")
        print(f"NBS Results Summary:")
        print(f"  Total components: {len(df)}")
        if 'p_value_fwer' in df.columns:
            significant = df[df['p_value_fwer'] < 0.05]
            print(f"  Significant components (p<0.05): {len(significant)}")
            if not significant.empty:
                print(f"  Largest component size: {significant['size_edges'].max()} edges")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
