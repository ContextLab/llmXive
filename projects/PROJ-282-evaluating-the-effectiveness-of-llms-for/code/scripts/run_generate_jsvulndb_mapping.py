import os
import sys
import logging
from pathlib import Path

# Ensure the code directory is in the path
code_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(code_root))

from src.data.generate_jsvulndb_mapping import main
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure

def main_execution():
    logger = get_logger("pipeline_runner")
    log_stage_start(logger, "Executing T011a: Generate JSVulnDB Mapping")
    
    try:
        exit_code = main()
        if exit_code == 0:
            log_stage_complete(logger, "T011a execution completed successfully")
        else:
            log_stage_failure(logger, "T011a execution failed with exit code {}".format(exit_code))
        return exit_code
    except Exception as e:
        log_stage_failure(logger, "T011a execution crashed: {}".format(str(e)))
        return 1

if __name__ == "__main__":
    sys.exit(main_execution())
