import sys
from pathlib import Path
from logger import get_logger, log_structured_event, configure_root_logger
from config import get_project_root, ensure_directories_exist

def main() -> None:
    """
    Main entry point to initialize the logging infrastructure.
    Configures the root logger to output to both console and a structured log file
    in the state/ directory.
    """
    project_root = get_project_root()
    state_dir = project_root / "state"
    ensure_directories_exist(state_dir)
    
    log_file_path = state_dir / "pipeline.log"
    
    # Configure the root logger
    configure_root_logger(log_file=str(log_file_path))
    
    logger = get_logger()
    
    # Log initialization event
    log_structured_event(
        event_type="LOGGING_INITIALIZED",
        message="Logging infrastructure configured successfully.",
        level="INFO",
        log_file=str(log_file_path),
        state_directory=str(state_dir)
    )
    
    logger.info("Logging system ready. Outputting to console and %s", log_file_path)

if __name__ == "__main__":
    main()
