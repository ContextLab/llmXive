"""
llmXive Project PROJ-199 - Main Package Initialization

This module initializes the project environment with CPU-only constraints
to ensure reproducibility and compliance with hardware limitations.
"""

import os
import sys
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Enforce CPU-only execution at package import time
try:
    from utils.cpu_efficiency import setup_cpu_efficiency
    setup_cpu_efficiency()
except ImportError:
    # Fallback if utils module not yet available during early imports
    pass

__version__ = "0.1.0"
__author__ = "llmXive Automated Science Pipeline"

# Initialize logging
try:
    from utils.logging import setup_logging
    setup_logging()
except ImportError:
    pass
