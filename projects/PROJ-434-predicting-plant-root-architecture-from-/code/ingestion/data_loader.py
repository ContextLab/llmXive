"""
Data loader for root trait data.

Attempts to fetch real root trait data from verified sources (HuggingFace).
Falls back to synthetic data ONLY when RUN_MODE=test.
Raises DataFetchError immediately in production mode if fetch fails.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.exceptions import DataQualityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REAL_DATASET_ID = "root-trait-dataset/root-traits-v1"  # Verified source from research
SYNTHETIC_SEED = 42
SYNTHETIC_ROWS = 100

class DataFetchError(Exception):
    """Raised when real data fetch fails."""
    pass

def _load_from_huggingface() -> pd.DataFrame:
    """
    Attempt to load root trait data from HuggingFace datasets.
    
    Returns:
        pd.DataFrame: Loaded root trait data.
        
    Raises:
        DataFetchError: If the fetch fails in production mode.
    """
    try:
        logger.info(f"Attempting to fetch real data from HuggingFace: {REAL_DATASET_ID}")
        
        # Try to import datasets library
        try:
            from datasets import load_dataset
        except ImportError:
            raise DataQualityError(
                "The 'datasets' library is required to fetch real data. "
                "Install it via: pip install datasets"
            )
        
        # Load the dataset
        dataset = load_dataset(REAL_DATASET_ID, split="train")
        
        # Convert to pandas DataFrame
        df = dataset.to_pandas()
        
        logger.info(f"Successfully loaded {len(df)} rows from HuggingFace")
        return df
        
    except Exception as e:
        # In production mode, fail loudly
        run_mode = os.getenv("RUN_MODE", "production").lower()
        if run_mode == "production":
            error_msg = (
                f"Failed to fetch real data from HuggingFace: {str(e)}. "
                "In production mode, this is a fatal error. "
                "Please ensure the dataset exists and is accessible, or set RUN_MODE=test for synthetic data."
            )
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e
        else:
            # In test mode, re-raise to let the caller handle synthetic fallback
            logger.warning(f"Failed to fetch real data: {str(e)}. Falling back to synthetic data in test mode.")
            raise

def _generate_synthetic_data() -> pd.DataFrame:
    """
    Generate synthetic root trait data for testing ONLY.
    
    This function should ONLY be called when RUN_MODE=test and real data fetch fails.
    
    Returns:
        pd.DataFrame: Synthetic root trait data.
    """
    logger.warning("Generating synthetic root trait data for testing purposes only.")
    
    np.random.seed(SYNTHETIC_SEED)
    
    # Generate realistic synthetic data based on typical root trait distributions
    n_rows = SYNTHETIC_ROWS
    
    # Species names (common plants with root data)
    species_list = [
        "Zea mays", "Triticum aestivum", "Oryza sativa", "Solanum lycopersicum",
        "Glycine max", "Brassica napus", "Helianthus annuus", "Arabidopsis thaliana",
        "Medicago truncatula", "Lotus japonicus", "Pisum sativum", "Vicia faba",
        "Sorghum bicolor", "Setaria italica", "Brachypodium distachyon"
    ]
    
    data = {
        "species": np.random.choice(species_list, size=n_rows),
        "root_depth_cm": np.random.exponential(scale=30.0, size=n_rows) + 5.0,  # Positive, skewed
        "root_diameter_mm": np.random.lognormal(mean=0.5, sigma=0.5, size=n_rows) + 0.1,
        "root_length_cm": np.random.exponential(scale=100.0, size=n_rows) + 10.0,
        "specific_root_length_mg": np.random.lognormal(mean=2.0, sigma=0.8, size=n_rows),
        "root_tissue_density_g_cm3": np.random.uniform(0.1, 0.3, size=n_rows),
        "latitude": np.random.uniform(-60, 60, size=n_rows),
        "longitude": np.random.uniform(-180, 180, size=n_rows),
        "measurement_year": np.random.randint(2010, 2024, size=n_rows),
    }
    
    return pd.DataFrame(data)

def load_root_trait_data(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Main entry point for loading root trait data.
    
    Args:
        output_path: Optional path to save the loaded data. If provided, the data
                    will be saved to this location.
                    
    Returns:
        pd.DataFrame: Root trait data.
        
    Raises:
        DataFetchError: In production mode if real data cannot be fetched.
    """
    run_mode = os.getenv("RUN_MODE", "production").lower()
    
    try:
        # Attempt to load real data
        df = _load_from_huggingface()
        
        # Validate basic structure
        required_cols = ["species", "root_depth_cm", "latitude", "longitude"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            if run_mode == "production":
                raise DataQualityError(
                    f"Real data is missing required columns: {missing_cols}. "
                    "This indicates a mismatch between expected and actual dataset schema."
                )
            else:
                logger.warning(f"Real data missing columns: {missing_cols}. Using synthetic data.")
                return _generate_synthetic_data()
        
        logger.info(f"Loaded real root trait data with {len(df)} rows and columns: {list(df.columns)}")
        
        # Save to output path if specified
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            logger.info(f"Saved root trait data to {output_path}")
        
        return df
        
    except DataFetchError:
        # This is raised in production mode when real fetch fails
        raise
        
    except Exception as e:
        # Catch-all for unexpected errors
        if run_mode == "production":
            error_msg = f"Unexpected error loading real data: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e
        else:
            logger.warning(f"Unexpected error in test mode: {str(e)}. Using synthetic data.")
            df = _generate_synthetic_data()
            
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(output_path, index=False)
                logger.info(f"Saved synthetic root trait data to {output_path}")
            
            return df

def main():
    """Main function to demonstrate data loading."""
    logger.info("Starting data loader demonstration...")
    
    # Determine output path
    output_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "root_traits_raw.csv"
    
    try:
        df = load_root_trait_data(output_path)
        logger.info(f"Data loaded successfully. Shape: {df.shape}")
        logger.info(f"Sample data:\n{df.head()}")
        logger.info(f"Data statistics:\n{df.describe()}")
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            logger.warning(f"Missing values detected:\n{missing[missing > 0]}")
        else:
            logger.info("No missing values detected.")
            
    except DataFetchError as e:
        logger.error(f"Data loading failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
