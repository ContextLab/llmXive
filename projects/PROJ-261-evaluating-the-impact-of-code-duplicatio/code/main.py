import logging
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime
import hashlib

# Import from sibling modules
from config import get_random_seed, get_memory_limit_mb, get_clone_thresholds
from memory_monitor import setup_memory_monitoring, stop_memory_monitoring, get_peak_memory_mb
from data_loader import save_raw_data_to_csv, load_raw_data
from ast_cloner import compute_clone_density_batch, save_clone_metrics
from model_metrics import compute_perplexity_batch, save_perplexity_scores
from checksum_manifest import record_artifact_checksums

def setup_logging() -> logging.Logger:
    """Setup logging for the pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/pipeline.log')
        ]
    )
    return logging.getLogger(__name__)

def load_raw_data_wrapper(logger: logging.Logger) -> Path:
    """
    Load raw data from the data loader.
    
    Returns:
        Path to the raw data CSV file
    """
    logger.info("Stage 1: Loading raw data")
    raw_data_path = Path("data/raw/github-code-sample.csv")
    
    # Ensure raw data directory exists
    raw_data_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if raw data already exists
    if raw_data_path.exists():
        logger.info(f"Raw data already exists at {raw_data_path}")
        return raw_data_path
    
    # Run data_loader.py to download and save sample
    logger.info("Running data_loader.py to download sample data")
    result = subprocess.run(
        [sys.executable, "code/data_loader.py", "--output", str(raw_data_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"data_loader.py failed: {result.stderr}")
        raise RuntimeError(f"data_loader.py failed with return code {result.returncode}")
    
    if not raw_data_path.exists():
        raise RuntimeError("data_loader.py did not create expected output file")
    
    logger.info(f"Raw data loaded successfully: {raw_data_path}")
    return raw_data_path

def compute_clone_metrics_batch(
    input_path: Path,
    output_path: Path,
    logger: logging.Logger
) -> bool:
    """
    Compute clone density metrics for all files in input.
    
    Args:
        input_path: Path to raw data CSV
        output_path: Path to save clone metrics CSV
        logger: Logger instance
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Stage 2: Computing clone density metrics")
    
    # Run ast_cloner.py with proper arguments
    result = subprocess.run(
        [sys.executable, "code/ast_cloner.py", "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"ast_cloner.py failed: {result.stderr}")
        return False
    
    if not output_path.exists():
        logger.error(f"Clone metrics output not created: {output_path}")
        return False
    
    logger.info(f"Clone metrics saved to {output_path}")
    return True

def compute_perplexity_scores_batch(
    input_path: Path,
    output_path: Path,
    logger: logging.Logger
) -> bool:
    """
    Compute perplexity scores for all files in input.
    
    Args:
        input_path: Path to raw data CSV
        output_path: Path to save perplexity scores CSV
        logger: Logger instance
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Stage 3: Computing perplexity scores")
    
    # Run model_metrics.py with proper arguments
    result = subprocess.run(
        [sys.executable, "code/model_metrics.py", "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"model_metrics.py failed: {result.stderr}")
        return False
    
    if not output_path.exists():
        logger.error(f"Perplexity scores output not created: {output_path}")
        return False
    
    logger.info(f"Perplexity scores saved to {output_path}")
    return True

def join_metrics(
    clone_metrics_path: Path,
    perplexity_path: Path,
    output_path: Path,
    logger: logging.Logger
) -> bool:
    """
    Join clone density and perplexity metrics into a single file.
    
    Args:
        clone_metrics_path: Path to clone metrics CSV
        perplexity_path: Path to perplexity scores CSV
        output_path: Path to save joined metrics CSV
        logger: Logger instance
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Stage 4: Joining metrics")
    
    try:
        # Load clone metrics
        clone_df = pd.read_csv(clone_metrics_path)
        logger.info(f"Loaded {len(clone_df)} clone metric records")
        
        # Load perplexity scores
        perplexity_df = pd.read_csv(perplexity_path)
        logger.info(f"Loaded {len(perplexity_df)} perplexity records")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Join on file_path or id column
        if 'file_path' in clone_df.columns and 'file_path' in perplexity_df.columns:
            joined_df = pd.merge(clone_df, perplexity_df, on='file_path', how='inner')
        elif 'id' in clone_df.columns and 'id' in perplexity_df.columns:
            joined_df = pd.merge(clone_df, perplexity_df, on='id', how='inner')
        else:
            # Fallback: assume same order
            min_len = min(len(clone_df), len(perplexity_df))
            joined_df = pd.concat([clone_df.iloc[:min_len], perplexity_df.iloc[:min_len]], axis=1)
        
        # Add metadata columns
        joined_df['processed_at'] = datetime.now().isoformat()
        joined_df['seed'] = get_random_seed()
        
        # Save joined metrics
        joined_df.to_csv(output_path, index=False)
        logger.info(f"Joined metrics saved to {output_path} with {len(joined_df)} records")
        
        return True
    except Exception as e:
        logger.error(f"Failed to join metrics: {e}")
        return False

def save_results(
    joined_metrics_path: Path,
    perplexity_path: Path,
    logger: logging.Logger
) -> bool:
    """
    Save final results and record checksums.
    
    Args:
        joined_metrics_path: Path to joined metrics CSV
        perplexity_path: Path to perplexity scores CSV
        logger: Logger instance
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Stage 5: Saving results and checksums")
    
    try:
        # Verify files exist
        if not joined_metrics_path.exists():
            logger.error(f"Joined metrics file not found: {joined_metrics_path}")
            return False
        
        if not perplexity_path.exists():
            logger.error(f"Perplexity scores file not found: {perplexity_path}")
            return False
        
        # Record checksums
        record_artifact_checksums(
            artifacts=[str(joined_metrics_path), str(perplexity_path)],
            log_dir=Path("data/logs")
        )
        
        logger.info("Results saved and checksums recorded")
        return True
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return False

def run_pipeline(logger: logging.Logger) -> bool:
    """
    Run the complete pipeline.
    
    Args:
        logger: Logger instance
    
    Returns:
        True if pipeline completed successfully, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Starting pipeline orchestration")
    logger.info("=" * 60)
    
    try:
        # Setup memory monitoring (now accepts optional parameters)
        setup_memory_monitoring()
        logger.info("Memory monitoring initialized")
        
        # Stage 1: Load raw data
        raw_data_path = load_raw_data_wrapper(logger)
        
        # Define output paths
        clone_metrics_path = Path("data/processed/clone_metrics.csv")
        perplexity_path = Path("data/processed/perplexity_scores.csv")
        joined_path = Path("data/processed/joined_metrics.csv")
        
        # Stage 2: Compute clone metrics
        if not compute_clone_metrics_batch(raw_data_path, clone_metrics_path, logger):
            logger.error("Clone metric computation failed")
            return False
        
        # Stage 3: Compute perplexity scores
        if not compute_perplexity_scores_batch(raw_data_path, perplexity_path, logger):
            logger.error("Perplexity computation failed")
            return False
        
        # Stage 4: Join metrics
        if not join_metrics(clone_metrics_path, perplexity_path, joined_path, logger):
            logger.error("Metrics joining failed")
            return False
        
        # Stage 5: Save results
        if not save_results(joined_path, perplexity_path, logger):
            logger.error("Result saving failed")
            return False
        
        logger.info("=" * 60)
        logger.info("Pipeline completed successfully")
        logger.info(f"Peak memory usage: {get_peak_memory_mb():.2f} MB")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        return False
    finally:
        stop_memory_monitoring()

def main():
    """Main entry point for pipeline orchestration."""
    logger = setup_logging()
    
    success = run_pipeline(logger)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()