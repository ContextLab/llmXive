"""
Code package for the llmXive automated science pipeline.
This package contains all implementation modules for the project.
"""
from pathlib import Path
import os

def verify_code_directory():
    """
    Verify that the code/ directory exists relative to this file.
    Returns True if the directory exists, False otherwise.
    """
    current_file = Path(__file__)
    parent_dir = current_file.parent
    code_dir = parent_dir.joinpath('code')
    return code_dir.is_dir()

# Verify the directory structure upon import
if not verify_code_directory():
    raise RuntimeError("The 'code/' directory structure is not correctly set up. "
                       "Please ensure the directory exists relative to this file.")

__all__ = ['verify_code_directory']
