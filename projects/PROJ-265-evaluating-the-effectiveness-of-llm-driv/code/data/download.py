"""
Data download module for CodeSearchNet Python subset.

Downloads the CodeSearchNet dataset using the HuggingFace datasets library.
"""

import os
import sys
from pathlib import Path
from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library not found. Install with: pip install datasets")
    sys.exit(1)


def download_codesearchnet(output_dir: str):
    """
    Download CodeSearchNet Python subset.
    
    Args:
        output_dir: Directory to save downloaded data
    """
    logger = get_logger("download")
    log_stage_start(logger, "download", "Starting CodeSearchNet download")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load the Python subset of CodeSearchNet
        logger.info("Loading codeparrot/codesearchnet-python dataset")
        dataset = load_dataset("codeparrot/codesearchnet-python", split="train")
        
        # Save to parquet
        parquet_path = output_path / "codesearchnet_python.parquet"
        dataset.to_parquet(str(parquet_path))
        
        logger.info(f"Dataset saved to {parquet_path}")
        log_stage_complete(logger, "download", f"Downloaded {len(dataset)} examples")
        
        return str(parquet_path)
        
    except Exception as e:
        log_stage_error(logger, "download", f"Download failed: {str(e)}")
        raise


def main():
    """Entry point for command-line execution."""
    if len(sys.argv) < 2:
        print("Usage: python -m data.download <output_dir>")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    
    try:
        path = download_codesearchnet(output_dir)
        print(f"Download complete: {path}")
        sys.exit(0)
    except Exception as e:
        print(f"Download failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
