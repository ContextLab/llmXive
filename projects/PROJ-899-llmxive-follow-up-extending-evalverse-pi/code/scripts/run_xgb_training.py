"""
Script to run XGBoost training (Task T015b).
"""
import os
import sys
import logging
from pathlib import Path
from src.models.train import main
from src.utils import setup_logging

def main_wrapper():
    setup_logging()
    main()

if __name__ == "__main__":
    main_wrapper()
