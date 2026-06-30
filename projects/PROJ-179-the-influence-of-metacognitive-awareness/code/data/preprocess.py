import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Import configuration
from config.env_config import load_config, setup_logging, get_seed

logger = logging.getLogger(__name__)

def setup_directories():
    """Ensure output directories exist."""
    cfg = load_config()
    derived_dir = Path(cfg.get('paths', {}).get('derived', 'data/derived'))
    derived_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {derived_dir}")
    return derived_dir

def load_and_clean_data(input_path: str) -> pd.DataFrame:
    """
    Load the raw dataset and perform basic cleaning.
    """
    logger.info(f"Loading dataset from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Dataset not found at {input_path}. Ensure T005 (download.py) has successfully executed.")
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
        
        # Basic cleaning: drop rows with missing critical fields
        required_cols = ['participant_id', 'trial_id', 'source_label', 'participant_response', 'confidence_rating']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Required fields missing: {missing_cols}")
        
        # Drop rows with NaN in critical columns
        initial_count = len(df)
        df = df.dropna(subset=required_cols)
        dropped = initial_count - len(df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows due to missing critical values.")
        
        return df
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def extract_trial_data(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Extract and format trial-wise data according to the specification.
    Ensures correct data types and column mapping.
    """
    logger.info("Extracting trial data...")
    
    # Map columns based on config (with defaults)
    col_map = {
        'participant_id': cfg.get('columns', {}).get('participant_id', 'participant_id'),
        'trial_id': cfg.get('columns', {}).get('trial_id', 'trial_id'),
        'stimulus_modality': cfg.get('columns', {}).get('stimulus_modality', 'stimulus_modality'),
        'source_label': cfg.get('columns', {}).get('source_label', 'source_label'),
        'participant_response': cfg.get('columns', {}).get('participant_response', 'participant_response'),
        'confidence_rating': cfg.get('columns', {}).get('confidence_rating', 'confidence_rating')
    }
    
    # Ensure all mapped columns exist, if not, use original names if they exist
    final_cols = {}
    for key, source in col_map.items():
        if source in df.columns:
            final_cols[key] = source
        else:
            # Fallback: check if key itself exists in df
            if key in df.columns:
                final_cols[key] = key
            else:
                logger.warning(f"Column mapping failed for {key} (expected {source}). Column not found.")
                # We will fail later if truly missing, but let's proceed to see all issues
                final_cols[key] = None

    # Build the output dataframe
    output_data = []
    for _, row in df.iterrows():
        # Extract values safely
        p_id = row.get(final_cols.get('participant_id', ''), '')
        t_id = row.get(final_cols.get('trial_id', ''), '')
        modality = row.get(final_cols.get('stimulus_modality', ''), 'unknown')
        source = row.get(final_cols.get('source_label', ''), 'unknown')
        response = row.get(final_cols.get('participant_response', ''), '')
        confidence = row.get(final_cols.get('confidence_rating'), 0.0)
        
        # Convert types safely
        try:
            confidence = float(confidence) if confidence is not None else 0.0
        except (ValueError, TypeError):
            confidence = 0.0
            logger.warning(f"Invalid confidence rating: {confidence} for trial {t_id}")

        output_data.append({
            'participant_id': str(p_id),
            'trial_id': str(t_id),
            'stimulus_modality': str(modality).lower(),
            'source_label': str(source).lower(),
            'participant_response': str(response),
            'confidence_rating': confidence
        })

    result_df = pd.DataFrame(output_data)
    logger.info(f"Extracted {len(result_df)} valid trials.")
    return result_df

def write_output(df: pd.DataFrame, output_path: Path):
    """Write the processed dataframe to CSV."""
    logger.info(f"Writing output to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Output written successfully.")

def main():
    """Main entry point for preprocessing."""
    # Setup logging
    setup_logging()
    
    # Load configuration
    cfg = load_config()
    
    # Setup directories
    output_dir = setup_directories()
    output_file = output_dir / "trial_data.csv"
    
    # Check for input file
    # T006 validated the dataset, so we expect it to be in data/
    # Common output from download.py is data/ds003386_behavioral.csv or similar
    input_file = Path("data/ds003386_behavioral.csv")
    if not input_file.exists():
        # Try to find any csv in data/
        data_files = list(Path("data").glob("*.csv"))
        if data_files:
            input_file = data_files[0]
            logger.info(f"Input file not found at default, using: {input_file}")
        else:
            logger.error("No input CSV found in data/ directory. Run T005 first.")
            sys.exit(1)
    
    try:
        # Load and clean
        df_raw = load_and_clean_data(str(input_file))
        
        # Extract trial data
        df_processed = extract_trial_data(df_raw, cfg)
        
        # Write output
        write_output(df_processed, output_file)
        
        logger.info("Preprocessing completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()