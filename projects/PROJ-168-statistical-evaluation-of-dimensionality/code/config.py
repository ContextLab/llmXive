"""
Configuration module for the project.

This file defines the Config class, which provides paths and settings
used throughout the pipeline. It reads environment variables where
appropriate, and supplies sensible defaults.
"""

import os
from pathlib import Path
import logging
import random
import numpy as np

class Config:
    """
    Central configuration holder.

    Attributes:
        RAW_DATA_DIR (Path): Directory where raw GEO files are stored.
        PROCESSED_DATA_DIR (Path): Directory for processed data.
        EMBEDDINGS_DIR (Path): Directory for embedding outputs.
        CLUSTERING_DIR (Path): Directory for clustering results.
        METRICS_DIR (Path): Directory for metric files.
        RESULTS_DIR (Path): Directory for final result artifacts.
        FIGURES_DIR (Path): Directory for generated figures.
        ACCESSIONS (list): List of GEO accession IDs to resolve.
        N_CORES (int): Number of CPU cores to allocate to Snakemake.
        SEED (int): Global random seed for reproducibility.
        SAMPLE_CELLS_THRESHOLD (int): Cell count above which deterministic
            subsampling is performed (FR‑002 / FR‑003 requirement).
        SAMPLE_SIZE (int): Number of cells to retain when subsampling
            (deterministic, seed‑controlled).
    """

    # Base project root – the toolkit provides helpers to build paths.
    # These helpers automatically create parent directories when used.
    from llmxive_toolkit import paths

    # Directories (Path objects)
    RAW_DATA_DIR: Path = paths.data("raw")
    PROCESSED_DATA_DIR: Path = paths.data("processed")
    EMBEDDINGS_DIR: Path = paths.data("embeddings")
    CLUSTERING_DIR: Path = paths.data("clustering")
    METRICS_DIR: Path = paths.data("metrics")
    RESULTS_DIR: Path = paths.results()
    FIGURES_DIR: Path = paths.figures()

    # GEO accessions required for the study.
    ACCESSIONS = ["GSE131907", "GSE111322", "GSE150728"]

    # Number of cores for Snakemake – default to 2 if not set.
    N_CORES: int = int(os.getenv("N_CORES", "2"))

    # Global random seed for reproducibility.
    SEED: int = int(os.getenv("GLOBAL_SEED", "42"))

    # Deterministic subsampling parameters (FR‑002, FR‑003)
    SAMPLE_CELLS_THRESHOLD: int = 10000   # if >10 000 cells, subsample
    SAMPLE_SIZE: int = 5000               # number of cells to keep

    # Logging configuration (optional, can be overridden elsewhere)
    LOG_LEVEL = logging.INFO
