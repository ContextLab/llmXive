"""
Main entry point for the isotropy analysis pipeline.
Handles environment configuration, logging initialization, and orchestration.
"""
import os
import random
import sys
from pathlib import Path

# Import utilities from the project's existing API surface
from utils import get_logger, setup_logging, ensure_directory
from models import SupernovaRecord, HealpixPixel, HarmonicCoefficient

# Import dotenv for environment variable loading
try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback if python-dotenv is not installed (though it should be in requirements)
    print("Warning: python-dotenv not found. Environment variables from .env will not be loaded.")
    load_dotenv = None

# Ensure project root is in path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

def configure_environment():
    """
    Loads environment variables from .env file and sets defaults.
    Returns a dictionary of configuration values.
    """
    if load_dotenv:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            load_dotenv(str(env_file))
        else:
            # Attempt to load from root if not in code/
            root_env = Path(__file__).parent.parent.parent / ".env"
            if root_env.exists():
                load_dotenv(str(root_env))

    # Set defaults for simulation seeds if not provided
    os.environ.setdefault("SIMULATION_SEED", "42")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("DATA_DIR", "data")
    os.environ.setdefault("REPORTS_DIR", "reports")

    config = {
        "simulation_seed": int(os.getenv("SIMULATION_SEED", 42)),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "data_dir": os.getenv("DATA_DIR", "data"),
        "reports_dir": os.getenv("REPORTS_DIR", "reports"),
    }
    return config

def set_simulation_seed(seed: int):
    """
    Sets the random seed for reproducibility in simulations.
    """
    random.seed(seed)
    # Note: If numpy is used later, np.random.seed(seed) should be called there too
    # For now, we stick to the standard library as per current API surface
    return seed

def main():
    """
    Main execution flow.
    """
    # 1. Configure Environment
    config = configure_environment()
    
    # 2. Set Simulation Seed
    seed = set_simulation_seed(config["simulation_seed"])
    logger = get_logger(__name__)
    logger.info(f"Initialized pipeline with simulation seed: {seed}")

    # 3. Ensure Output Directories exist
    data_dir = Path(config["data_dir"])
    reports_dir = Path(config["reports_dir"])
    ensure_directory(data_dir)
    ensure_directory(reports_dir)
    ensure_directory(data_dir / "raw")
    ensure_directory(data_dir / "processed")

    logger.info(f"Output directories ready. Data: {data_dir}, Reports: {reports_dir}")

    # TODO: Orchestrate the pipeline steps (US1 -> US2 -> US3)
    # This is a placeholder for the actual pipeline execution logic
    # which will be implemented in subsequent tasks (T012, T026a, etc.)
    logger.info("Pipeline orchestration placeholder. Awaiting implementation of user stories.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
