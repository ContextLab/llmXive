import os
import sys
import logging
import pandas as pd
import yaml
from logging_config import setup_logging

def check_sensory_deprivation_tags(df, column='condition'):
    """
    Check if the 'condition' column contains sensory deprivation tags.
    
    Args:
        df: Input DataFrame.
        column: Name of the column to check.
    
    Returns:
        Boolean indicating if sensory deprivation tags are found.
    """
    if column not in df.columns:
        return False
    
    # Convert to string and check for keywords
    condition_str = df[column].astype(str).str.lower()
    keywords = ['sensory_deprivation', 'deprivation', 'isolation', 'sensory reduction']
    
    for keyword in keywords:
        if condition_str.str.contains(keyword, na=False).any():
            return True
    
    return False

def validate_required_columns(df):
    """
    Validate that the DataFrame contains required columns.
    
    Args:
        df: Input DataFrame.
    
    Returns:
        Boolean indicating if all required columns are present.
    """
    required_cols = ['condition', 'recall', 'bizarreness', 'participant_id']
    missing = [col for col in required_cols if col not in df.columns]
    return len(missing) == 0, missing

def ingest_csv(filepath):
    """
    Ingest a CSV file into a DataFrame.
    
    Args:
        filepath: Path to the CSV file.
    
    Returns:
        DataFrame containing the ingested data.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Ingesting data from {filepath}")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Successfully ingested {len(df)} rows from {filepath}")
    return df

def auto_generate_data(protocol_path, output_path):
    """
    Trigger synthetic data generation if real data is not found.
    
    Args:
        protocol_path: Path to protocol.yaml.
        output_path: Path where generated data should be saved.
    
    Returns:
        DataFrame containing the generated synthetic data.
    """
    logger = logging.getLogger(__name__)
    logger.warning("No real data found with sensory deprivation tags. "
                   "Triggering synthetic data generation.")
    
    # Import here to avoid circular dependency if needed, 
    # but in this structure we can call the function directly
    from generate_data import generate_synthetic_datasets
    
    df = generate_synthetic_datasets(protocol_path, output_path)
    logger.info(f"Synthetic data generated and saved to {output_path}")
    return df

def run_ingestion(data_dir, protocol_path, output_dir):
    """
    Main ingestion logic: scan for real data, validate, or generate synthetic.
    
    Args:
        data_dir: Directory containing raw data files.
        protocol_path: Path to protocol.yaml.
        output_dir: Directory to save processed/ingested data.
    
    Returns:
        DataFrame containing the final ingested dataset.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting data ingestion process.")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Scan for CSV files
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not csv_files:
        logger.info(f"No CSV files found in {data_dir}. Generating synthetic data.")
        return auto_generate_data(protocol_path, output_dir)
    
    final_dfs = []
    found_real_data = False
    
    for csv_file in csv_files:
        filepath = os.path.join(data_dir, csv_file)
        try:
            df = ingest_csv(filepath)
            
            # Check for sensory deprivation tags
            has_tags = check_sensory_deprivation_tags(df)
            is_valid, missing = validate_required_columns(df)
            
            if has_tags and is_valid:
                logger.info(f"Real data found in {csv_file} with valid structure.")
                df['data_source'] = 'real'
                final_dfs.append(df)
                found_real_data = True
            else:
                if not is_valid:
                    logger.warning(f"File {csv_file} missing columns: {missing}. Skipping.")
                else:
                    logger.info(f"File {csv_file} does not contain sensory deprivation tags. Skipping.")
                    
        except Exception as e:
            logger.error(f"Error ingesting {csv_file}: {str(e)}")
            continue
    
    if not found_real_data:
        logger.warning("No valid real data found. Generating synthetic data.")
        return auto_generate_data(protocol_path, output_dir)
    
    # Combine all valid real data
    combined_df = pd.concat(final_dfs, ignore_index=True)
    logger.info(f"Ingestion complete. Total rows: {len(combined_df)}")
    
    return combined_df

def main():
    """Main entry point for ingestion."""
    # Setup logging
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"ingest_{timestamp}.log")
    setup_logging(log_file=log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting data ingestion pipeline.")
    
    # Paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data", "raw")
    protocol_path = os.path.join(project_root, "data", "protocols", "protocol.yaml")
    output_dir = os.path.join(project_root, "data", "processed")
    
    # Create raw data dir if it doesn't exist (for safety if empty)
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        df = run_ingestion(data_dir, protocol_path, output_dir)
        
        # Save ingested data
        output_file = os.path.join(output_dir, "ingested_data.csv")
        df.to_csv(output_file, index=False)
        logger.info(f"Saved ingested data to {output_file}")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise

if __name__ == "__main__":
    from datetime import datetime
    main()