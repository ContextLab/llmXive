import os
import sys
from utils import get_logger, set_task_id, get_task_id

def main():
    set_task_id("T001")
    logger = get_logger()
    
    dirs = [
        "data/raw",
        "data/generated",
        "data/analysis",
        "results/figures",
        "state"
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        if logger:
            logger.info(f"Created directory: {d}")
        else:
            print(f"Created directory: {d}")

if __name__ == "__main__":
    main()
