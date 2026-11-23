"""
Code module initialization.
Provides relative import configuration for the project's codebase.
"""
import sys
import os

# Ensure the code directory is in the path for relative imports if running as script
# This is handled by the runner, but good for local execution safety
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

__version__ = "0.1.0"
__author__ = "llmXive"
