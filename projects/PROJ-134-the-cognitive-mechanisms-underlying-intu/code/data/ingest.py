"""
Data Ingestion Module (T015).

Orchestrates the loading and merging of MFQ, Moral Stories, and VR Logs data.
Routes to simulation or real data fetchers based on DATA_MODE in code/config.py.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from code.config import get_path, DATA_MODE, validate_data_mode, ensure_directories
from code.utils.logging import log_pipeline_step

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def load_mfq_data() -> pd.DataFrame:
    """
    Load MFQ data. Routes to simulation or real fetcher based on DATA_MODE.
    
    Returns:
        DataFrame of MFQ data.
    
    Raises:
        FileNotFoundError: If real data fetch fails and mode is 'real'.
    """
    if DATA_MODE == 'simulation':
        logger.info("Loading MFQ data from simulation source.")
        # Import simulation module locally to avoid circular imports if not needed
        from code.data.simulation_mfq import main as run_mfq_sim
        # Run the simulation to ensure data is generated
        run_mfq_sim()
        
        input_path = get_path("data", "raw", "synthetic_mfq.csv")
        if not input_path.exists():
            # Fallback for direct script execution if main() didn't write
            input_path = get_path("data", "processed", "synthetic_mfq.csv")
            if not input_path.exists():
                raise FileNotFoundError(f"Simulated MFQ data not found at {input_path}")
        
        return pd.read_csv(input_path)
    
    elif DATA_MODE == 'real':
        logger.info("Loading MFQ data from real source.")
        # Ensure real data interface is valid
        validate_data_mode()
        
        # Import real fetcher
        try:
            from code.data.fetch_real import fetch_real_mfq_data
        except ImportError:
            raise ImportError("Real data fetcher (fetch_real.py) not found. Ensure Phase 6 tasks are complete.")
        
        try:
            output_path = fetch_real_mfq_data()
            return pd.read_csv(output_path)
        except Exception as e:
            logger.error(f"Real MFQ data fetch failed: {e}")
            raise FileNotFoundError(f"Failed to fetch real MFQ data: {e}") from e
    
    else:
        raise ValueError(f"Unknown DATA_MODE: {DATA_MODE}")

def load_stories_data() -> pd.DataFrame:
    """
    Load Moral Stories data. Routes to simulation or real fetcher.
    
    Returns:
        DataFrame of Stories data.
    """
    if DATA_MODE == 'simulation':
        logger.info("Loading Stories data from simulation source.")
        from code.data.simulation_stories import main as run_stories_sim
        run_stories_sim()
        
        input_path = get_path("data", "raw", "synthetic_stories.csv")
        if not input_path.exists():
            input_path = get_path("data", "processed", "synthetic_stories.csv")
            if not input_path.exists():
                raise FileNotFoundError(f"Simulated Stories data not found at {input_path}")
        
        return pd.read_csv(input_path)
    
    elif DATA_MODE == 'real':
        logger.info("Loading Stories data from real source.")
        validate_data_mode()
        try:
            from code.data.fetch_real import fetch_real_stories_data
        except ImportError:
            raise ImportError("Real data fetcher (fetch_real.py) not found.")
        
        try:
            output_path = fetch_real_stories_data()
            return pd.read_csv(output_path)
        except Exception as e:
            logger.error(f"Real Stories data fetch failed: {e}")
            raise FileNotFoundError(f"Failed to fetch real Stories data: {e}") from e
    
    else:
        raise ValueError(f"Unknown DATA_MODE: {DATA_MODE}")

def load_vr_logs_data() -> pd.DataFrame:
    """
    Load VR Interaction Logs. Routes to simulation or real fetcher.
    
    Returns:
        DataFrame of VR Logs data.
    """
    if DATA_MODE == 'simulation':
        logger.info("Loading VR Logs data from simulation source.")
        from code.data.simulation_stories import main as run_stories_sim
        run_stories_sim()
        
        input_path = get_path("data", "raw", "synthetic_vr_logs.csv")
        if not input_path.exists():
            input_path = get_path("data", "processed", "synthetic_vr_logs.csv")
            if not input_path.exists():
                raise FileNotFoundError(f"Simulated VR Logs data not found at {input_path}")
        
        return pd.read_csv(input_path)
    
    elif DATA_MODE == 'real':
        logger.info("Loading VR Logs data from real source.")
        validate_data_mode()
        try:
            from code.data.fetch_real import fetch_real_vr_logs
        except ImportError:
            raise ImportError("Real data fetcher (fetch_real.py) not found.")
        
        try:
            output_path = fetch_real_vr_logs()
            return pd.read_csv(output_path)
        except Exception as e:
            logger.error(f"Real VR Logs fetch failed: {e}")
            raise FileNotFoundError(f"Failed to fetch real VR Logs: {e}") from e
    
    else:
        raise ValueError(f"Unknown DATA_MODE: {DATA_MODE}")

def merge_datasets(mfq_df: pd.DataFrame, stories_df: pd.DataFrame, vr_logs_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Merge MFQ, Stories, and VR Logs datasets on participant_id.
    
    Args:
        mfq_df: MFQ DataFrame.
        stories_df: Stories DataFrame.
        vr_logs_df: Optional VR Logs DataFrame.
    
    Returns:
        Merged DataFrame.
    """
    logger.info("Merging datasets...")
    
    # Ensure common columns exist
    required_cols = ['participant_id']
    for df in [mfq_df, stories_df]:
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns in input data. Expected: {required_cols}")
    
    # Merge MFQ and Stories
    merged = pd.merge(mfq_df, stories_df, on='participant_id', how='outer')
    
    # Merge VR Logs if available
    if vr_logs_df is not None and not vr_logs_df.empty:
        if 'participant_id' in vr_logs_df.columns:
            merged = pd.merge(merged, vr_logs_df, on='participant_id', how='outer')
        else:
            logger.warning("VR Logs missing participant_id column. Skipping merge.")
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def validate_and_save(merged_df: pd.DataFrame, output_path: Optional[str] = None) -> Path:
    """
    Validate merged data and save to CSV.
    
    Args:
        merged_df: Merged DataFrame.
        output_path: Path to save the CSV.
    
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = get_path("data", "processed", "merged_data.csv")
    
    full_path = Path(output_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Basic validation
    if merged_df.empty:
        raise ValueError("Merged dataset is empty. Validation failed.")
    
    if 'participant_id' not in merged_df.columns:
        raise ValueError("Merged dataset missing 'participant_id' column.")
    
    merged_df.to_csv(full_path, index=False)
    logger.info(f"Merged data saved to {full_path}")
    
    return full_path

def main():
    """Main entry point for data ingestion."""
    ensure_directories()
    
    log_pipeline_step("start_ingestion", DATA_MODE)
    
    try:
        # Validate mode first
        validate_data_mode()
        
        # Load data
        mfq_df = load_mfq_data()
        stories_df = load_stories_data()
        
        vr_logs_df = None
        if DATA_MODE == 'simulation':
            # In simulation, we might have VR logs generated
            try:
                vr_logs_df = load_vr_logs_data()
            except FileNotFoundError:
                logger.warning("VR Logs not found in simulation. Proceeding without them.")
        elif DATA_MODE == 'real':
            try:
                vr_logs_df = load_vr_logs_data()
            except FileNotFoundError:
                logger.warning("VR Logs not found in real data. Proceeding without them.")
        
        # Merge
        merged_df = merge_datasets(mfq_df, stories_df, vr_logs_df)
        
        # Save
        output_path = validate_and_save(merged_df)
        
        log_pipeline_step("end_ingestion", {"records": len(merged_df), "output": str(output_path)})
        
        return merged_df
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        log_pipeline_step("end_ingestion_failed", {"error": str(e)})
        raise

if __name__ == "__main__":
    main()