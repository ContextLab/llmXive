"""
code/utils/ingestion_stats.py
------------------------------

Helper utilities that compute ingestion statistics.  The functions are
lightweight wrappers used by ``code/main_pipeline.py``.  They operate on the
``data/results/ingestion_stats.json`` file produced by the ingestion step.
"""

import json
from pathlib import Path
from typing import Dict

from llmxive_toolkit import paths

def calculate_ingestion_stats(config: Dict) -> Dict:
    """
    Load ``ingestion_stats.json`` and return its contents as a dictionary.
    If the file does not exist, an empty dict is returned.
    """
    stats_path = paths.results("ingestion_stats.json")
    if not stats_path.is_file():
        return {}
    with open(stats_path, "r") as f:
        return json.load(f)

def write_ingestion_stats(config: Dict) -> None:
    """
    Placeholder – the actual stats are written by ``code/data/ingest.py``.
    This function exists so that ``code/main_pipeline.py`` can import it
    without raising an ``ImportError``.
    """
    # No action required – the ingestion script already wrote the JSON file.
    pass
