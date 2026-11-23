"""
Data loading module for eye-tracking data.

Ingests raw eye-tracking files (.edf, .csv) from verified sources
and converts them to a uniform CSV schema.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import yaml

# Try to import EDF reader
try:
    import pyedflib
    EDF_AVAILABLE = True
except ImportError:
    EDF_AVAILABLE = False
    logging.warning("pyedflib not available. EDF files will not be supported.")

from config import load_config
from utils.provenance import hash_file, write_meta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_data_from_dataset(dataset_path: Path) -> pd.DataFrame:
    """
    Load raw eye-tracking data from a directory containing .edf or .csv files.
    
    Args:
        dataset_path: Path to the directory containing raw data files.
        
    Returns:
        DataFrame with columns: timestamp, x, y, pupil_diameter
        
    Raises:
        RuntimeError: If no valid data files are found or if EDF files are requested
                      but pyedflib is not installed.
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {dataset_path}")
    
    all_data = []
    edf_files = list(dataset_path.glob("*.edf"))
    csv_files = list(dataset_path.glob("*.csv"))
    
    if not edf_files and not csv_files:
        raise ValueError(f"No .edf or .csv files found in {dataset_path}")
    
    logger.info(f"Found {len(edf_files)} EDF files and {len(csv_files)} CSV files")
    
    # Process EDF files
    if edf_files:
        if not EDF_AVAILABLE:
            raise RuntimeError(
                "EDF files found but pyedflib is not installed. "
                "Install it with: pip install pyedflib"
            )
        
        for edf_file in edf_files:
            logger.info(f"Processing EDF file: {edf_file}")
            try:
                data_df = _read_edf_file(edf_file)
                if data_df is not None and not data_df.empty:
                    all_data.append(data_df)
            except Exception as e:
                logger.error(f"Error processing {edf_file}: {e}")
                raise
    
    # Process CSV files
    for csv_file in csv_files:
        logger.info(f"Processing CSV file: {csv_file}")
        try:
            data_df = _read_csv_file(csv_file)
            if data_df is not None and not data_df.empty:
                all_data.append(data_df)
        except Exception as e:
            logger.error(f"Error processing {csv_file}: {e}")
            raise
    
    if not all_data:
        raise ValueError("No valid data could be extracted from any files")
    
    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"Combined data shape: {combined_df.shape}")
    
    return combined_df

def _read_edf_file(edf_path: Path) -> Optional[pd.DataFrame]:
    """
    Read data from an EDF file using pyedflib.
    
    Args:
        edf_path: Path to the EDF file.
        
    Returns:
        DataFrame with eye-tracking data or None if no data found.
    """
    try:
        with pyedflib.EdfReader(str(edf_path)) as edf:
            n_signals = edf.signals_in_file
            signal_labels = edf.getSignalLabels()
            
            # Look for eye-tracking channels
            pupil_channel = None
            x_channel = None
            y_channel = None
            timestamp_channel = None
            
            for i, label in enumerate(signal_labels):
                label_lower = label.lower()
                if 'pupil' in label_lower or 'size' in label_lower:
                    pupil_channel = i
                elif 'x' in label_lower and ('eye' in label_lower or 'pos' in label_lower):
                    x_channel = i
                elif 'y' in label_lower and ('eye' in label_lower or 'pos' in label_lower):
                    y_channel = i
                elif 'time' in label_lower or 'timestamp' in label_lower:
                    timestamp_channel = i
            
            # If specific channels not found, try to use first few channels
            if pupil_channel is None and n_signals > 0:
                pupil_channel = 0
            if x_channel is None and n_signals > 1:
                x_channel = 1
            if y_channel is None and n_signals > 2:
                y_channel = 2
            
            # Read data
            signals = []
            for i in range(min(3, n_signals)):
                signals.append(edf.readSignal(i))
            
            if len(signals) < 3:
                logger.warning(f"Not enough signals in {edf_path}")
                return None
            
            # Create DataFrame
            df = pd.DataFrame({
                'timestamp': np.arange(len(signals[0])) * (1.0 / edf.getSampleFrequency(0)),
                'x': signals[0] if x_channel == 0 else (signals[1] if x_channel == 1 else signals[2]),
                'y': signals[0] if y_channel == 0 else (signals[1] if y_channel == 1 else signals[2]),
                'pupil_diameter': signals[0] if pupil_channel == 0 else (signals[1] if pupil_channel == 1 else signals[2])
            })
            
            return df
            
    except Exception as e:
        logger.error(f"Failed to read EDF file {edf_path}: {e}")
        raise

