"""
llmXive: Predicting Molecular Surface Area from Graph Convolutional Networks

This package provides tools for ingesting molecular data, generating 3D conformers,
calculating Solvent Accessible Surface Area (SASA), and training Graph Convolutional
Networks (GCN) to predict molecular surface area from molecular graphs.
"""
__version__ = "0.1.0"

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to sys.path if running as a script
# This ensures imports work whether run as `python -m code...` or `python code/main.py`
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import core configuration to ensure environment variables are loaded early
# This prevents circular imports by only importing the config module, not executing heavy logic
try:
    from code import config
    from code.utils import logging
    from code.utils import seed
    from code.utils import validators
    from code.utils import checksum
    from code.utils import memory_monitor
    from code.utils import network_check
    from code.utils import directories
    from code.utils import conformer_config
    
    # Expose key utilities at package level for convenience
    get_logger = logging.get_logger
    setup_logging = logging.setup_logging
    set_seed = seed.set_seed
    validate_smiles = validators.validate_smiles
    MemoryMonitor = memory_monitor.MemoryMonitor
    check_network = network_check.run_network_checks
    
except ImportError as e:
    # If dependencies aren't installed yet, we still allow the package to load
    # for basic inspection, but configuration functions will be unavailable.
    pass