import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.model_selector import main as model_selection_main
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure

logger = get_logger(__name__)

def main_execution():
    """
    Execute the model selection pipeline.
    """
    log_stage_start("T004a", "Deterministic Model Selection")
    
    try:
        exit_code = model_selection_main()
        
        if exit_code == 0:
            log_stage_complete("T004a", "Model selection completed successfully.")
            return 0
        else:
            log_stage_failure("T004a", "Model selection failed.")
            return 1
            
    except Exception as e:
        logger.exception(f"Execution failed: {e}")
        log_stage_failure("T004a", f"Execution failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_execution())