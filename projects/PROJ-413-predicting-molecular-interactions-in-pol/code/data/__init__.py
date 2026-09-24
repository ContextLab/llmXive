"""
Data module for the molecular interaction GNN project.
"""
from .download import main as download_main
from .clean import main as clean_main
from .generate_curated import main as generate_curated_main
from .descriptor_extractor import main as descriptor_extractor_main
from .graph_build import main as graph_build_main

__all__ = [
    "download_main",
    "clean_main",
    "generate_curated_main",
    "descriptor_extractor_main",
    "graph_build_main",
]
