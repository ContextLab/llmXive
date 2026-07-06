"""
Entry point for the Molecular Permeability Prediction Pipeline.

This script initializes the environment, checks hardware constraints (CPU-only),
and serves as the central orchestrator for data ingestion, model training, and evaluation.
"""
import os
import sys
import logging

def check_environment():
    """Verify CPU-only constraint and basic environment setup."""
    # Explicitly enforce CPU usage as per project constraints
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    try:
        import torch
        if torch.cuda.is_available():
            logging.warning("CUDA detected but enforced CPU-only mode. GPU devices disabled.")
        
        # Verify CPU backend is functional
        device = torch.device("cpu")
        test_tensor = torch.zeros(1, device=device)
        
        logging.info(f"PyTorch version: {torch.__version__}")
        logging.info(f"Available device: {device}")
        logging.info("Environment check passed: CPU-only mode active.")
    except ImportError as e:
        logging.critical(f"Failed to import torch: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logging.critical(f"Failed to initialize PyTorch CPU backend: {e}")
        sys.exit(1)

def main():
    """Main execution flow."""
    # Setup basic logging for immediate feedback
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    check_environment()
    logging.info("Pipeline initialized successfully.")
    # Future tasks will invoke data ingestion and training here

if __name__ == "__main__":
    main()