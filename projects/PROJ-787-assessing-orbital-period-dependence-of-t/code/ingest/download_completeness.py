import os
import sys
import logging
from pathlib import Path
from astroquery.mast import Observations
import pandas as pd
import astropy.table
from utils.retry import retry_with_backoff

# Configure logging for this module
logger = logging.getLogger(__name__)

# MAST Product ID for the Kepler completeness map
# Based on Kepler DR25 completeness maps (Fressin et al. 2013 / Fulton et al. 2017)
# The specific product is often "Kepler_DR25_Completeness" or similar in MAST
# We will query for the specific product ID mentioned in literature or MAST search
COMPLETENESS_PRODUCT_NAME = "Kepler_DR25_Completeness"

def fetch_completeness_map():
    """
    Fetches the Kepler completeness map from the MAST archive.
    
    Returns:
        pd.DataFrame: The completeness map data.
    
    Raises:
        ValueError: If the product is not found or data cannot be retrieved.
    """
    logger.info(f"Searching for completeness map: {COMPLETENESS_PRODUCT_NAME}")
    
    try:
        # Search for the product
        search_result = Observations.query_criteria(
            productType="MISC",
            dataProductSubtype="COMPLETENESS",
            proposal_id="K2", # Kepler mission ID
            obs_collection="Kepler"
        )
        
        # If specific query fails, try a broader search for Kepler completeness
        if search_result is None or len(search_result) == 0:
            logger.warning("Specific completeness query returned no results. Trying broader search...")
            search_result = Observations.query_criteria(
                obs_collection="Kepler",
                dataProductSubtype="COMPLETENESS"
            )
        
        # Fallback: If still nothing, try searching by name pattern
        if search_result is None or len(search_result) == 0:
            logger.warning("Broad query failed. Searching by name pattern...")
            all_kepler = Observations.query_criteria(obs_collection="Kepler")
            # Filter for files containing 'completeness' in the product name
            completeness_files = all_kepler[all_kepler['productFilename'].str.contains('completeness', case=False, na=False)]
            if len(completeness_files) > 0:
                search_result = completeness_files
            else:
                # Last resort: try the specific product name if it's a known catalog
                # Sometimes completeness is part of the DR25 release itself
                pass

        # If we found a result, try to download the first relevant one
        if search_result is not None and len(search_result) > 0:
            # Filter for CSV or FITS files that look like completeness data
            relevant_files = search_result[search_result['productFilename'].str.contains('completeness|dr25', case=False, na=False)]
            if len(relevant_files) == 0:
                relevant_files = search_result[0:1] # Take the first one if no specific match
            
            logger.info(f"Found {len(relevant_files)} potential completeness files.")
            
            # Download the first relevant file
            download_list = Observations.download_products(relevant_files[0:1])
            
            if download_list is not None and 'Local Path' in download_list.columns:
                local_path = download_list['Local Path'][0]
                logger.info(f"Downloaded file to: {local_path}")
                
                # Load the data
                if local_path.endswith('.fits'):
                    # Try to read as table
                    try:
                        table = astropy.table.Table.read(local_path)
                        df = table.to_pandas()
                    except Exception as e:
                        logger.error(f"Failed to parse FITS file: {e}")
                        raise
                elif local_path.endswith('.csv'):
                    df = pd.read_csv(local_path)
                else:
                    # Try to infer
                    try:
                        df = pd.read_csv(local_path)
                    except:
                        # Maybe it's a text file with different delimiter
                        df = pd.read_csv(local_path, sep='\t')
                
                logger.info(f"Successfully loaded completeness map with shape: {df.shape}")
                return df
            else:
                logger.error("Download returned no local path.")
                raise ValueError("Download failed to produce a local file.")
        else:
            # If MAST query fails completely, we might need to construct a synthetic path 
            # based on known literature or use a fallback if the project expects a specific file.
            # However, per strict requirements, we must fail if no real source is found.
            # A common location for Kepler DR25 completeness is within the DR25 release products.
            # Let's try one more specific query for the DR25 planet table which might include completeness columns
            # or the specific completeness product.
            
            # Attempt to fetch the specific product ID if known (e.g., from literature)
            # "m13001" or similar might be the MAST ID. 
            # Since we can't hardcode a specific ID without verification, we rely on the search above.
            # If the search above failed, we raise an error.
            raise ValueError("Could not locate Kepler completeness map in MAST archive via automated query.")

    except Exception as e:
        logger.error(f"Error fetching completeness map: {e}")
        raise

def save_completeness_map(df, output_path):
    """
    Saves the completeness map DataFrame to a CSV file.
    
    Args:
        df (pd.DataFrame): The data to save.
        output_path (str): The path to save the file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved completeness map to {output_path}")

def main():
    """
    Main entry point to download and save the Kepler completeness map.
    """
    # Setup paths relative to project root
    # Assuming script is run from code/ingest/ or code/
    project_root = Path(__file__).parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    output_file = data_raw_dir / "completeness_map.csv"
    
    # Ensure output directory exists
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download of Kepler completeness map to {output_file}")
    
    try:
        # Fetch data
        completeness_df = fetch_completeness_map()
        
        # Save data
        save_completeness_map(completeness_df, str(output_file))
        
        logger.info("Task completed successfully.")
        
    except Exception as e:
        logger.critical(f"Task failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Initialize logging
    from utils.logging_config import setup_logging
    setup_logging()
    main()
