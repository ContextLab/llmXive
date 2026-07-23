import os
from pathlib import Path
from config import PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_data_directories() -> None:
    """
    Creates the required data directory structure for the project.
    This ensures that all necessary folders for prompts, models, and outputs
    exist before data acquisition or inference begins.
    
    Creates:
      - data/prompts/
      - data/models/
      - data/outputs/base/
      - data/outputs/rl_unified/
      - data/results/
      - data/reports/
      - figures/
    
    Adds .gitkeep files to ensure directories are tracked by git.
    """
    data_dirs = [
        "prompts",
        "models",
        "outputs/base",
        "outputs/rl_unified",
        "results",
        "reports",
    ]
    
    figures_dir = "figures"
    
    base_path = Path(PROJECT_ROOT) / "data"
    
    logger.info(f"Setting up data directories under: {base_path}")
    
    for dir_name in data_dirs:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Add .gitkeep to ensure empty directories are tracked
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch()
        logger.debug(f"Created directory: {dir_path} with .gitkeep")
    
    # Create figures directory separately as it's often at root level or parallel to data
    figures_path = Path(PROJECT_ROOT) / figures_dir
    figures_path.mkdir(parents=True, exist_ok=True)
    figures_gitkeep = figures_path / ".gitkeep"
    figures_gitkeep.touch()
    logger.debug(f"Created directory: {figures_path} with .gitkeep")
    
    logger.info("Data directory structure setup complete.")
