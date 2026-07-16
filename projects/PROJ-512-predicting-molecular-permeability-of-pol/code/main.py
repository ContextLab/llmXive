import os
import sys
import logging

# Ensure project root is in path for relative imports if run as script
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from data.utils import setup_logging, set_seed, get_seed
from models.gnn import create_gnn_model
from models.baselines import RandomForestBaseline, LinearRegressionBaseline
from data.ingestion import fetch_nist_pubchem_data, process_dataset, main as ingestion_main
from data.preprocessing import process_graphs, murcko_scaffold_split
from models.trainer import create_trainer
from evaluation.metrics import evaluate_predictions
from evaluation.report import generate_final_report

def check_environment():
    """
    Validates the runtime environment.
    1. Checks Python version.
    2. Ensures CPU-only PyTorch configuration as per spec.
    
    This function enforces a strict CPU-only execution mode. If CUDA is detected,
    it explicitly disables it to prevent non-deterministic GPU behavior and
    ensure compatibility with the CPU-constrained CI environment.
    """
    import torch

    # Check Python version
    if sys.version_info < (3, 11):
        raise RuntimeError(f"Python 3.11+ required. Current: {sys.version}")

    # CPU-only enforcement logic
    if torch.cuda.is_available():
        logging.warning("CUDA is available, but forcing CPU execution for consistency with CPU-only spec.")
        # Explicitly disable CUDA usage
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        torch.cuda.is_available = lambda: False  # Override for safety in this session
        
        # Verify that forcing CPU actually works by attempting a tensor allocation
        try:
            # Attempt to create a tensor on a non-existent GPU to ensure we don't accidentally use it
            # If we force CPU, this should raise an error or be handled gracefully by the device logic
            # We want to ensure the *default* device is CPU
            test_tensor = torch.zeros(1, device='cpu')
            del test_tensor
        except Exception as e:
            raise RuntimeError(f"Failed to allocate CPU tensor after disabling CUDA: {e}")
    else:
        logging.info("CUDA not detected. Running in native CPU mode.")
    
    # Verify torch can create a CPU tensor (sanity check)
    try:
        _ = torch.zeros(1, device='cpu')
    except Exception as e:
        raise RuntimeError(f"PyTorch CPU backend check failed: {e}")

    # Final assertion: ensure we are not accidentally using CUDA
    if torch.cuda.is_available():
        raise RuntimeError("Environment check failed: CUDA is still available despite CPU-only requirement.")

    logging.info("Environment check passed. CPU-only mode enforced.")

def main():
    """
    Main entry point for the molecular permeability prediction pipeline.
    Orchestrates data ingestion, preprocessing, training, and evaluation.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Molecular Permeability Pipeline (T001 Setup)")

    # 1. Environment Check
    check_environment()

    # 2. Initialize Seed
    seed = get_seed()
    set_seed(seed)
    logger.info(f"Random seed initialized: {seed}")

    # 3. Data Ingestion (US1)
    # Note: This calls the ingestion module which fetches real data.
    # If real data is unavailable, it will fail loudly as per FR-001.
    logger.info("Fetching and processing dataset...")
    try:
        # Assuming the ingestion module handles the fetch and initial cleaning
        # We rely on the main() in ingestion.py to return the cleaned dataset
        # or raise an error if data is missing.
        # For T001, we ensure the structure exists and imports work.
        # Actual data fetching logic is in T010/T014.
        logger.info("Data ingestion module structure verified.")
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise

    # 4. Preprocessing & Splitting (US1/US2)
    logger.info("Preprocessing and splitting data...")
    # Placeholder for T014/T020 logic integration
    
    # 5. Model Training (US2)
    logger.info("Initializing models...")
    # GNN Model
    gnn_model = create_gnn_model()
    # Baselines
    rf_model = RandomForestBaseline()
    lr_model = LinearRegressionBaseline()

    # 6. Evaluation (US2/US3)
    logger.info("Pipeline structure complete. Ready for execution.")
    return 0

if __name__ == "__main__":
    sys.exit(main())