"""
Script to execute T022b: Serialization of synthesized adapters.

This script:
1. Loads the skill index from data/processed/skill_index.npz
2. Loads query embeddings from data/processed/query_embeddings.npy
3. Synthesizes adapters using multiple strategies
4. Saves the results to artifacts/synthesized_adapters/

Usage:
    python scripts/run_t022b.py
"""
import os
import sys
import logging
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from src.retrieval.strategies import main as strategies_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info("Executing T022b: Adapter Serialization")
    logger.info("=" * 60)
    
    # Ensure required directories exist
    artifacts_dir = Path("artifacts/synthesized_adapters")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Output directory: {artifacts_dir.absolute()}")
    
    try:
        # Execute the main logic from strategies.py
        strategies_main()
        
        logger.info("=" * 60)
        logger.info("T022b Execution Complete")
        logger.info("=" * 60)
        
        # List generated files
        files = list(artifacts_dir.glob("*.npz"))
        logger.info(f"Generated {len(files)} adapter files:")
        for f in files:
            logger.info(f"  - {f.name}")
            
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        logger.error("Ensure T014b (skill_index.npz) and T019 (query_embeddings.npy) are completed first.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        raise

if __name__ == "__main__":
    main()