def _read_csv_file(csv_path: Path) -> Optional[pd.DataFrame]:
    """
    Read data from a CSV file.
    
    Args:
        csv_path: Path to the CSV file.
        
    Returns:
        DataFrame with eye-tracking data or None if no data found.
    """
    try:
        # Try to read with common column names
        df = pd.read_csv(csv_path)
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Look for required columns
        timestamp_col = None
        x_col = None
        y_col = None
        pupil_col = None
        
        for col in df.columns:
            if 'time' in col and 'stamp' in col:
                timestamp_col = col
            elif 'time' in col:
                timestamp_col = col
            elif col in ['x', 'x_pos', 'x_position', 'horizontal']:
                x_col = col
            elif col in ['y', 'y_pos', 'y_position', 'vertical']:
                y_col = col
            elif 'pupil' in col or 'size' in col or 'diameter' in col:
                pupil_col = col
        
        # If not found, assume standard positions
        if timestamp_col is None and len(df.columns) >= 4:
            timestamp_col = df.columns[0]
        if x_col is None and len(df.columns) >= 4:
            x_col = df.columns[1]
        if y_col is None and len(df.columns) >= 4:
            y_col = df.columns[2]
        if pupil_col is None and len(df.columns) >= 4:
            pupil_col = df.columns[3]
        
        if not all([timestamp_col, x_col, y_col, pupil_col]):
            logger.warning(f"Could not identify all required columns in {csv_path}")
            return None
        
        # Create standardized DataFrame
        result_df = pd.DataFrame({
            'timestamp': pd.to_numeric(df[timestamp_col], errors='coerce'),
            'x': pd.to_numeric(df[x_col], errors='coerce'),
            'y': pd.to_numeric(df[y_col], errors='coerce'),
            'pupil_diameter': pd.to_numeric(df[pupil_col], errors='coerce')
        })
        
        # Drop rows with NaN values
        result_df = result_df.dropna()
        
        return result_df
        
    except Exception as e:
        logger.error(f"Failed to read CSV file {csv_path}: {e}")
        raise

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the DataFrame has the correct column types and names.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Normalized DataFrame with required columns and types.
    """
    required_cols = ['timestamp', 'x', 'y', 'pupil_diameter']
    
    # Ensure columns exist
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Convert to correct types
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
    df['x'] = pd.to_numeric(df['x'], errors='coerce')
    df['y'] = pd.to_numeric(df['y'], errors='coerce')
    df['pupil_diameter'] = pd.to_numeric(df['pupil_diameter'], errors='coerce')
    
    # Drop rows with NaN values
    df = df.dropna()
    
    # Reset index
    df = df.reset_index(drop=True)
    
    # Convert timestamp to milliseconds if it's in seconds
    if df['timestamp'].max() < 1000:  # Assuming data is in seconds if max < 1000
        df['timestamp'] = df['timestamp'] * 1000
    
    return df

def save_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the DataFrame to a CSV file.
    
    Args:
        df: DataFrame to save.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")
    
    # Generate provenance metadata
    meta = {
        'source': str(output_path),
        'timestamp': pd.Timestamp.now().isoformat(),
        'rows': len(df),
        'columns': list(df.columns)
    }
    write_meta(output_path, meta)

def process_single_file(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Process a single input file and save to output.
    
    Args:
        input_path: Path to input file.
        output_path: Path to output CSV.
        
    Returns:
        Processed DataFrame.
    """
    if input_path.suffix.lower() == '.edf':
        df = _read_edf_file(input_path)
    elif input_path.suffix.lower() == '.csv':
        df = _read_csv_file(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")
    
    if df is None or df.empty:
        raise ValueError(f"No data could be extracted from {input_path}")
    
    df = normalize_columns(df)
    save_to_csv(df, output_path)
    
    return df

def run_loading_pipeline(config_path: Optional[str] = None, 
                       output_path: Optional[str] = None) -> Path:
    """
    Run the full data loading pipeline.
    
    Args:
        config_path: Path to config.yaml. If None, uses default location.
        output_path: Path for output CSV. If None, uses default location.
        
    Returns:
        Path to the output CSV file.
    """
    config = load_config(config_path)
    
    # Get input and output paths from config
    data_dir = Path(config['paths'].get('data_raw', 'data/raw'))
    output_file = Path(output_path) if output_path else Path(config['paths'].get('data_processed', 'data/processed')) / 'raw_converted.csv'
    
    logger.info(f"Loading data from: {data_dir}")
    logger.info(f"Output will be saved to: {output_file}")
    
    # Load data
    raw_df = load_raw_data_from_dataset(data_dir)
    
    # Normalize columns
    processed_df = normalize_columns(raw_df)
    
    # Save to CSV
    save_to_csv(processed_df, output_file)
    
    return output_file

def main():
    """Main entry point for the data loading script."""
    parser = argparse.ArgumentParser(description='Load and convert eye-tracking data')
    parser.add_argument('--config', type=str, help='Path to config.yaml')
    parser.add_argument('--output', type=str, help='Path to output CSV file')
    parser.add_argument('--input', type=str, help='Path to input directory (overrides config)')
    
    args = parser.parse_args()
    
    try:
        output_path = run_loading_pipeline(
            config_path=args.config,
            output_path=args.output
        )
        print(f"Data loading complete. Output saved to: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
