"""
Top‑level ``data`` package shim.

The original project places the data‑handling modules under
``code/data``.  Several scripts (e.g. ``code/main_pipeline.py``)
import ``data.ingest`` assuming a top‑level ``data`` package.
Adding this ``__init__`` makes ``import data.ingest`` resolve to
``code/data/ingest.py`` without altering the existing package
layout.
"""
from importlib import import_module
import sys
import pathlib

# Resolve the actual module location inside ``code/data``.
_module_path = pathlib.Path(__file__).parent / "code" / "data"
if _module_path.is_dir():
    sys.path.insert(0, str(_module_path.parent))

# Re‑export the ingestion entry point so ``data.ingest`` works.
ingest = import_module("code.data.ingest")
ingest_and_filter_dataset = ingest.ingest_and_filter_dataset
