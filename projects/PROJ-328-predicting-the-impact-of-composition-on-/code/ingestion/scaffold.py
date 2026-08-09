import os
import sys
import logging
from pathlib import Path
from seed import init_reproducibility
from ingestion.aggregator import LiteratureAggregator, main as run_aggregator

def setup_directories(root: Path) -> None:
    """
    Create the directory structure required for the ingestion pipeline.
    
    This scaffolds the `code/ingestion/` sub-structure and ensures
    data directories exist for raw, processed, and log outputs.
    
    Args:
        root: The project root path (e.g., projects/PROJ-328-...)
    """
    dirs_to_create = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "processed" / "validation_logs",
        root / "data" / "config",
        root / "data" / "checksums",
        root / "code" / "ingestion",
        root / "models",
    ]
    
    logger = logging.getLogger(__name__)
    logger.info(f"Setting up directories in {root}")
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {dir_path}")
        
    # Ensure __init__.py exists for ingestion package if not present
    init_file = root / "code" / "ingestion" / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        logger.info(f"Created package init file: {init_file}")

def main():
    """
    Entry point for T005: Ingestion Scaffolding.
    
    1. Initializes reproducibility seeds.
    2. Sets up required directory structure.
    3. Instantiates the LiteratureAggregator (scaffold check).
    """
    # Initialize seeds
    init_reproducibility()
    
    # Determine project root relative to this file
    # Assuming code/ is in the project root or parent
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Ingestion Scaffolding for project: {project_root}")
    
    # Setup directories
    setup_directories(project_root)
    
    # Verify LiteratureAggregator scaffold is importable and instantiable
    try:
        aggregator = LiteratureAggregator(config_path=project_root / "data" / "config" / "sources.yaml")
        logger.info("LiteratureAggregator scaffold instantiated successfully.")
    except Exception as e:
        # Expected if sources.yaml is missing (T009 handles config, T012 handles missing config error)
        # We just need to ensure the class structure exists and imports work.
        logger.warning(f"LiteratureAggregator instantiation failed (expected if config missing): {e}")
    
    logger.info("Ingestion scaffolding complete.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()
