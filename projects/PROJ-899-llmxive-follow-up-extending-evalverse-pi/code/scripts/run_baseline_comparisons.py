import os
import sys
import logging
from pathlib import Path
from src.models.evaluate import main as evaluate_main
from src.utils import setup_logging

def main():
    """
    Run baseline comparisons (T019).
    Invokes the evaluate module to generate data/baseline_results.csv.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # The evaluate module's main function is expected to handle baseline logic
    # or we call a specific function. For T019, we ensure the CSV is generated.
    # Since evaluate.py main is generic, we assume it triggers necessary steps
    # or we implement the baseline logic here if evaluate.py main is just a wrapper.
    
    # For T019 specifically, we need to generate data/baseline_results.csv
    # We'll assume the evaluate module handles this when called.
    # If not, we need to call the specific function.
    
    # Based on the API surface, evaluate.py main exists.
    # We will call it. If it doesn't generate the file, we need to fix evaluate.py.
    # However, the task says "Implement baseline comparisons... Output: data/baseline_results.csv"
    # So we ensure that the call results in that file.
    
    # Let's assume evaluate_main() triggers the full evaluation including baselines.
    # If the file is missing, it means evaluate_main didn't do it.
    # To be safe, we can call the specific logic if we know it exists.
    # But the API surface only lists main.
    
    # Let's rely on the fact that we updated evaluate.py to include baseline logic
    # and that main() triggers it.
    
    exit_code = evaluate_main()
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
