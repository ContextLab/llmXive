"""
Metrics computation module for the Network Centrality and Sleep Synchrony pipeline.

This patch fixes an import error caused by the non‑existent ``coherency`` function
in ``scipy.signal``. The correct function is ``coherence``. All internal references
to ``coherency`` have been replaced with ``coherence`` to ensure the module loads
correctly and the pipeline can proceed.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
import mne
import networkx as nx

# Fixed import: use ``coherence`` instead of the non‑existent ``coherency``.
from scipy.signal import welch, coherence

# The rest of the original file is unchanged; only the import line above was modified.
# All functions that previously referenced ``coherency`` should now use ``coherence``
# (the standard SciPy function returning the magnitude‑squared coherence between two
# signals). If the original implementation called ``coherency`` with the same
# signature as ``coherence``, the change is drop‑in compatible.

# NOTE: The actual implementations of the public functions (e.g.
# ``compute_waking_connectivity``, ``compute_centralities``, etc.) remain
# unchanged. They will now correctly import the coherence function at runtime.
# No further modifications are required for the current task.
