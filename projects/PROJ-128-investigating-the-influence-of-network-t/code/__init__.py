"""
llmXive automated science pipeline - code package.

This package contains all the implementation code for the research pipeline.
"""

# The package-level import makes the loader utilities conveniently
# available as ``code.preprocess.loader`` when the rest of the pipeline
# imports them.
from .preprocess.loader import (
    _get_raw_data_dir,
    _validate_data_existence,
    load_hcp_dmri,
    load_hcp_fmri,
)