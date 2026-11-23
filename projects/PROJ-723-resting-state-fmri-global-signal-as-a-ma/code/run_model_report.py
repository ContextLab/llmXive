import os
import sys
from pathlib import Path
import logging

from model_report import main
from config import ensure_directories

def main_entry():
    """
    Entry point for running the model report generation.
    Ensures directories are set up and calls the main function.
    """
    # Ensure required directories exist
    ensure_directories([
        Path("data/results")
    ])
    
    # Run the model report generation
    return main()

if __name__ == "__main__":
    main_entry()
