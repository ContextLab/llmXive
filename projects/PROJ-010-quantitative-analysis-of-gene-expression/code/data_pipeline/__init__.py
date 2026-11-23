"""
Package initializer for the code.data_pipeline package.

Exposes core utility functions defined in the sibling module
``data_pipeline.py`` so that imports such as
``from code.data_pipeline import calculate_lisi`` work correctly.
"""
from .data_pipeline import (
    calculate_lisi,
    calculate_stage_variance,
    _download_public_dataset,
    _run_quality_control,
    _normalize_and_log1p,
    _highly_variable_genes,
    _scale_and_pca,
    _apply_harmony,
    parse_args,
    main,
)
